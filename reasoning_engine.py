
"""
CERBERUS-X
Offline Multimodal Evidence Investigation System

Reasoning Engine:
1. Detect conflicts between facts.
2. Assess evidence reliability indicators.
3. Answer questions using available evidence only.

No external APIs or internet-based AI services required.
"""

import re
from collections import defaultdict
from datetime import date, datetime


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def _clean(value):
    """Convert a value into a safe, normalized string."""
    if value is None:
        return ""
    return str(value).strip()


def _normalize(value):
    """Normalize values for comparison."""
    return re.sub(r"\s+", " ", _clean(value)).casefold()


def _fact_value(fact, key, default=""):
    """Safely read a field from a fact dictionary."""
    value = fact.get(key, default)
    return _clean(value)


def _source_location(fact):
    """Create a readable source and location reference."""
    source = _fact_value(fact, "source") or "Unknown source"
    location = _fact_value(fact, "location") or "Location unavailable"
    return {
        "source": source,
        "location": location
    }


def _unique_facts(facts):
    """Remove duplicate facts while preserving their original order."""
    result = []
    seen = set()

    for fact in facts:
        if not isinstance(fact, dict):
            continue

        key = (
            _normalize(fact.get("entity")),
            _normalize(fact.get("attribute")),
            _normalize(fact.get("value")),
            _normalize(fact.get("source")),
            _normalize(fact.get("location"))
        )

        if key not in seen:
            seen.add(key)
            result.append(fact)

    return result


def _suspicious_instruction_patterns(text):
    """
    Identify instruction-like content in extracted documents.
    These are warning indicators, not proof of malicious activity.
    """
    patterns = [
        r"\bignore (all )?(previous|prior|above) instructions\b",
        r"\bdisregard (all )?(previous|prior|above) instructions\b",
        r"\breveal (the )?(system prompt|hidden instructions|secrets)\b",
        r"\bshow (me )?(the )?(passwords|secret keys|credentials)\b",
        r"\boverride (the )?(system|security) instructions\b",
        r"\bact as (a )?(system|developer) message\b",
        r"\bignore your (rules|instructions|safety)\b"
    ]

    matches = []

    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(pattern)

    return matches


def _parse_date(value):
    """Parse common date formats without assuming unknown formats."""
    value = _clean(value)

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _fact_text(fact):
    """Combine relevant fact fields for question matching."""
    fields = [
        fact.get("entity", ""),
        fact.get("attribute", ""),
        fact.get("value", ""),
        fact.get("raw_text", "")
    ]
    return " ".join(_clean(item) for item in fields)


def _question_tokens(question):
    """Extract useful words from a question."""
    stop_words = {
        "what", "when", "where", "who", "why", "how",
        "is", "are", "was", "were", "the", "a", "an",
        "of", "for", "in", "on", "to", "and", "or",
        "does", "do", "did", "tell", "me", "about",
        "please", "give", "show", "find"
    }

    tokens = re.findall(r"[a-zA-Z0-9]+", question.casefold())

    return {
        token for token in tokens
        if len(token) > 1 and token not in stop_words
    }


def _evidence_item(fact):
    """Create an evidence entry with its source reference."""
    item = {
        "entity": _fact_value(fact, "entity"),
        "attribute": _fact_value(fact, "attribute"),
        "value": _fact_value(fact, "value"),
        "source": _fact_value(fact, "source") or "Unknown source",
        "location": _fact_value(fact, "location") or "Location unavailable",
        "modality": _fact_value(fact, "modality") or "Unknown",
        "extraction_quality": (
            _fact_value(fact, "extraction_quality") or "UNKNOWN"
        )
    }

    return item


# ---------------------------------------------------------
# FUNCTION 1: DETECT CONFLICTS
# ---------------------------------------------------------

