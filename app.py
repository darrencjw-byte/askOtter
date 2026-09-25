import os
import time
import streamlit as st

# -----------------------------------------------------------------------------
# 1. APPLICATION & PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AskOtter - Enterprise RAG Assistant",
    page_icon="🦦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "query_engine" not in st.session_state:
        st.session_state.query_engine = None

init_session_state()

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION GATE
# -----------------------------------------------------------------------------
def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🦦 AskOtter Portal Access")
        st.caption("Public Sector AI Assistant — Authenticate to Proceed")
        
        with st.form("login_form"):
            password_input = st.text_input("Enter Access Password", type="password")
            submit_button = st.form_submit_button("Authenticate", use_container_width=True)
            
            if submit_button:
                target_password = os.getenv("APP_PASSWORD", "CFS@2027")
                if password_input == target_password:
                    st.session_state.authenticated = True
                    st.success("Authentication successful! Redirecting...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Access Key. Please check your credentials.")

def logout():
    st.session_state.authenticated = False
    st.session_state.messages = []
    st.rerun()

# -----------------------------------------------------------------------------
# 4. PAGE DEFINITIONS
# -----------------------------------------------------------------------------

# PAGE 1: CHAT INTERFACE
def page_ask_otter():
    st.title("🦦 AskOtter Chat Assistant")
    st.caption("Context-Aware Policy & Document Intelligence System")
    st.divider()

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### 🛠️ Session Controls")
        if st.button("Clear Conversation", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.rerun()
        st.markdown("---")
        st.markdown("**Index Status:** `Active (Cloud Sync)`")
        st.markdown("**Model:** `Azure GPT-4o / Vertex AI`")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Citation Sources"):
                    for idx, src in enumerate(message["sources"], 1):
                        st.markdown(f"**[{idx}] {src['title']}** (Page {src['page']})")
                        st.caption(f'"{src["snippet"]}"')

    # Query Input
    if prompt := st.chat_input("Ask a question regarding internal documents..."):
        # Store & render user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing vector database & retrieving citations..."):
                # Mock RAG response (Replace with LlamaIndex/LangChain query call)
                time.sleep(1.0)
                assistant_response = (
                    f"Based on internal indexed documentation regarding **'{prompt}'**, "
                    f"agencies must maintain compliance with Section 4.2 of the Governance Framework."
                )
                mock_citations = [
                    {
                        "title": "Public_Sector_Governance_2026.pdf",
                        "page": 12,
                        "snippet": "All deployment repositories must enforce containerized runtime limits and password gating."
                    },
                    {
                        "title": "Cloud_Drive_Ingestion_Policy.docx",
                        "page": 5,
                        "snippet": "Vector re-indexing occurs asynchronously upon document modifications."
                    }
                ]

                st.markdown(assistant_response)
                with st.expander("📚 Citation Sources"):
                    for idx, src in enumerate(mock_citations, 1):
                        st.markdown(f"**[{idx}] {src['title']}** (Page {src['page']})")
                        st.caption(f'"{src["snippet"]}"')

        # Store Assistant Message
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response,
            "sources": mock_citations
        })

# PAGE 2: ABOUT US
def page_about_us():
    st.title("ℹ️ About AskOtter")
    st.markdown("### Public Sector AI Innovation")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **AskOtter** is an enterprise Retrieval-Augmented Generation (RAG) agent developed for the **AI Champion Bootcamp (August – November 2026)**.
        
        #### Primary Objectives:
        * **Automate Document Discovery**: Index institutional memory across SharePoint and Google Drive.
        * **Zero Halucination Target**: Enforce strict source citations on every query answer.
        * **Secure Access**: Implement role-aware container deployment and password gating.
        """)
    with col2:
        st.info("""
        #### Key Metadata
        * **Repo Slug:** `ask-otter`
        * **Deployment Runtime:** RabbitDeploy (Docker / Streamlit Engine)
        * **Submission Portal:** LaunchPad
        * **Target Grading Focus:** Session State, Prompt Engineering, Agent Tools (25% Weightage)
        """)

# PAGE 3: METHODOLOGY
def page_methodology():
    st.title("⚙️ System Methodology & Architecture")
    st.markdown("### Technical Framework & Flowchart")

    st.markdown("""
    #### 1. End-to-End Data Flow
    1. **Ingestion Layer**: Document loaders pull `.pdf`, `.docx`, and `.xlsx` files from designated SharePoint / Google Drive folders.
    2. **Vector Indexing**: Documents are parsed into overlap chunks and converted to vector embeddings using `text-embedding-3-large`.
    3. **Query Engine**: Streamlit passes user queries to LlamaIndex retriever, extracting top-$k$ relevant passages based on cosine similarity.
    4. **Prompt Guard**: Query and retrieved context are merged into a strictly constrained system prompt before invoking the LLM.
    """)

    st.markdown("#### 2. Process Architecture")
    st.code("""
[ Cloud Drive ] ---> [ Chunking & Embeddings ] ---> [ Vector Database ]
                                                            |
[ User Query ] ---> [ Streamlit Auth Gate ] ---> [ Vector Retriever ]
                                                            |
[ Grounded Answer + Citations ] <--- [ LLM Synthesis ] <----+
    """, language="text")

# -----------------------------------------------------------------------------
# 5. NAVIGATION ROUTER & APP ENTRY POINT
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    login_screen()
else:
    # Page Declarations
    p_chat = st.Page(page_ask_otter, title="AskOtter Chat", icon="💬", default=True)
    p_about = st.Page(page_about_us, title="About Us", icon="ℹ️")
    p_method = st.Page(page_methodology, title="Methodology", icon="⚙️")

    # Routing Configuration
    pg = st.navigation({
        "Core Assistant": [p_chat],
        "Documentation": [p_about, p_method]
    })

    # Sidebar User Profile & Logout
    with st.sidebar:
        st.caption("👤 Logged in as: **Authenticated User**")
        if st.button("Log Out", type="secondary", use_container_width=True):
            logout()

    pg.run()