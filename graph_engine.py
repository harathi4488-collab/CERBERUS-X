"""
CERBERUS-X
Multimodal Evidence Investigation System

Module: graph_engine.py

Functions:
    1. resolve_entities(facts)
    2. build_graph(facts)

Dependencies:
    pip install networkx rapidfuzz
"""

import hashlib
import json
import re
import unicodedata

import networkx as nx
from rapidfuzz import fuzz


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def normalize_text(value):
    """Normalize text for cautious entity comparison."""

    if value is None:
        return ""

    value = unicodedata.normalize("NFKC", str(value))
    value = value.lower().strip()
    value = re.sub(r"[^\w\s@.+-]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def stable_hash(value, prefix="ID"):
    """Generate a deterministic identifier."""

    serialized = json.dumps(
        value,
        sort_keys=True,
        default=str,
        ensure_ascii=False
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()[:16]

    return f"{prefix}_{digest}"


def get_entity_name(fact):
    """
    Extract the entity name from commonly used fact fields.

    Supports different fact formats without modifying
    the original fact structure.
    """

    possible_fields = [
        "entity_name",
        "entity",
        "person_name",
        "organization_name",
        "company_name",
        "subject_name",
        "subject",
        "person",
        "organization",
        "company",
        "name"
    ]

    for field in possible_fields:

        value = fact.get(field)

        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, dict):
            for key in ("name", "value", "text"):
                nested_value = value.get(key)

                if isinstance(nested_value, str) and nested_value.strip():
                    return nested_value.strip()

    return ""


def get_entity_type(fact):
    """Determine the entity type when available."""

    possible_fields = [
        "entity_type",
        "subject_type",
        "type"
    ]

    for field in possible_fields:

        value = fact.get(field)

        if isinstance(value, str) and value.strip():
            return normalize_text(value)

    return "unknown"


def get_source_info(fact):
    """Extract original source filename and location."""

    filename = (
        fact.get("source_file")
        or fact.get("filename")
        or fact.get("source_filename")
        or fact.get("file_name")
        or fact.get("source")
        or "unknown_source"
    )

    page = (
        fact.get("page")
        or fact.get("page_number")
    )

    row = (
        fact.get("row")
        or fact.get("row_number")
    )

    location = (
        fact.get("location")
        or fact.get("source_location")
        or fact.get("page_location")
    )

    return {
        "filename": str(filename),
        "page": page,
        "row": row,
        "location": location
    }


def get_identity_attributes(fact):
    """
    Extract attributes useful for entity matching.

    Names alone are not sufficient to merge people.
    """

    attribute_groups = {
        "email": [
            "email",
            "email_address"
        ],
        "phone": [
            "phone",
            "phone_number",
            "mobile"
        ],
        "identifier": [
            "person_id",
            "employee_id",
            "customer_id",
            "entity_identifier",
            "registration_number",
            "passport_number"
        ],
        "date_of_birth": [
            "date_of_birth",
            "dob",
            "birth_date"
        ],
        "organization": [
            "organization",
            "company",
            "employer",
            "organization_name"
        ],
        "address": [
            "address",
            "location",
            "residential_address"
        ],
        "role": [
            "role",
            "designation",
            "occupation",
            "job_title"
        ]
    }

    attributes = {}

    for category, fields in attribute_groups.items():

        for field in fields:

            value = fact.get(field)

            if isinstance(value, str) and value.strip():
                attributes[category] = normalize_text(value)
                break

            if isinstance(value, (int, float)):
                attributes[category] = str(value)
                break

    return attributes


def has_conflicting_identifiers(attributes_a, attributes_b):
    """
    Check whether two records contain conflicting
    strong identifiers.

    Conflicting identifiers prevent automatic merging.
    """

    strong_fields = [
        "email",
        "phone",
        "identifier",
        "date_of_birth"
    ]

    for field in strong_fields:

        value_a = attributes_a.get(field)
        value_b = attributes_b.get(field)

        if value_a and value_b and value_a != value_b:
            return True

    return False


def count_matching_attributes(attributes_a, attributes_b):
    """Count matching identity attributes."""

    matching = 0

    for field in attributes_a:

        if field in attributes_b:

            if attributes_a[field] == attributes_b[field]:
                matching += 1

    return matching


# ---------------------------------------------------------
# FUNCTION 1: ENTITY RESOLUTION
# ---------------------------------------------------------

def resolve_entities(facts):
    """
    Resolve possible duplicate entities across different files.

    Parameters:
        facts (list): Facts extracted by Member 2.

    Returns:
        list: Original facts enriched with:
            entity_id
            entity_match_status

    Status:
        MATCHED       - Strong evidence supports a match.
        POSSIBLE_MATCH - Similar entity, but insufficient
                         evidence for automatic merging.
        UNMATCHED     - No suitable matching entity found.

    Important:
        - Does not delete facts.
        - Does not delete contradictory evidence.
        - Does not merge people based on name alone.
        - Uses RapidFuzz for cautious name matching.
        - Preserves original fact fields.
    """

    if not isinstance(facts, list):
        raise TypeError("facts must be a list")

    resolved_facts = []

    # Stores independently identified entities.
    entity_registry = []

    for index, original_fact in enumerate(facts):

        if not isinstance(original_fact, dict):
            raise TypeError(
                f"Fact at index {index} must be a dictionary"
            )

        # Copy the fact to preserve the original input.
        fact = original_fact.copy()

        entity_name = get_entity_name(fact)
        normalized_name = normalize_text(entity_name)

        entity_type = get_entity_type(fact)
        attributes = get_identity_attributes(fact)

        source_info = get_source_info(fact)

        # Facts without an identifiable entity are retained.
        if not normalized_name:

            fact["entity_id"] = stable_hash(
                {
                    "fact": fact,
                    "index": index
                },
                prefix="ENTITY"
            )

            fact["entity_match_status"] = "UNMATCHED"

            resolved_facts.append(fact)
            continue

        best_match = None
        best_score = 0

        possible_match_found = False

        # Compare against previously identified entities.
        for candidate in entity_registry:

            if candidate["entity_type"] != entity_type:
                continue

            candidate_name = candidate["normalized_name"]

            similarity = fuzz.ratio(
                normalized_name,
                candidate_name
            )

            candidate_attributes = candidate["attributes"]

            # Never merge records with conflicting
            # strong identity information.
            if has_conflicting_identifiers(
                attributes,
                candidate_attributes
            ):
                continue

            matching_attributes = count_matching_attributes(
                attributes,
                candidate_attributes
            )

            # Check for a strong unique identifier match.
            exact_identifier_match = any(
                attributes.get(field)
                and attributes.get(field)
                == candidate_attributes.get(field)
                for field in [
                    "email",
                    "phone",
                    "identifier"
                ]
            )

            # A matching name alone must not merge people.
            if similarity >= 95:

                possible_match_found = True

                # Automatic matching requires corroborating
                # identity information.
                if exact_identifier_match or matching_attributes >= 2:

                    if similarity > best_score:
                        best_score = similarity
                        best_match = candidate

                elif matching_attributes >= 1:

                    if similarity > best_score:
                        best_score = similarity
                        best_match = candidate

            # Similar names without sufficient evidence
            # remain possible matches.
            elif similarity >= 85:

                possible_match_found = True

        # -------------------------------------------------
        # CASE 1: CONFIDENT MATCH
        # -------------------------------------------------

        if best_match is not None:

            entity_id = best_match["entity_id"]

            fact["entity_id"] = entity_id
            fact["entity_match_status"] = "MATCHED"

            # Preserve all original facts and their evidence.
            # Add additional attributes without overwriting
            # previously established information.
            for key, value in attributes.items():

                if key not in best_match["attributes"]:
                    best_match["attributes"][key] = value

        # -------------------------------------------------
        # CASE 2: POSSIBLE MATCH
        # -------------------------------------------------

        elif possible_match_found:

            # Do not merge uncertain entities.
            # Give the fact its own stable identifier.
            entity_id = stable_hash(
                {
                    "name": normalized_name,
                    "type": entity_type,
                    "source": source_info,
                    "attributes": attributes
                },
                prefix="ENTITY"
            )

            fact["entity_id"] = entity_id
            fact["entity_match_status"] = "POSSIBLE_MATCH"

            entity_registry.append({
                "entity_id": entity_id,
                "normalized_name": normalized_name,
                "entity_type": entity_type,
                "attributes": attributes.copy(),
                "source": source_info
            })

        # -------------------------------------------------
        # CASE 3: NO MATCH
        # -------------------------------------------------

        else:

            entity_id = stable_hash(
                {
                    "name": normalized_name,
                    "type": entity_type,
                    "source": source_info,
                    "attributes": attributes
                },
                prefix="ENTITY"
            )

            fact["entity_id"] = entity_id
            fact["entity_match_status"] = "UNMATCHED"

            entity_registry.append({
                "entity_id": entity_id,
                "normalized_name": normalized_name,
                "entity_type": entity_type,
                "attributes": attributes.copy(),
                "source": source_info
            })

        resolved_facts.append(fact)

    return resolved_facts


# ---------------------------------------------------------
# FUNCTION 2: MULTIMODAL EVIDENCE GRAPH CONSTRUCTION
# ---------------------------------------------------------

def build_graph(facts):
    """
    Construct a NetworkX evidence graph.

    Parameters:
        facts (list): Entity-resolved facts.

    Returns:
        networkx.Graph: Evidence graph containing:

            1. Entity nodes
            2. Fact nodes
            3. Source nodes

    Relationships:

        ENTITY -- HAS_FACT --> FACT

        FACT -- ORIGINATES_FROM --> SOURCE

    Source filename and page/row location are preserved.

    Conflict detection is intentionally not performed here.
    """

    if not isinstance(facts, list):
        raise TypeError("facts must be a list")

    # Create an undirected evidence graph.
    graph = nx.MultiGraph()

    # -----------------------------------------------------
    # GRAPH METADATA
    # -----------------------------------------------------

    graph.graph["project"] = "CERBERUS-X"

    graph.graph["description"] = (
        "Multimodal Evidence Graph for "
        "Conflict-Aware Reasoning"
    )

    graph.graph["node_types"] = [
        "ENTITY",
        "FACT",
        "SOURCE"
    ]

    # Empty facts must still return a valid graph.
    if not facts:
        return graph

    # -----------------------------------------------------
    # ADD ENTITY, FACT AND SOURCE NODES
    # -----------------------------------------------------

    for index, fact in enumerate(facts):

        if not isinstance(fact, dict):
            continue

        # ---------------------------------------------
        # ENTITY INFORMATION
        # ---------------------------------------------

        entity_name = get_entity_name(fact)

        entity_id = fact.get("entity_id")

        if not entity_id:

            entity_id = stable_hash(
                {
                    "name": normalize_text(entity_name),
                    "index": index
                },
                prefix="ENTITY"
            )

        entity_type = get_entity_type(fact)

        match_status = fact.get(
            "entity_match_status",
            "UNMATCHED"
        )

        # Add entity node only if it has an identifiable name.
        if entity_name:

            if not graph.has_node(entity_id):

                graph.add_node(
                    entity_id,
                    node_type="ENTITY",
                    entity_id=entity_id,
                    name=entity_name,
                    entity_type=entity_type,
                    match_status=match_status
                )

        # ---------------------------------------------
        # FACT INFORMATION
        # ---------------------------------------------

        # Preserve the complete original fact.
        fact_id = stable_hash(
            {
                "fact": fact,
                "index": index
            },
            prefix="FACT"
        )

        graph.add_node(
            fact_id,
            node_type="FACT",
            fact_id=fact_id,
            entity_id=entity_id,
            content=fact.get(
                "fact",
                fact.get(
                    "claim",
                    fact.get(
                        "statement",
                        fact.get("text", str(fact))
                    )
                )
            ),
            fact_data=fact.copy(),
            modality=fact.get(
                "modality",
                fact.get("source_type", "UNKNOWN")
            ),
            entity_match_status=match_status
        )

        # Connect entity to fact.
        if entity_name:

            graph.add_edge(
                entity_id,
                fact_id,
                relationship="HAS_FACT"
            )

        # ---------------------------------------------
        # SOURCE INFORMATION
        # ---------------------------------------------

        source_info = get_source_info(fact)

        filename = source_info["filename"]

        page = source_info["page"]
        row = source_info["row"]
        location = source_info["location"]

        source_id = stable_hash(
            {
                "filename": filename,
                "page": page,
                "row": row,
                "location": location
            },
            prefix="SOURCE"
        )

        # Add source node.
        if not graph.has_node(source_id):

            graph.add_node(
                source_id,
                node_type="SOURCE",
                source_id=source_id,
                filename=filename,
                page=page,
                row=row,
                location=location
            )

        # Connect fact to its original source.
        graph.add_edge(
            fact_id,
            source_id,
            relationship="ORIGINATES_FROM",
            filename=filename,
            page=page,
            row=row,
            location=location
        )

    return graph