def detect_conflicts(facts):
    """
    Detect different values for the same entity and attribute.

    Returns a list of conflict dictionaries.
    Different values are reported as conflicts, not as fraud.
    """

    if not isinstance(facts, list) or not facts:
        return []

    grouped_facts = defaultdict(list)

    for fact in facts:
        if not isinstance(fact, dict):
            continue

        entity = _normalize(fact.get("entity"))
        attribute = _normalize(fact.get("attribute"))
        value = _normalize(fact.get("value"))

        if not entity or not attribute or not value:
            continue

        grouped_facts[(entity, attribute)].append(fact)

    conflicts = []

    for (entity, attribute), group in grouped_facts.items():

        values = defaultdict(list)

        for fact in group:
            normalized_value = _normalize(fact.get("value"))
            values[normalized_value].append(fact)

        if len(values) <= 1:
            continue

        evidence_groups = []

        for original_value, matching_facts in values.items():
            evidence_groups.append({
                "value": _fact_value(matching_facts[0], "value"),
                "facts": [
                    _evidence_item(fact)
                    for fact in matching_facts
                ]
            })

        conflicts.append({
            "entity": _fact_value(group[0], "entity"),
            "attribute": _fact_value(group[0], "attribute"),
            "conflict_type": "VALUE_MISMATCH",
            "status": "CONFLICTING",
            "value_groups": evidence_groups,
            "explanation": (
                "Different values were found for the same entity "
                "and attribute across the available evidence sources. "
                "This difference does not by itself prove fraud "
                "or manipulation."
            )
        })

    return conflicts


# ---------------------------------------------------------
# FUNCTION 2: ASSESS RELIABILITY
# ---------------------------------------------------------

def assess_reliability(facts):
    """
    Evaluate explainable evidence reliability indicators.

    This function does not authenticate documents or calculate
    fake accuracy percentages.
    """

    if not isinstance(facts, list) or not facts:
        return []

    valid_facts = [
        fact for fact in facts
        if isinstance(fact, dict)
    ]

    if not valid_facts:
        return []

    results = []

    # Identify facts that have matching values from independent sources.
    corroboration = defaultdict(set)

    for fact in valid_facts:
        entity = _normalize(fact.get("entity"))
        attribute = _normalize(fact.get("attribute"))
        value = _normalize(fact.get("value"))
        source = _normalize(fact.get("source"))

        if entity and attribute and value and source:
            corroboration[(entity, attribute, value)].add(source)

    today = date.today()

    for fact in valid_facts:

        reasons = []
        indicators = []

        quality = _fact_value(
            fact, "extraction_quality"
        ).upper()

        source = _fact_value(fact, "source")
        location = _fact_value(fact, "location")
        raw_text = _fact_value(fact, "raw_text")

        # Extraction quality
        if quality == "HIGH":
            indicators.append({
                "indicator": "EXTRACTION_QUALITY",
                "result": "HIGH",
                "reason": "Extraction quality is marked HIGH."
            })
        elif quality == "MEDIUM":
            indicators.append({
                "indicator": "EXTRACTION_QUALITY",
                "result": "MEDIUM",
                "reason": "Extraction quality is marked MEDIUM."
            })
            reasons.append("Extraction quality is medium.")
        elif quality == "LOW":
            indicators.append({
                "indicator": "EXTRACTION_QUALITY",
                "result": "LOW",
                "reason": "Extraction quality is marked LOW."
            })
            reasons.append("Extraction quality is low.")
        else:
            indicators.append({
                "indicator": "EXTRACTION_QUALITY",
                "result": "UNKNOWN",
                "reason": "Extraction quality is missing or unknown."
            })
            reasons.append("Extraction quality is not established.")

        # Source and location
        if source:
            indicators.append({
                "indicator": "SOURCE_REFERENCE",
                "result": "PRESENT",
                "reason": "A source filename is available."
            })
        else:
            indicators.append({
                "indicator": "SOURCE_REFERENCE",
                "result": "MISSING",
                "reason": "The source filename is missing."
            })
            reasons.append("Source filename is missing.")

        if location:
            indicators.append({
                "indicator": "DOCUMENT_LOCATION",
                "result": "PRESENT",
                "reason": "A page, row or other location is available."
            })
        else:
            indicators.append({
                "indicator": "DOCUMENT_LOCATION",
                "result": "MISSING",
                "reason": "The document location is missing."
            })
            reasons.append("Document location is missing.")

        # Independent-source corroboration
        key = (
            _normalize(fact.get("entity")),
            _normalize(fact.get("attribute")),
            _normalize(fact.get("value"))
        )

        sources = corroboration.get(key, set())

        if len(sources) > 1:
            indicators.append({
                "indicator": "CORROBORATION",
                "result": "MULTIPLE_SOURCES",
                "reason": (
                    "The same value appears in multiple distinct "
                    "source filenames. Independence is not verified."
                )
            })
        else:
            indicators.append({
                "indicator": "CORROBORATION",
                "result": "NOT_ESTABLISHED",
                "reason": (
                    "No matching value from another distinct source "
                    "was identified."
                )
            })

        # Date and possible outdated information
        date_value = _parse_date(fact.get("value", ""))

        if date_value:
            if date_value > today:
                indicators.append({
                    "indicator": "DATE_CONTEXT",
                    "result": "FUTURE_DATE",
                    "reason": (
                        "The extracted date is in the future. "
                        "Its meaning needs review."
                    )
                })
                reasons.append("The extracted date is in the future.")
            else:
                indicators.append({
                    "indicator": "DATE_CONTEXT",
                    "result": "DATE_AVAILABLE",
                    "reason": (
                        "A date was recognized. Its relevance depends "
                        "on the question and document context."
                    )
                })
        else:
            indicators.append({
                "indicator": "DATE_CONTEXT",
                "result": "NOT_DETECTED",
                "reason": (
                    "No supported date format was identified "
                    "in the fact value."
                )
            })

        # Suspicious instruction-like content
        suspicious = _suspicious_instruction_patterns(raw_text)

        if suspicious:
            indicators.append({
                "indicator": "INSTRUCTION_LIKE_CONTENT",
                "result": "WARNING",
                "reason": (
                    "Instruction-like text was detected in the "
                    "extracted content. Treat it as untrusted evidence."
                )
            })
            reasons.append(
                "Instruction-like content was detected; "
                "it is not followed."
            )
        else:
            indicators.append({
                "indicator": "INSTRUCTION_LIKE_CONTENT",
                "result": "NOT_DETECTED",
                "reason": (
                    "No known instruction-like patterns were detected."
                )
            })

        results.append({
            "entity": _fact_value(fact, "entity"),
            "attribute": _fact_value(fact, "attribute"),
            "value": _fact_value(fact, "value"),
            "source": source or "Unknown source",
            "location": location or "Location unavailable",
            "indicators": indicators,
            "reasons": reasons,
            "assessment": (
                "REVIEW_REQUIRED" if reasons else "NO_FLAGGED_INDICATORS"
            ),
            "limitations": (
                "These indicators do not prove document authenticity, "
                "source independence or factual correctness."
            )
        })

    return results


