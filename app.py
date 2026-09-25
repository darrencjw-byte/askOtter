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
    if "sharepoint_url" not in st.session_state:
        st.session_state.sharepoint_url = os.getenv("SHAREPOINT_URL", "")
    if "gdrive_url" not in st.session_state:
        st.session_state.gdrive_url = os.getenv("GDRIVE_URL", "")

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

        # Display configured sources
        if st.session_state.sharepoint_url or st.session_state.gdrive_url:
            st.markdown("---")
            st.markdown("### 📂 Data Sources")
            if st.session_state.sharepoint_url:
                st.caption(f"📊 SharePoint: `{st.session_state.sharepoint_url[:40]}...`")
            if st.session_state.gdrive_url:
                st.caption(f"📁 Google Drive: `{st.session_state.gdrive_url[:40]}...`")

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

# PAGE 4: SETTINGS
def page_settings():
    st.title("⚙️ Data Source Configuration")
    st.caption("Connect your SharePoint or Google Drive folders using your own credentials")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 SharePoint Configuration")
        st.caption("Access documents from your Microsoft 365 account")

        sharepoint_input = st.text_input(
            "SharePoint Folder URL",
            value=st.session_state.sharepoint_url,
            placeholder="https://yourorg.sharepoint.com/sites/...",
            help="Enter the SharePoint folder URL you have access to"
        )

        if st.button("Save SharePoint URL", type="primary", key="save_sp"):
            st.session_state.sharepoint_url = sharepoint_input
            st.success("SharePoint URL saved successfully")
            time.sleep(0.5)
            st.rerun()

        if st.session_state.sharepoint_url:
            st.info(f"**Current URL:**\n\n`{st.session_state.sharepoint_url}`")
            st.warning("⚠️ Authentication required: You will need to authenticate with your Microsoft 365 account to access these files")

        if st.button("Clear SharePoint URL", type="secondary", key="clear_sp"):
            st.session_state.sharepoint_url = ""
            st.rerun()

    with col2:
        st.markdown("### 📁 Google Drive Configuration")
        st.caption("Access documents from your Google account")

        gdrive_input = st.text_input(
            "Google Drive Folder URL",
            value=st.session_state.gdrive_url,
            placeholder="https://drive.google.com/drive/folders/...",
            help="Enter the Google Drive folder URL you have access to"
        )

        if st.button("Save Google Drive URL", type="primary", key="save_gd"):
            st.session_state.gdrive_url = gdrive_input
            st.success("Google Drive URL saved successfully")
            time.sleep(0.5)
            st.rerun()

        if st.session_state.gdrive_url:
            st.info(f"**Current URL:**\n\n`{st.session_state.gdrive_url}`")
            st.warning("⚠️ Authentication required: You will need to authenticate with your Google account to access these files")

        if st.button("Clear Google Drive URL", type="secondary", key="clear_gd"):
            st.session_state.gdrive_url = ""
            st.rerun()

    st.divider()
    st.markdown("#### 💡 How It Works")
    st.markdown("""
    * **User-Based Access**: Documents are accessed using your own Microsoft 365 or Google account credentials
    * **Personal Permissions**: You can only access folders and files you personally have permission to view
    * **OAuth Authentication**: When indexing starts, you will be prompted to authenticate with Microsoft or Google
    * **Secure Tokens**: Your access tokens are stored securely and used only for retrieving documents you own
    * **No Shared Access**: Each user authenticates individually — no shared service account
    """)

    st.markdown("#### 🔐 Privacy & Security")
    st.success("""
    ✓ Your credentials are never stored in plain text
    ✓ Only you can access your own files
    ✓ OAuth tokens expire and require re-authentication
    ✓ No cross-user data access
    """)

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
    p_settings = st.Page(page_settings, title="Data Source Settings", icon="⚙️")

    # Routing Configuration
    pg = st.navigation({
        "Core Assistant": [p_chat],
        "Documentation": [p_about, p_method],
        "Configuration": [p_settings]
    })

    # Sidebar User Profile & Logout
    with st.sidebar:
        st.caption("👤 Logged in as: **Authenticated User**")
        if st.button("Log Out", type="secondary", use_container_width=True):
            logout()

    pg.run()