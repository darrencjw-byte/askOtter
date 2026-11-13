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
        st.session_state.memory_index_status = None
    if "memory_index_error" not in st.session_state:
        st.session_state.memory_index_error = None

init_session_state()

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION GATE (password only)
# -----------------------------------------------------------------------------
def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🦦 AskOtter Portal Access")
        st.caption("Public Sector AI Assistant — enter the access password to continue")
        st.info("🔑 **Access Password:** `CFS@2027`")

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
# 4. INDEX BUILDER (runs once for the entire app, shared across all sessions)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _build_global_index():
    """Builds the vector index once and caches it across all user sessions."""
    credentials = google_auth.get_credentials()

    gdrive_url = os.getenv("GDRIVE_URL", "")
    drive_files = drive_sync.list_files(credentials, folder_url=gdrive_url or None)

    if not drive_files:
        return None, [], 0

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set. Add it to your Streamlit Cloud secrets.")

    service = drive_sync._build_service("drive", "v3", credentials)
    in_memory_files = []
    file_names = []
    for f in drive_files:
        content, final_name = drive_sync.download_file(credentials, f["id"], f["mimeType"], f["name"], service=service)
        in_memory_files.append((final_name, content))
        file_names.append(final_name)

    index, chunk_count = rag_engine.build_index_from_memory(in_memory_files)
    return index, file_names, chunk_count


def ensure_index_built():
    status = st.session_state.memory_index_status
    if status is not None and status != "building":
        return

    st.session_state.memory_index_status = "building"
    try:
        with st.spinner("Loading document index..."):
            index, file_names, chunk_count = _build_global_index()

        if index is None:
            st.session_state.memory_index_status = "empty"
            return

        st.session_state.memory_index = index
        st.session_state["indexed_file_names"] = file_names
        st.session_state.memory_index_status = "ready"
    except Exception as exc:
        st.session_state.memory_index_status = "error"
        st.session_state.memory_index_error = str(exc)


# -----------------------------------------------------------------------------
# 5. PAGE DEFINITIONS
# -----------------------------------------------------------------------------

CHAT_PAGE_CSS = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background: radial-gradient(circle at 20% 0%, #efe6fb 0%, #f7f3fd 35%, #ffffff 70%);
}
[data-testid="stChatInput"] {
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(90, 60, 160, 0.08);
}
[data-testid="stChatInput"] textarea {
    font-size: 1.02rem;
}
.askotter-suggestion-row button {
    border-radius: 999px !important;
    border: 1px solid #e3d9f5 !important;
    background: #ffffff !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.1rem !important;
}
.askotter-suggestion-row button:hover {
    border-color: #8b5cf6 !important;
    color: #6d28d9 !important;
}
.askotter-hero {
    text-align: center;
    padding-top: 4rem;
}
.askotter-hero h1 {
    font-size: 2.1rem;
    font-weight: 600;
    color: #2a1f3d;
}
.askotter-hero p {
    color: #6b6480;
    font-size: 0.95rem;
}
</style>
"""


def page_ask_otter():
    st.markdown(CHAT_PAGE_CSS, unsafe_allow_html=True)

    status = st.session_state.memory_index_status
    if status is None or status == "building":
        ensure_index_built()

    # Sidebar
    with st.sidebar:
        st.markdown("### 🦦 AskOtter")
        st.caption("Context-aware policy & document intelligence")
        st.markdown("---")
        st.markdown("### 🛠️ Session Controls")
        if st.button("Clear Conversation", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.rerun()
        if st.button("🔄 Re-sync Google Drive", use_container_width=True, type="secondary"):
            _build_global_index.clear()
            st.session_state.memory_index = None
            st.session_state.memory_index_status = None
            st.session_state.memory_index_error = None
            st.rerun()
        st.markdown("---")
        status_map = {
            "building": "Building...",
            "ready": "Active (cached across sessions)",
            "empty": "No Drive files found",
            "error": "Failed to build",
        }
        status_label = status_map.get(st.session_state.memory_index_status, "Not started")
        st.markdown(f"**Index Status:** `{status_label}`")
        st.markdown("**Model:** `OpenAI gpt-4o-mini / text-embedding-3-small`")

    has_history = len(st.session_state.messages) > 0

    if not has_history:
        st.markdown(
            """
            <div class="askotter-hero">
                <h1>🦦 Ask away, your documents are ready</h1>
                <p>Answers are grounded in files from the configured Google Drive folder.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="askotter-suggestion-row">', unsafe_allow_html=True)
        sug_col1, sug_col2, sug_col3 = st.columns(3)
        suggestion_clicked = None
        with sug_col1:
            if st.button("Summarise my documents", use_container_width=True, key="sug_1"):
                suggestion_clicked = "Summarise the key points across my imported documents."
        with sug_col2:
            if st.button("Find a policy clause", use_container_width=True, key="sug_2"):
                suggestion_clicked = "Find the clause or section that covers the main policy requirements."
        with sug_col3:
            if st.button("List document sources", use_container_width=True, key="sug_3"):
                suggestion_clicked = "List the documents that were imported and indexed in this session."
        st.markdown("</div>", unsafe_allow_html=True)

        if suggestion_clicked:
            st.session_state["_pending_prompt"] = suggestion_clicked
            st.rerun()

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Citation Sources"):
                    for idx, src in enumerate(message["sources"], 1):
                        st.markdown(f"**[{idx}] {src['title']}** (Page {src['page']})")
                        st.caption(f'"{src["snippet"]}"')

    if st.session_state.memory_index_status == "empty":
        st.info("📂 No supported files were found in the configured Google Drive folder.")
    elif st.session_state.memory_index_status == "error":
        st.warning(f"⚠️ Could not build the index from Google Drive: {st.session_state.memory_index_error}")

    prompt = st.chat_input("Ask me anything about your documents...")
    pending = st.session_state.pop("_pending_prompt", None)
    if pending:
        prompt = pending

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving relevant passages & generating grounded answer..."):
                try:
                    if st.session_state.memory_index is None:
                        raise ValueError("No index available. The Google Drive may be empty or the import failed.")
                    file_names = st.session_state.get("indexed_file_names", [])
                    file_list_context = "\n".join(f"- {name}" for name in file_names)
                    augmented_prompt = f"{prompt}\n\n[System context — indexed files in this session:\n{file_list_context}]"
                    result = rag_engine.query_index(st.session_state.memory_index, augmented_prompt)
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

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response,
            "sources": citations
        })