# ---------------------------------------------------------
# FUNCTION 3: ANSWER QUESTION
# ---------------------------------------------------------

def answer_question(question, facts, conflicts, reliability):
    """
    Answer a question using extracted facts and source references.

    Possible statuses:
    SUPPORTED
    CONFLICTING
    INSUFFICIENT_EVIDENCE

    No instructions from uploaded documents are executed.
    """

    empty_result = {
        "status": "INSUFFICIENT_EVIDENCE",
        "answer": "There is not enough evidence to answer this question.",
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "explanation": "The question or available evidence is empty."
    }

    if not _clean(question):
        return empty_result

    if not isinstance(facts, list) or not facts:
        return empty_result

    valid_facts = [
        fact for fact in facts
        if isinstance(fact, dict)
    ]

    if not valid_facts:
        return empty_result

    tokens = _question_tokens(question)

    if not tokens:
        return empty_result

    # Find relevant facts using entity, attribute and extracted text.
    relevant_facts = []

    for fact in valid_facts:
        searchable_text = _fact_text(fact).casefold()
        searchable_tokens = set(
            re.findall(r"[a-zA-Z0-9]+", searchable_text)
        )

        attribute = _fact_value(fact, "attribute")
        attribute_tokens = _question_tokens(attribute)

        if tokens.intersection(attribute_tokens):
          relevant_facts.append(fact)

    relevant_facts = _unique_facts(relevant_facts)

    if not relevant_facts:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "answer": "No matching evidence was found for this question.",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "explanation": (
                "The available facts do not contain a clear match "
                "for the question."
            )
        }

    # Identify conflicts that involve relevant facts.
    relevant_keys = {
        (
            _normalize(fact.get("entity")),
            _normalize(fact.get("attribute"))
        )
        for fact in relevant_facts
    }

    relevant_conflicts = []

    if isinstance(conflicts, list):
        for conflict in conflicts:
            if not isinstance(conflict, dict):
                continue

            key = (
                _normalize(conflict.get("entity")),
                _normalize(conflict.get("attribute"))
            )

            if key in relevant_keys:
                relevant_conflicts.append(conflict)

    # Separate facts into supporting and contradicting groups.
    # A conflict group is not resolved by majority voting.
    supporting = []
    contradicting = []

    conflict_keys = {
        (
            _normalize(conflict.get("entity")),
            _normalize(conflict.get("attribute"))
        )
        for conflict in relevant_conflicts
    }

    for fact in relevant_facts:
        key = (
            _normalize(fact.get("entity")),
            _normalize(fact.get("attribute"))
        )

        if key in conflict_keys:
            contradicting.append(_evidence_item(fact))
        else:
            supporting.append(_evidence_item(fact))

    if relevant_conflicts:
        return {
            "status": "CONFLICTING",
            "answer": (
                "The available evidence contains conflicting values. "
                "A reliable single answer cannot be selected."
            ),
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "explanation": (
                "Different values were found for the same entity "
                "and attribute. The system preserves the source "
                "references and does not select a value based on "
                "majority voting."
            )
        }

    # A single matching fact or multiple consistent facts can support
    # a limited answer, but do not prove authenticity.
    values = {
        (
            _normalize(fact.get("entity")),
            _normalize(fact.get("attribute")),
            _normalize(fact.get("value"))
        )
        for fact in relevant_facts
    }

    if not values:
        return empty_result

    if not supporting:
        supporting = [
            _evidence_item(fact) for fact in relevant_facts
        ]

    answer_values = []

    for fact in relevant_facts:
        value = _fact_value(fact, "value")
        if value and value not in answer_values:
            answer_values.append(value)

    if not answer_values:
        return empty_result

    answer_text = "; ".join(answer_values)

    return {
        "status": "SUPPORTED",
        "answer": (
            "The available evidence reports: " + answer_text
        ),
        "supporting_evidence": supporting,
        "contradicting_evidence": [],
        "explanation": (
            "The matching evidence contains no detected conflict "
            "for the selected facts. This supports the reported "
            "information but does not independently authenticate "
            "the documents."
        )
    }


