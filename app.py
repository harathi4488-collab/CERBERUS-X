
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="CERBERUS-X",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# PROJECT DIRECTORIES
# ==========================================

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "facts": [],
    "conflicts": [],
    "reliability": {},
    "activity": [],
    "analysis_completed": False,
    "graph": None,
    "page": "Dashboard"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# NAVIGATION CALLBACK
# ==========================================

def navigate_to(page_name):
    st.session_state["page"] = page_name


# ==========================================
# CUSTOM DESIGN - NAVY BLUE THEME
# ==========================================

st.markdown("""
<style>

/* ==========================================
   MAIN APPLICATION
========================================== */

.stApp {
    background-color: #142B4A;
    color: #F1F5F9;
}

[data-testid="stMain"] {
    background-color: #142B4A;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* ==========================================
   TEXT AND HEADINGS
========================================== */

h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

p, label, .stMarkdown, .stCaption {
    color: #DCE8F5;
}

[data-testid="stHeader"] {
    background-color: #142B4A;
}

/* ==========================================
   SIDEBAR
========================================== */

[data-testid="stSidebar"] {
    background-color: #0D1B2A;
    border-right: 1px solid #294766;
}

[data-testid="stSidebar"] > div {
    background-color: #0D1B2A;
}

[data-testid="stSidebar"] * {
    color: #E2EAF5;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background-color: transparent;
    border-radius: 9px;
    padding: 8px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #203F63;
}

/* ==========================================
   METRIC CARDS
========================================== */

[data-testid="stMetric"] {
    background: #203F63;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #365B80;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

[data-testid="stMetricLabel"] {
    color: #C5D7EB !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 800;
}

/* ==========================================
   BUTTONS
========================================== */

.stButton > button,
.stDownloadButton > button {
    background-color: #60A5FA;
    color: #0D1B2A !important;
    border: none;
    border-radius: 9px;
    padding: 10px 20px;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #93C5FD;
    color: #0D1B2A !important;
    border: none;
}

.stButton > button:focus,
.stDownloadButton > button:focus {
    color: #0D1B2A !important;
    border-color: #93C5FD;
}

/* ==========================================
   FILE UPLOADER
========================================== */

[data-testid="stFileUploader"] {
    background-color: #203F63;
    border: 1px dashed #60A5FA;
    border-radius: 14px;
    padding: 15px;
}

[data-testid="stFileUploader"] section {
    background-color: #203F63;
}

/* ==========================================
   INPUT FIELDS
========================================== */

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: #203F63 !important;
    color: #FFFFFF !important;
    border: 1px solid #54799E !important;
    border-radius: 9px;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #AFC4DB !important;
}

[data-baseweb="select"] > div {
    background-color: #203F63;
    color: #FFFFFF;
    border-color: #54799E;
}

/* ==========================================
   DATAFRAMES AND TABLES
========================================== */

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background-color: #203F63;
    border-radius: 10px;
}

/* ==========================================
   TABS
========================================== */

button[data-baseweb="tab"] {
    color: #DCE8F5;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #93C5FD;
    border-bottom-color: #60A5FA;
}

/* ==========================================
   ALERTS
========================================== */

[data-testid="stAlert"] {
    border-radius: 10px;
}

/* ==========================================
   EXPANDERS
========================================== */

[data-testid="stExpander"] {
    background-color: #203F63;
    border: 1px solid #365B80;
    border-radius: 10px;
}

/* ==========================================
   CHECKBOXES AND RADIO BUTTONS
========================================== */

[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {
    color: #DCE8F5;
}

/* ==========================================
   DIVIDERS
========================================== */

hr {
    border-color: #365B80;
}

/* ==========================================
   FOOTER AND CAPTIONS
========================================== */

[data-testid="stCaptionContainer"] {
    color: #AFC4DB;
}

/* ==========================================
   JSON OUTPUT
========================================== */

[data-testid="stJson"] {
    background-color: #203F63;
    border-radius: 10px;
    padding: 12px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

pages = [
    "Dashboard",
    "Upload Evidence",
    "Evidence Analysis",
    "Graph Visualisation",
    "Ask Questions",
    "About Project"
]

with st.sidebar:

    st.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <div style="
            font-size: 25px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 1px;">
            CERBERUS-X
        </div>
        <div style="
            font-size: 12px;
            color: #B8C9DC;
            margin-top: 5px;">
            Evidence Intelligence System
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#93A9C2; font-size:11px; "
        "font-weight:700; letter-spacing:1.5px;'>WORKSPACE</p>",
        unsafe_allow_html=True
    )

    page = st.radio(
        "NAVIGATION",
        pages,
        format_func=lambda x: {
            "Dashboard": ":material/dashboard:  Dashboard",
            "Upload Evidence": ":material/upload_file:  Upload Evidence",
            "Evidence Analysis": ":material/account_tree:  Evidence Analysis",
            "Graph Visualisation": ":material/hub:  Graph Visualisation",
            "Ask Questions": ":material/forum:  Ask Questions",
            "About Project": ":material/info:  About Project"
        }[x],
        label_visibility="collapsed",
        key="page"
    )

    st.divider()

    st.caption("INVESTIGATION WORKSPACE")
    st.caption("Offline Evidence Processing")
    st.caption("Multimodal Investigation")


# ==========================================
# MAIN HEADER
# ==========================================

st.title("🔍 CERBERUS-X")

st.caption(
    "Multimodal Evidence Investigation & Conflict-Aware Reasoning"
)


# ==========================================
# DASHBOARD
# ==========================================

if page == "Dashboard":

    st.subheader("Investigation Dashboard")

    files = [
        f for f in UPLOAD_DIR.iterdir()
        if f.is_file()
    ]

    facts = st.session_state["facts"]
    conflicts = st.session_state["conflicts"]

    sources = set()

    for fact in facts:
        if isinstance(fact, dict) and fact.get("source"):
            sources.add(fact["source"])

    # INVESTIGATION OVERVIEW

    st.markdown("### Investigation Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📁 Uploaded Files", len(files))
    c2.metric("📄 Facts Extracted", len(facts))
    c3.metric("⚠️ Conflicts Detected", len(conflicts))
    c4.metric("🔍 Evidence Sources", len(sources))

    st.caption(
        "Metrics are based on uploaded files and available analysis results."
    )

    st.divider()

    # SYSTEM STATUS

    st.markdown("### System Status")

    s1, s2 = st.columns(2)

    if st.session_state["analysis_completed"]:
        s1.success("Analysis Completed")
    else:
        s1.info("Frontend Ready — Analysis Pending")

    s2.info("Processing Mode: Local Project")

    st.divider()

    # SYSTEM CAPABILITIES

    st.markdown("### System Capabilities")

    c1, c2, c3 = st.columns(3)

    c1.info("📄 Multimodal Document Extraction")
    c2.info("🔗 Entity Resolution & Knowledge Graph")
    c3.info("⚠️ Contradiction Detection")

    c1, c2, c3 = st.columns(3)

    c1.info("🛡️ Evidence Reliability Assessment")
    c2.info("💬 Evidence-Based Question Answering")
    c3.info("🔍 Traceable Evidence Verification")

    st.divider()

    # RECENT ACTIVITY

    st.markdown("### Recent Investigation Activity")

    if st.session_state["activity"]:

        for activity in reversed(
            st.session_state["activity"][-5:]
        ):
            st.write("•", activity)

    else:
        st.caption("No investigation activity yet.")

    st.divider()

    # QUICK ACTIONS

    st.markdown("### Quick Actions")

    q1, q2, q3 = st.columns(3)

    with q1:
        st.button(
            "📁 Upload Evidence",
            use_container_width=True,
            on_click=navigate_to,
            args=("Upload Evidence",)
        )

    with q2:
        st.button(
            "⚙️ Analyze Evidence",
            use_container_width=True,
            on_click=navigate_to,
            args=("Evidence Analysis",)
        )

    with q3:
        st.button(
            "💬 Ask Questions",
            use_container_width=True,
            on_click=navigate_to,
            args=("Ask Questions",)
        )

    st.divider()

    st.caption(
        "Welcome to CERBERUS-X. Upload evidence to begin your investigation."
    )


# ==========================================
# UPLOAD EVIDENCE
# ==========================================

elif page == "Upload Evidence":

    st.subheader("📁 Upload Investigation Evidence")

    st.write(
        "Upload PDF documents, images and spreadsheets for investigation."
    )

    uploaded_files = st.file_uploader(
        "Choose your evidence files",
        type=["pdf", "png", "jpg", "jpeg", "csv", "xlsx"],
        accept_multiple_files=True
    )

    if st.button("Save Uploaded Files", type="primary"):

        if not uploaded_files:

            st.warning("Please select files first.")

        else:

            saved_count = 0

            for file in uploaded_files:

                safe_name = Path(file.name).name
                file_path = UPLOAD_DIR / safe_name

                file_path.write_bytes(file.getvalue())

                saved_count += 1

                st.session_state["activity"].append(
                    f"{datetime.now().strftime('%H:%M:%S')} - "
                    f"Uploaded {safe_name}"
                )

            st.success(
                f"{saved_count} file(s) saved successfully!"
            )

            st.rerun()

    st.divider()

    st.subheader("Saved Evidence Files")

    saved_files = [
        f for f in UPLOAD_DIR.iterdir()
        if f.is_file()
    ]

    if saved_files:

        for file in saved_files:
            st.write("📄", file.name)

    else:

        st.info("No evidence files uploaded yet.")


# ==========================================
# EVIDENCE ANALYSIS
# ==========================================

elif page == "Evidence Analysis":

    st.subheader("⚙️ Evidence Analysis")

    st.write(
        "Process uploaded evidence and investigate contradictions."
    )

    if st.button("Analyze Evidence", type="primary"):

        paths = [
            str(f) for f in UPLOAD_DIR.iterdir()
            if f.is_file()
        ]

        if not paths:

            st.warning("Upload evidence files first.")

        else:

            try:

                from modules.extractor import extract_files
                from modules.graph_engine import (
                    resolve_entities,
                    build_graph
                )
                from modules.reasoning_engine import (
                    detect_conflicts,
                    assess_reliability
                )

                with st.spinner("Investigating evidence..."):

                    facts = extract_files(paths)

                    facts = resolve_entities(facts)

                    graph = build_graph(facts)

                    st.session_state["graph"] = graph

                    conflicts = detect_conflicts(facts)

                    reliability = assess_reliability(facts)

                st.session_state["facts"] = facts
                st.session_state["conflicts"] = conflicts
                st.session_state["reliability"] = reliability
                st.session_state["analysis_completed"] = True

                st.session_state["activity"].append(
                    f"{datetime.now().strftime('%H:%M:%S')} - "
                    "Evidence analysis completed"
                )

                st.success("Evidence analysis completed!")

                st.subheader("Extracted Evidence")

                if facts:
                    st.dataframe(facts, use_container_width=True)
                else:
                    st.info("No facts were extracted.")

                st.subheader("Detected Contradictions")

                if conflicts:
                    st.dataframe(conflicts, use_container_width=True)
                else:
                    st.info(
                        "No conflicts detected by the current rules."
                    )

                st.subheader("Evidence Reliability")

                st.json(reliability)

                st.subheader("Knowledge Graph Summary")

                st.write("Total Nodes:", graph.number_of_nodes())
                st.write("Total Edges:", graph.number_of_edges())

                st.markdown("### Visual Knowledge Graph")

                joining_facts = [
                    fact for fact in facts
                    if str(
                        fact.get("attribute", "")
                    ).lower().replace(" ", "_") == "joining_date"
                    and fact.get("value")
                ]

                dot = [
                    "digraph CERBERUS_X {",
                    'graph [rankdir=LR, bgcolor="transparent", nodesep=0.35, ranksep=0.5];',
                    'node [style="filled", fontname="Arial", fontsize=9, margin=0.12];',
                    'edge [fontname="Arial", fontsize=8];',
                    '"employee" [label="Rahul Kumar", shape=ellipse, fillcolor="#93C5FD", fontcolor="#0D1B2A"];'
                ]

                for i, fact in enumerate(joining_facts):

                    date_id = f"date_{i}"
                    source_id = f"source_{i}"

                    date_label = (
                        "Joining Date: " + str(fact.get("value"))
                    )

                    source_label = str(
                        fact.get("source", "Unknown source")
                    )

                    dot.append(
                        f'{json.dumps(date_id)} '
                        f'[label={json.dumps(date_label)}, '
                        'shape=box, fillcolor="#BBF7D0", fontcolor="#0D1B2A"];'
                    )

                    dot.append(
                        f'{json.dumps(source_id)} '
                        f'[label={json.dumps(source_label)}, '
                        'shape=folder, fillcolor="#FED7AA", fontcolor="#0D1B2A"];'
                    )

                    dot.append(
                        f'"employee" -> {json.dumps(date_id)} '
                        '[label="HAS FACT", fontcolor="#FFFFFF", color="#93C5FD"];'
                    )

                    dot.append(
                        f'{json.dumps(date_id)} -> {json.dumps(source_id)} '
                        '[label="FROM", fontcolor="#FFFFFF", color="#93C5FD"];'
                    )

                dot.append("}")

                if joining_facts:

                    _, graph_column, _ = st.columns([1, 3, 1])

                    with graph_column:
                        st.graphviz_chart(
                            "\n".join(dot),
                            width=500
                        )

                else:

                    st.info(
                        "No joining-date facts available to display."
                    )

            except Exception as error:

                st.error(f"Analysis error: {error}")

                st.session_state["analysis_completed"] = False


# ==========================================
# GRAPH VISUALISATION
# ==========================================

elif page == "Graph Visualisation":

    st.subheader("CERBERUS-X Graph Visualisation")

    if not st.session_state["analysis_completed"]:

        st.warning("Please run Evidence Analysis first.")

    else:

        try:

            import networkx as nx
            from pyvis.network import Network
            import streamlit.components.v1 as components

            facts = st.session_state["facts"]
            graph = st.session_state.get("graph")

            tab1, tab2 = st.tabs([
                "Entity Resolution Graph",
                "Knowledge Graph"
            ])

            # ENTITY RESOLUTION GRAPH

            with tab1:

                st.markdown("### Entity and Evidence Relationships")

                net = Network(
                    height="500px",
                    width="100%",
                    bgcolor="#142B4A",
                    font_color="#FFFFFF"
                )

                groups = {}

                for i, fact in enumerate(facts):

                    attribute = str(
                        fact.get("attribute", "")
                    ).lower().replace(" ", "_")

                    entity = (
                        fact.get("entity_name")
                        or fact.get("resolved_entity")
                        or fact.get("person_name")
                    )

                    if not entity and attribute in [
                        "employee_name",
                        "person_name",
                        "full_name"
                    ]:
                        entity = fact.get("value")

                    if entity:

                        groups.setdefault(
                            str(entity), []
                        ).append((i, fact))

                st.metric("Entity Groups Found", len(groups))

                for entity, records in groups.items():

                    entity_id = "entity_" + entity

                    net.add_node(
                        entity_id,
                        label=entity,
                        color="#60A5FA",
                        font={"color": "#FFFFFF"},
                        shape="ellipse"
                    )

                    for i, fact in records:

                        fact_id = f"fact_{i}"

                        net.add_node(
                            fact_id,
                            label=(
                                str(fact.get("attribute", "Fact"))
                                + ": "
                                + str(fact.get("value", ""))
                            ),
                            color="#86EFAC",
                            font={"color": "#0D1B2A"}
                        )

                        net.add_edge(
                            entity_id,
                            fact_id,
                            label="HAS FACT",
                            color="#93C5FD",
                            font={"color": "#FFFFFF"}
                        )

                        source_id = f"source_{i}"

                        source = str(
                            fact.get("source", "Unknown source")
                        )

                        net.add_node(
                            source_id,
                            label=source,
                            color="#FDBA74",
                            font={"color": "#0D1B2A"},
                            shape="database"
                        )

                        net.add_edge(
                            fact_id,
                            source_id,
                            label="FROM",
                            color="#93C5FD",
                            font={"color": "#FFFFFF"}
                        )

                if groups:

                    components.html(
                        net.generate_html(),
                        height=520,
                        scrolling=True
                    )

                else:

                    st.info("No entity names were found.")

                st.caption(
                    "This graph groups facts by extracted entity labels. "
                    "It does not independently prove identity matches."
                )

            # KNOWLEDGE GRAPH

            with tab2:

                st.markdown("### Evidence Knowledge Graph")

                if graph is None or graph.number_of_nodes() == 0:

                    st.warning(
                        "Knowledge graph unavailable. Run analysis again."
                    )

                else:

                    kg = Network(
                        height="550px",
                        width="100%",
                        bgcolor="#142B4A",
                        font_color="#FFFFFF"
                    )

                    for node, data in graph.nodes(data=True):

                        node_type = str(
                            data.get("type", "FACT")
                        ).upper()

                        colors = {
                            "ENTITY": "#60A5FA",
                            "FACT": "#86EFAC",
                            "SOURCE": "#FDBA74"
                        }

                        kg.add_node(
                            str(node),
                            label=str(data.get("label", node)),
                            color=colors.get(
                                node_type, "#C4B5FD"
                            ),
                            font={"color": "#0D1B2A"},
                            title="Type: " + node_type
                        )

                    for u, v, data in graph.edges(data=True):

                        kg.add_edge(
                            str(u),
                            str(v),
                            label=str(
                                data.get(
                                    "relation",
                                    data.get("label", "RELATED")
                                )
                            ),
                            color="#93C5FD",
                            font={"color": "#FFFFFF"}
                        )

                    components.html(
                        kg.generate_html(),
                        height=570,
                        scrolling=True
                    )

                    st.markdown("### Graph Analysis")

                    c1, c2, c3 = st.columns(3)

                    c1.metric(
                        "Total Nodes",
                        graph.number_of_nodes()
                    )

                    c2.metric(
                        "Total Edges",
                        graph.number_of_edges()
                    )

                    c3.metric(
                        "Connected Components",
                        nx.number_connected_components(
                            graph.to_undirected()
                        )
                    )

                    st.caption(
                        "The graph displays relationships represented "
                        "in the current evidence graph."
                    )

        except Exception as error:

            st.error(f"Graph error: {error}")


# ==========================================
# ASK QUESTIONS
# ==========================================

elif page == "Ask Questions":

    st.subheader("💬 Ask Questions")

    st.write(
        "Ask questions about the uploaded evidence."
    )

    question = st.text_area(
        "Enter your investigation question"
    )

    if st.button(
        "Get Evidence-Based Answer",
        type="primary"
    ):

        if not question.strip():

            st.warning("Please enter a question.")

        elif not st.session_state["analysis_completed"]:

            st.warning("Analyze the evidence first.")

        else:

            try:

                from modules.reasoning_engine import answer_question

                result = answer_question(
                    question,
                    st.session_state["facts"],
                    st.session_state["conflicts"],
                    st.session_state["reliability"]
                )

                st.subheader("Investigation Result")

                st.write(
                    "**Status:**",
                    result.get("status", "UNKNOWN")
                )

                st.write(
                    "**Answer:**",
                    result.get("answer", "No answer available.")
                )

                st.write(
                    "**Explanation:**",
                    result.get("explanation", "")
                )

                st.subheader("Supporting Evidence")

                st.json(
                    result.get("supporting_evidence", [])
                )

                st.subheader("Contradicting Evidence")

                st.json(
                    result.get("contradicting_evidence", [])
                )

            except Exception as error:

                st.error(
                    f"Question answering error: {error}"
                )


# ==========================================
# ABOUT PROJECT
# ==========================================

elif page == "About Project":

    st.subheader("About CERBERUS-X")

    st.markdown("""
    ### Multimodal Evidence Investigation & Conflict-Aware Reasoning

    CERBERUS-X is an offline multimodal evidence investigation system.

    It processes supported evidence formats such as:

    - PDF documents
    - Images and scanned records
    - CSV files
    - Excel spreadsheets

    ### Main Capabilities

    - Identify conflicting information
    - Evaluate evidence reliability
    - Connect related entities
    - Construct knowledge graphs
    - Generate traceable answers

    ### Project Objective

    The system aims to organise scattered digital evidence,
    identify inconsistencies, and support investigation through
    evidence-based reasoning.

    The system does not blindly trust information.
    It investigates evidence before reaching a conclusion.
    """)

    st.success("Verify Before You Trust.")


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "CERBERUS-X | Multimodal Evidence Investigation System"
)
