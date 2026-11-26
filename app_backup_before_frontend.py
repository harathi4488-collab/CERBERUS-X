
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

if "facts" not in st.session_state:
    st.session_state["facts"] = []

if "conflicts" not in st.session_state:
    st.session_state["conflicts"] = []

if "reliability" not in st.session_state:
    st.session_state["reliability"] = {}

if "activity" not in st.session_state:
    st.session_state["activity"] = []

if "analysis_completed" not in st.session_state:
    st.session_state["analysis_completed"] = False

# ==========================================
# CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #F5F8FC;
    color: #243247;
}

h1, h2, h3 {
    color: #183153 !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, #E5F1FF, #F0F6FF);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #C8DDF5;
    box-shadow: 0 3px 12px rgba(40,80,130,0.08);
}

[data-testid="stMetricLabel"] {
    color: #405875 !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #174A7E !important;
    font-weight: 700;
}

[data-testid="stSidebar"] {
    background-color: #EAF1FA;
}

.stButton > button {
    background-color: #2563EB;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #174EA6;
    color: white;
}

[data-testid="stFileUploader"] {
    background-color: white;
    border: 1px dashed #8BAFD8;
    border-radius: 14px;
    padding: 15px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

with st.sidebar:

    st.title("🔍 CERBERUS-X")

    st.caption("Evidence Intelligence System")

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Upload Evidence",
            "Evidence Analysis",
            "Ask Questions",
            "About Project"
        ]
    )

    st.divider()

    st.caption("Multimodal Evidence Investigation")
    st.caption("Offline Intelligence Platform")

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

    c1.metric(
        "📁 Uploaded Files",
        len(files)
    )

    c2.metric(
        "📄 Facts Extracted",
        len(facts)
    )

    c3.metric(
        "⚠️ Conflicts Detected",
        len(conflicts)
    )

    c4.metric(
        "🔍 Evidence Sources",
        len(sources)
    )

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

    st.markdown("### Quick Actions")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button("📁 Upload Evidence", use_container_width=True):
            st.session_state["navigation_target"] = "Upload Evidence"
            st.rerun()

    with q2:
        if st.button("⚙️ Analyze Evidence", use_container_width=True):
            st.session_state["navigation_target"] = "Evidence Analysis"
            st.rerun()

    with q3:
        if st.button("💬 Ask Questions", use_container_width=True):
            st.session_state["navigation_target"] = "Ask Questions"
            st.rerun()

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
                    f"{datetime.now().strftime('%H:%M:%S')} - Uploaded {safe_name}"
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
                from modules.graph_engine import resolve_entities, build_graph
                from modules.reasoning_engine import (
                    detect_conflicts,
                    assess_reliability
                )

                with st.spinner("Investigating evidence..."):

                    facts = extract_files(paths)

                    facts = resolve_entities(facts)

                    graph = build_graph(facts)

                    conflicts = detect_conflicts(facts)

                    reliability = assess_reliability(facts)

                st.session_state["facts"] = facts
                st.session_state["conflicts"] = conflicts
                st.session_state["reliability"] = reliability
                st.session_state["analysis_completed"] = True

                st.session_state["activity"].append(
                    f"{datetime.now().strftime('%H:%M:%S')} - Evidence analysis completed"
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
                    st.info("No conflicts detected by the current rules.")

                st.subheader("Evidence Reliability")

                st.json(reliability)

                st.subheader("Knowledge Graph Summary")

                st.write("Total Nodes:", graph.number_of_nodes())
                st.write("Total Edges:", graph.number_of_edges())

                st.markdown("### Visual Knowledge Graph")

                joining_facts = [
                    fact for fact in facts
                    if str(fact.get("attribute", "")).lower().replace(" ", "_") == "joining_date"
                    and fact.get("value")
                ]

                dot = [
                    "digraph CERBERUS_X {",
                    'graph [rankdir=LR, bgcolor="transparent", nodesep=0.35, ranksep=0.5];',
                    'node [style="filled", fontname="Arial", fontsize=9, margin=0.12];',
                    'edge [fontname="Arial", fontsize=8];',
                    '"employee" [label="Rahul Kumar", shape=ellipse, fillcolor="#BFDBFE"];'
                ]

                for i, fact in enumerate(joining_facts):
                    date_id = f"date_{i}"
                    source_id = f"source_{i}"
                    date_label = "Joining Date: " + str(fact.get("value"))
                    source_label = str(fact.get("source", "Unknown source"))

                    dot.append(
                        f'{json.dumps(date_id)} [label={json.dumps(date_label)}, shape=box, fillcolor="#BBF7D0"];'
                    )
                    dot.append(
                        f'{json.dumps(source_id)} [label={json.dumps(source_label)}, shape=folder, fillcolor="#FED7AA"];'
                    )
                    dot.append(f'"employee" -> {json.dumps(date_id)} [label="HAS FACT"];')
                    dot.append(f'{json.dumps(date_id)} -> {json.dumps(source_id)} [label="FROM"];')

                dot.append("}")

                if joining_facts:
                    _, graph_column, _ = st.columns([1, 3, 1])
                    with graph_column:
                        st.graphviz_chart("\n".join(dot), width=500)
                else:
                    st.info("No joining-date facts available to display.")

            except Exception as error:

                st.error(f"Analysis error: {error}")

                st.session_state["analysis_completed"] = False

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

    if st.button("Get Evidence-Based Answer", type="primary"):

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

                st.error(f"Question answering error: {error}")

# ==========================================
# ABOUT PROJECT
# ==========================================

elif page == "About Project":

    st.subheader("About CERBERUS-X")

    st.write("""
    CERBERUS-X is an offline multimodal evidence investigation system.

    It processes:

    - PDF documents
    - Images and scanned records
    - CSV files
    - Excel spreadsheets

    Its objective is to:

    - Identify conflicting information
    - Evaluate evidence reliability
    - Connect related entities
    - Construct knowledge graphs
    - Generate traceable answers

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