# ---------------------------------------------------------
# BASIC TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    sample_facts = [
        {
            "entity": "Rahul",
            "attribute": "Joining Date",
            "value": "10 June 2022",
            "source": "employee.pdf",
            "location": "Page 2",
            "modality": "PDF",
            "extraction_quality": "HIGH",
            "raw_text": "Rahul joining date is 10 June 2022."
        },
        {
            "entity": "Rahul",
            "attribute": "Joining Date",
            "value": "15 June 2022",
            "source": "id_card.jpg",
            "location": "Image",
            "modality": "IMAGE",
            "extraction_quality": "MEDIUM",
            "raw_text": "Rahul joining date is 15 June 2022."
        },
        {
            "entity": "Rahul",
            "attribute": "Joining Date",
            "value": "10 June 2022",
            "source": "employee.xlsx",
            "location": "Sheet1, Row 3",
            "modality": "EXCEL",
            "extraction_quality": "HIGH",
            "raw_text": "Rahul joining date is 10 June 2022."
        }
    ]

    print("\n========== CONFLICT DETECTION ==========")
    detected_conflicts = detect_conflicts(sample_facts)
    print(detected_conflicts)

    print("\n========== RELIABILITY ASSESSMENT ==========")
    reliability_results = assess_reliability(sample_facts)
    print(reliability_results)

    print("\n========== QUESTION ANSWERING ==========")
    result = answer_question(
        "What is Rahul's joining date?",
        sample_facts,
        detected_conflicts,
        reliability_results
    )
    print(result)
