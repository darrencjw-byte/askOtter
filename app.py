import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import rag_engine
import google_auth
import drive_sync

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
    if "memory_index" not in st.session_state:
        st.session_state.memory_index = None
    if "memory_index_status" not in st.session_state:
        st.session_state.memory_index_status = None  # None | "building" | "ready" | "error" | "empty"
    if "memory_index_error" not in st.session_state:
        st.session_state.memory_index_error = None
    if "sharepoint_url" not in st.session_state:
        st.session_state.sharepoint_url = os.getenv("SHAREPOINT_URL", "")
    if "gdrive_url" not in st.session_state:
        st.session_state.gdrive_url = os.getenv("GDRIVE_URL", "")

init_session_state()

# -----------------------------------------------------------------------------
# 2b. GOOGLE OAUTH CALLBACK HANDLING
# -----------------------------------------------------------------------------
_query_params = st.query_params
if "code" in _query_params and not google_auth.is_signed_in():
    try:
        profile = google_auth.handle_callback(_query_params["code"])
        st.session_state["google_profile"] = profile
        st.query_params.clear()
        st.rerun()
    except Exception as exc:
        st.error(f"Google sign-in failed: {exc}")

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION GATES
# -----------------------------------------------------------------------------
def google_signin_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🦦 AskOtter Portal Access")
        st.caption("Public Sector AI Assistant — Sign in with your Google account to continue")

        if not google_auth.is_configured():
            st.error("Google OAuth is not configured (missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / REDIRECT_URI).")
            return

        auth_url = google_auth.get_authorization_url()
        st.link_button("🔐 Sign in with Google", auth_url, type="primary", use_container_width=True)


def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        profile = st.session_state.get("google_profile", {})
        st.markdown("## 🦦 AskOtter Portal Access")
        st.caption(f"Signed in as **{profile.get('email', 'Google account')}** — enter the access password to continue")

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
    st.session_state.memory_index = None
    st.session_state.memory_index_status = None
    st.session_state.memory_index_error = None
    google_auth.sign_out()
    st.rerun()


def ensure_index_built():
    """Fetches the signed-in user's Drive files fresh and builds the index in memory.

    Runs automatically the first time the chat page is opened in this session.
    Nothing is written to disk: files are downloaded straight into memory, parsed
    via a temp dir that self-deletes, and the vector index lives only in RAM
    (session_state) — gone the moment the session ends.
    """
    if st.session_state.memory_index_status is not None:
        return  # already built (or already attempted) this session

    st.session_state.memory_index_status = "building"
    try:
        credentials = google_auth.get_credentials()
        drive_files = drive_sync.list_files(credentials, folder_url=st.session_state.gdrive_url or None)
        if not drive_files:
            st.session_state.memory_index_status = "empty"
            return

        in_memory_files = []
        for f in drive_files:
            content, final_name = drive_sync.download_file(credentials, f["id"], f["mimeType"], f["name"])
            in_memory_files.append((final_name, content))

        index, _chunk_count = rag_engine.build_index_from_memory(in_memory_files)
        st.session_state.memory_index = index
        st.session_state.memory_index_status = "ready"
    except Exception as exc:
        st.session_state.memory_index_status = "error"
        st.session_state.memory_index_error = str(exc)

# -----------------------------------------------------------------------------
# 4. PAGE DEFINITIONS
# -----------------------------------------------------------------------------