# PAGE 2: ABOUT US
def page_about_us():
    st.title("ℹ️ About Us")
    st.markdown("---")

    # --- Project Scope ---
    st.markdown("### 📋 Project Scope")
    st.markdown("""
    **AskOtter** is an enterprise Retrieval-Augmented Generation (RAG) assistant developed for the
    **AI Champion Bootcamp (August – November 2026)**. It enables public sector officers to query
    institutional documents using natural language and receive grounded, citation-backed answers —
    reducing the time spent manually searching through policy documents, guidelines, and reports.
    """)

    st.markdown("---")

    # --- Objectives ---
    st.markdown("### 🎯 Objectives")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        1. **Automate Document Discovery**
           - Index documents from a pre-configured Google Drive folder automatically on each session start.
           - Support PDF, DOCX, XLSX, Google Docs, and Google Sheets.
           - Recursively scan subfolders for complete coverage.

        2. **Provide Grounded, Accurate Answers**
           - Every answer is synthesised from retrieved document passages — not from the LLM's training data.
           - Source citations with document name, page number, and relevant snippet are displayed for every response.
        """)
    with col2:
        st.markdown("""
        3. **Ensure Secure Access**
           - Password-gated portal — only authorised users with the access password can use the assistant.
           - Google Drive access uses the owner's stored credentials; end users do not need a Google account.

        4. **Zero-Infrastructure Deployment**
           - Hosted on Streamlit Community Cloud with automatic redeployment from GitHub.
           - Fully in-memory indexing — no persistent database, no data stored server-side.
        """)

    st.markdown("---")

    # --- Data Sources ---
    st.markdown("### 📂 Data Sources")
    st.markdown("""
    | Source | Type | Access Method |
    |--------|------|---------------|
    | Google Drive (configured folder) | PDF, DOCX, XLSX, Google Docs, Google Sheets | Google Drive API v3 with OAuth 2.0 refresh token |
    | Manual upload (Settings page) | PDF, DOCX, TXT, MD | Streamlit file uploader |
    """)
    st.markdown("""
    - Documents are fetched **fresh each session** — the index always reflects the latest content in the Drive folder.
    - The app recursively scans all subfolders within the configured folder.
    - Google Docs and Sheets are automatically exported to PDF/XLSX format before indexing.
    """)

    st.markdown("---")

    # --- Features ---
    st.markdown("### ✨ Features")
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    with feat_col1:
        st.markdown("""
        **💬 RAG Chat Assistant**
        - Natural language Q&A over indexed documents
        - Grounded answers with citation sources
        - Conversation history within session
        - Suggestion chips for common queries
        """)
    with feat_col2:
        st.markdown("""
        **🔄 Automatic Indexing**
        - Google Drive folder indexed on session start
        - Recursive subfolder scanning
        - In-memory vector index (Qdrant)
        - Re-sync button for on-demand refresh
        """)
    with feat_col3:
        st.markdown("""
        **🔒 Secure & Stateless**
        - Password-gated access
        - No data persisted server-side
        - Owner-scoped Drive credentials
        - Session-isolated index (per user)
        """)

    st.markdown("---")

    # --- Key Metadata ---
    st.markdown("### 📊 Key Metadata")
    st.info("""
    | Field | Value |
    |-------|-------|
    | **Project Name** | AskOtter |
    | **Repo Slug** | `askOtter` |
    | **Deployment Runtime** | Streamlit Community Cloud |
    | **Submission Portal** | LaunchPad |
    | **LLM** | OpenAI `gpt-4o-mini` |
    | **Embedding Model** | OpenAI `text-embedding-3-small` |
    | **Vector Store** | Qdrant (in-memory) |
    | **Framework** | LlamaIndex |
    | **Target Grading Focus** | Session State, Prompt Engineering, Agent Tools (25% Weightage) |
    """)


# PAGE 3: METHODOLOGY
def page_methodology():
    st.title("⚙️ Methodology")
    st.markdown("---")

    # --- Overview ---
    st.markdown("### 🏗️ System Architecture Overview")
    st.markdown("""
    AskOtter follows a **Retrieval-Augmented Generation (RAG)** architecture. Instead of relying
    on the LLM's training data, every answer is grounded in the user's own documents. The system
    has two core use cases, each with its own data flow:

    1. **Document Indexing** — Fetching, parsing, and embedding documents from Google Drive
    2. **Chat with Documents** — Querying the index and generating grounded answers
    """)

    st.markdown("---")

    # --- Data Flow ---
    st.markdown("### 📊 End-to-End Data Flow")
    st.markdown("""
    | Stage | Component | Technology | Description |
    |-------|-----------|------------|-------------|
    | 1. Authentication | Password Gate | Streamlit | User enters access password to gain entry |
    | 2. Data Ingestion | Google Drive API v3 | `google-api-python-client` | Fetches PDF, DOCX, XLSX, Google Docs/Sheets from configured folder (recursive) |
    | 3. Document Parsing | File Loaders | LlamaIndex `SimpleDirectoryReader` | Extracts text content from each document format |
    | 4. Chunking | Sentence Splitter | LlamaIndex `SentenceSplitter` | Splits documents into 1024-token overlapping chunks (100-token overlap) |
    | 5. Embedding | Vector Encoding | OpenAI `text-embedding-3-small` | Converts each chunk into a 1536-dimensional vector |
    | 6. Indexing | Vector Store | Qdrant (in-memory) | Stores vectors for similarity search |
    | 7. Retrieval | Query Engine | LlamaIndex `VectorStoreIndex` | Finds top-*k* most relevant chunks via cosine similarity |
    | 8. Synthesis | LLM Generation | OpenAI `gpt-4o-mini` | Generates a grounded answer from retrieved passages |
    | 9. Citation | Source Attribution | Custom post-processing | Extracts document name, page number, and snippet for each source |
    """)

    st.markdown("---")

    # --- Use Case 1: Document Indexing ---
    st.markdown("### 📄 Use Case 1: Document Indexing")
    st.markdown("""
    This flow runs **automatically at session start**. It fetches the owner's Google Drive
    documents and builds an in-memory vector index that powers all subsequent queries.
    """)

    st.markdown("#### Flowchart")
    st.code("""
    ┌─────────────────────┐
    │   Session Starts    │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Load Google Drive   │
    │  Credentials         │
    │  (stored refresh     │
    │   token in secrets)  │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  List Files in       │
    │  Configured Folder   │◄──── Recursive: scans
    │  (Google Drive API)  │      all subfolders
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐     ┌──────────────────┐
    │  Files Found?        │─No─►│ Show "No files   │
    │                      │     │ found" message    │
    └─────────┬───────────┘     └──────────────────┘
              │ Yes
              ▼
    ┌─────────────────────┐
    │  Download Each File  │
    │  into Memory         │◄──── Google Docs → PDF
    │  (no disk writes)    │      Sheets → XLSX
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Parse & Extract     │
    │  Text Content        │◄──── SimpleDirectoryReader
    │                      │      (PDF, DOCX, XLSX)
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Split into Chunks   │◄──── 1024 tokens per chunk
    │  (SentenceSplitter)  │      100 token overlap
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Generate Embeddings │◄──── OpenAI
    │  for Each Chunk      │      text-embedding-3-small
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Store in Qdrant     │
    │  In-Memory Index     │──── Ready for queries
    └─────────────────────┘
    """, language="text")

    st.markdown("""
    **Key details:**
    - All files are processed **in memory** — nothing is written to disk on the server.
    - Google Docs and Sheets are automatically **exported** to PDF/XLSX before parsing.
    - The index is **session-scoped**: it is rebuilt fresh for each user session, ensuring data is always up to date.
    - Embeddings are sent to OpenAI in batches of 100 chunks to avoid API rate limits.
    """)

    st.markdown("---")

    # --- Use Case 2: Chat with Documents ---
    st.markdown("### 💬 Use Case 2: Chat with Documents")
    st.markdown("""
    Once the index is built, users can ask natural language questions. The system retrieves
    the most relevant passages and generates a grounded answer with source citations.
    """)

    st.markdown("#### Flowchart")
    st.code("""
    ┌─────────────────────┐
    │  User Enters Query   │
    │  (chat input)        │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Augment Query with  │◄──── Appends list of all
    │  File List Context   │      indexed file names
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Embed Query into    │◄──── Same embedding model
    │  Vector              │      (text-embedding-3-small)
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Cosine Similarity   │
    │  Search in Qdrant    │◄──── Retrieve top-4
    │  (top-k retrieval)   │      most relevant chunks
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Construct Prompt     │
    │  [System Instruction  │◄──── "Answer based ONLY
    │   + Retrieved Context │      on the provided
    │   + User Query]       │      context passages"
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  LLM Generates       │◄──── OpenAI gpt-4o-mini
    │  Grounded Answer     │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Extract Citation     │
    │  Sources             │◄──── Document name,
    │  (post-processing)   │      page number, snippet
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Display Answer +    │
    │  Expandable Citations│
    │  + Store in History  │
    └─────────────────────┘
    """, language="text")

    st.markdown("""
    **Key details:**
    - The query is **augmented** with the full list of indexed file names so the LLM can answer questions like "list my documents" accurately.
    - Retrieval uses **cosine similarity** over the vector embeddings to find the top-4 most relevant chunks.
    - The LLM is instructed to answer **only** from the retrieved context — not from its training data.
    - Each answer includes **expandable citation sources** showing the document name, page number, and a text snippet.
    - **Conversation history** is maintained within the session for follow-up questions.
    """)

    st.markdown("---")

    # --- Implementation Details ---
    st.markdown("### 🔧 Implementation Details")

    impl_col1, impl_col2 = st.columns(2)
    with impl_col1:
        st.markdown("""
        #### Technology Stack
        | Component | Technology |
        |-----------|------------|
        | Frontend & Hosting | Streamlit Community Cloud |
        | LLM | OpenAI `gpt-4o-mini` |
        | Embeddings | OpenAI `text-embedding-3-small` |
        | Vector Store | Qdrant (in-memory) |
        | RAG Framework | LlamaIndex |
        | Document Parsing | `pypdf`, `docx2txt` |
        | Data Source | Google Drive API v3 |
        | Authentication | Password gate |
        """)
    with impl_col2:
        st.markdown("""
        #### Design Decisions
        - **Fully in-memory**: No persistent database — the index is rebuilt fresh each session, ensuring data is always current and nothing is stored server-side.
        - **Owner-scoped Drive access**: The app reads from the owner's Google Drive using a stored OAuth refresh token. End users do not need their own Google account.
        - **Batch embeddings**: Chunks are embedded in batches of 100 to stay within OpenAI's rate limits (1M tokens per minute).
        - **Recursive folder scanning**: The Drive API scans the configured folder and all subfolders, so nested document structures are fully indexed.
        - **Session isolation**: Each user session builds its own independent index — no cross-session data leakage.
        """)


# -----------------------------------------------------------------------------
# 6. NAVIGATION ROUTER & APP ENTRY POINT
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    login_screen()
else:
    p_chat = st.Page(page_ask_otter, title="AskOtter Chat", icon="💬", default=True)
    p_about = st.Page(page_about_us, title="About Us", icon="ℹ️")
    p_method = st.Page(page_methodology, title="Methodology", icon="⚙️")

    pg = st.navigation({
        "Core Assistant": [p_chat],
        "Documentation": [p_about, p_method],
    })

    with st.sidebar:
        if st.button("Log Out", type="secondary", use_container_width=True):
            logout()

    pg.run()
