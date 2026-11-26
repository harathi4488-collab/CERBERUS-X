
from modules.graph_engine import resolve_entities, build_graph

# Sample facts for testing
facts = [
    {
        "entity_name": "Rahul Sharma",
        "entity_type": "person",
        "email": "rahul@gmail.com",
        "fact": "Rahul works in ABC Company",
        "source_file": "document1.pdf",
        "page": 2
    },
    {
        "entity_name": "Rahul Sharma",
        "entity_type": "person",
        "email": "rahul@gmail.com",
        "fact": "Rahul joined the company in 2024",
        "source_file": "document2.pdf",
        "page": 5
    },
    {
        "entity_name": "Rohit Sharma",
        "entity_type": "person",
        "email": "rohit@gmail.com",
        "fact": "Rohit works in XYZ Company",
        "source_file": "document3.pdf",
        "page": 3
    }
]

# Step 1: Resolve entities
resolved_facts = resolve_entities(facts)

print("\n========== ENTITY RESOLUTION ==========\n")

for fact in resolved_facts:
    print("Entity:", fact["entity_name"])
    print("Entity ID:", fact["entity_id"])
    print("Match Status:", fact["entity_match_status"])
    print("Source:", fact["source_file"])
    print("--------------------------------------")

# Step 2: Build evidence graph
graph = build_graph(resolved_facts)

print("\n========== GRAPH INFORMATION ==========\n")

print("Total Nodes:", graph.number_of_nodes())
print("Total Edges:", graph.number_of_edges())

print("\nNode Details:")

for node, data in graph.nodes(data=True):
    print(node, data)

print("\nEdge Details:")

for source, target, data in graph.edges(data=True):
    print(source, "-->", target, data)

print("\nCERBERUS-X GRAPH ENGINE EXECUTED SUCCESSFULLY!")