# PAGE 1: CHAT INTERFACE
def page_ask_otter():
    st.title("🦦 AskOtter Chat Assistant")
    st.caption("Context-Aware Policy & Document Intelligence System")
    st.divider()

    # Auto-import from Drive + auto-build the index, once per session, in memory only
    if st.session_state.memory_index_status is None:
        with st.spinner("Fetching your Google Drive files and building the index..."):
            ensure_index_built()

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### 🛠️ Session Controls")
        if st.button("Clear Conversation", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.rerun()
        if st.button("🔄 Re-sync Google Drive", use_container_width=True, type="secondary"):
            st.session_state.memory_index = None
            st.session_state.memory_index_status = None
            st.session_state.memory_index_error = None
            st.rerun()
        st.markdown("---")
        status_map = {
            "building": "Building...",
            "ready": "Active (in-memory, this session only)",
            "empty": "No Drive files found",
            "error": "Failed to build",
        }
        status_label = status_map.get(st.session_state.memory_index_status, "Not started")
        st.markdown(f"**Index Status:** `{status_label}`")
        st.markdown("**Model:** `OpenAI gpt-4o-mini / text-embedding-3-large`")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Citation Sources"):
                    for idx, src in enumerate(message["sources"], 1):
                        st.markdown(f"**[{idx}] {src['title']}** (Page {src['page']})")
                        st.caption(f'"{src["snippet"]}"')

    # Query Input status messages
    if st.session_state.memory_index_status == "empty":
        st.info("📂 No supported files were found in your Google Drive to index.")
    elif st.session_state.memory_index_status == "error":
        st.warning(f"⚠️ Could not build the index from Google Drive: {st.session_state.memory_index_error}")

    if prompt := st.chat_input("Ask a question regarding internal documents..."):
        # Store & render user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Retrieving relevant passages & generating grounded answer..."):
                try:
                    if st.session_state.memory_index is None:
                        raise ValueError("No index available. Your Google Drive may be empty or the import failed.")
                    result = rag_engine.query_index(st.session_state.memory_index, prompt)
                    assistant_response = result["answer"]
                    citations = result["sources"]
                except ValueError as exc:
                    assistant_response = f"⚠️ {exc}"
                    citations = []
                except Exception as exc:
                    assistant_response = f"⚠️ Could not complete the query: {exc}"
                    citations = []

                st.markdown(assistant_response)
                if citations:
                    with st.expander("📚 Citation Sources"):
                        for idx, src in enumerate(citations, 1):
                            st.markdown(f"**[{idx}] {src['title']}** (Page {src['page']})")
                            st.caption(f'"{src["snippet"]}"')

        # Store Assistant Message
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response,
            "sources": citations
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
    st.caption("Upload documents to index, or connect a cloud folder")
    st.divider()

    st.markdown("### 📄 Document Upload & Indexing")
    st.caption("Upload PDF, DOCX, or TXT files — this builds the real vector index used by the chat assistant")

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
    )
    if uploaded_files and st.button("Save Uploaded Files", type="primary", key="save_uploads"):
        count = rag_engine.save_uploaded_files(uploaded_files)
        st.success(f"Saved {count} file(s) to the document store")

    existing_docs = rag_engine.list_documents()
    if existing_docs:
        st.markdown(f"**Documents in store ({len(existing_docs)}):**")
        for doc in existing_docs:
            st.caption(f"📄 {doc}")

        if st.button("🔄 Build / Rebuild Index", type="primary", key="build_index"):
            with st.spinner("Chunking, embedding, and writing to Qdrant..."):
                try:
                    chunk_count = rag_engine.build_index()
                    st.success(f"Index built successfully — {chunk_count} chunks indexed")
                except Exception as exc:
                    st.error(f"Indexing failed: {exc}")
    else:
        st.caption("No documents uploaded yet.")

    st.divider()
    st.markdown("### ☁️ Cloud Folder Sync")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 SharePoint Configuration")
        st.warning(
            "⚠️ **Not yet connected.** SharePoint sync requires a WOG AD / Entra ID app "
            "registration with admin consent — not available in this environment yet."
        )

    with col2:
        st.markdown("### 📁 Google Drive")
        profile = st.session_state.get("google_profile", {})
        st.success(f"Signed in as **{profile.get('email', 'Google account')}**")
        st.caption(
            "Your Drive files are fetched fresh and indexed automatically in memory each "
            "time you open the Chat page — nothing is uploaded or saved here. Use "
            "**🔄 Re-sync Google Drive** on the Chat page to refresh with the latest files."
        )

        gdrive_input = st.text_input(
            "Shared Drive folder URL (optional — leave blank to use all of your Drive)",
            value=st.session_state.gdrive_url,
            placeholder="https://drive.google.com/drive/folders/...",
        )
        st.session_state.gdrive_url = gdrive_input

# -----------------------------------------------------------------------------
# 5. NAVIGATION ROUTER & APP ENTRY POINT
# -----------------------------------------------------------------------------
if not google_auth.is_signed_in():
    google_signin_screen()
elif not st.session_state.authenticated:
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
        _profile = st.session_state.get("google_profile", {})
        st.caption(f"👤 Logged in as: **{_profile.get('email', 'Authenticated User')}**")
        if st.button("Log Out", type="secondary", use_container_width=True):
            logout()

    pg.run()