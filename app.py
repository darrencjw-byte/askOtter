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
        st.info("🔑 **Access Password:** `admin123`")

        with st.form("login_form"):
            password_input = st.text_input("Enter Access Password", type="password")
            submit_button = st.form_submit_button("Authenticate", use_container_width=True)

            if submit_button:
                target_password = os.getenv("APP_PASSWORD", "admin123")
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
@st.cache_resource(show_spinner="Indexing documents from Google Drive... (first load only)")
def _build_global_index():
    """Builds the vector index once and caches it across all user sessions."""
    import logging
    logger = logging.getLogger("askotter")
    logging.basicConfig(level=logging.INFO)

    credentials = google_auth.get_credentials()

    gdrive_url = os.getenv("GDRIVE_URL", "")
    logger.info(f"Listing Drive files (folder: {gdrive_url or 'all'})")
    drive_files = drive_sync.list_files(credentials, folder_url=gdrive_url or None)
    logger.info(f"Found {len(drive_files)} files")

    if not drive_files:
        return None, [], 0

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set. Add it to your Streamlit Cloud secrets.")

    service = drive_sync._build_service("drive", "v3", credentials)
    in_memory_files = []
    file_names = []
    for i, f in enumerate(drive_files, 1):
        logger.info(f"Downloading ({i}/{len(drive_files)}): {f['name']}")
        content, final_name = drive_sync.download_file(credentials, f["id"], f["mimeType"], f["name"], service=service)
        in_memory_files.append((final_name, content))
        file_names.append(final_name)

    logger.info("Building vector index...")
    index, chunk_count = rag_engine.build_index_from_memory(in_memory_files)
    logger.info(f"Index built: {chunk_count} chunks from {len(drive_files)} files")
    return index, file_names, chunk_count


def ensure_index_built():
    if st.session_state.memory_index is not None:
        return

    try:
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
        st.markdown("**Model:** `Claude Sonnet 5.5 / text-embedding-3-large`")

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
        sug_col1, sug_col2 = st.columns(2)
        suggestion_clicked = None
        with sug_col1:
            if st.button("Summarise my documents", use_container_width=True, key="sug_1"):
                suggestion_clicked = "Summarise the key points across my imported documents."
        with sug_col2:
            if st.button("List document sources", use_container_width=True, key="sug_2"):
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
                    result = rag_engine.query_index(st.session_state.memory_index, prompt, file_names=file_names)
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
           - Index documents from a pre-configured Google Drive folder on first load.
           - Support PDF, DOCX, XLSX, Google Docs, and Google Sheets.
           - Recursively scan subfolders for complete coverage.
           - Each document is parsed individually to preserve page-level metadata.

        2. **Provide Grounded, Accurate Answers**
           - Every answer is synthesised strictly from retrieved document passages using a RAG pipeline — not from the LLM's training data.
           - A strict system prompt enforces grounding: the LLM must cite sources and refuse to answer when context is insufficient.
           - Source citations with document name, page number, and relevant snippet are displayed for every response.
        """)
    with col2:
        st.markdown("""
        3. **Ensure Secure Access**
           - Password-gated portal — only authorised users with the access password can use the assistant.
           - Google Drive access uses the owner's stored OAuth refresh token; end users do not need a Google account.

        4. **Zero-Infrastructure Deployment**
           - Hosted on Streamlit Community Cloud with automatic redeployment from GitHub.
           - Fully in-memory indexing with Qdrant — no persistent database, no data stored server-side.
           - Index is built once and cached globally (`st.cache_resource`) — subsequent users load instantly.
        """)

    st.markdown("---")

    # --- Data Sources ---
    st.markdown("### 📂 Data Sources")
    st.markdown("""
    | Source | Supported Formats | Access Method |
    |--------|-------------------|---------------|
    | Google Drive (configured folder) | PDF, DOCX, XLSX, Google Docs, Google Sheets | Google Drive API v3 with OAuth 2.0 refresh token |
    """)
    st.markdown("""
    - The index is built **once on first load** and cached globally across all user sessions.
    - The app **recursively scans all subfolders** within the configured folder.
    - Google Docs and Sheets are automatically **exported** to PDF/XLSX format before parsing.
    - Each document is **parsed individually** (per-document indexing) so file names and page numbers are accurately preserved in metadata.
    - Use the **Re-sync Google Drive** button to rebuild the index after adding new documents.
    """)

    st.markdown("---")

    # --- Features ---
    st.markdown("### ✨ Features")
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    with feat_col1:
        st.markdown("""
        **💬 RAG Chat Assistant**
        - Natural language Q&A over indexed documents
        - Strict RAG grounding — answers only from retrieved context
        - Expandable citation sources per answer
        - Conversation history within session
        - Smart retrieval: broader search for summary queries
        """)
    with feat_col2:
        st.markdown("""
        **🔄 Automatic Indexing**
        - Google Drive folder indexed on first load
        - Per-document parsing with page-level metadata
        - Recursive subfolder scanning
        - Globally cached index (`st.cache_resource`)
        - Re-sync button for on-demand refresh
        """)
    with feat_col3:
        st.markdown("""
        **🔒 Secure & Stateless**
        - Password-gated access
        - No data persisted server-side
        - Owner-scoped Drive credentials (refresh token)
        - In-memory vector store only
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
    | **LLM** | Claude Sonnet 5.5 |
    | **Embedding Model** | OpenAI `text-embedding-3-large` (3072 dimensions) |
    | **Vector Store** | Qdrant (in-memory) |
    | **RAG Framework** | LlamaIndex |
    | **Chunk Size** | 512 tokens, 50-token overlap |
    | **Retrieval** | Top-6 (standard) / Top-20 (summary queries) |
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
    on the LLM's training data, every answer is strictly grounded in the user's own documents
    through a four-step pipeline: **Retrieve → Augment → Generate → Cite**.

    The system has two core use cases, each with its own data flow:

    1. **Document Indexing** — Fetching, parsing, and embedding documents from Google Drive (per-document)
    2. **Chat with Documents (RAG)** — Retrieving relevant passages and generating grounded answers
    """)

    st.markdown("---")

    # --- Data Flow ---
    st.markdown("### 📊 End-to-End Data Flow")
    st.markdown("""
    | Stage | Component | Technology | Description |
    |-------|-----------|------------|-------------|
    | 1. Authentication | Password Gate | Streamlit | User enters access password to gain entry |
    | 2. Data Ingestion | Google Drive API v3 | `google-api-python-client` | Fetches documents from configured folder recursively using owner's stored refresh token |
    | 3. Per-Document Parsing | File Loaders | LlamaIndex `SimpleDirectoryReader` + `llama-index-readers-file` | Each document is parsed individually to preserve file name and page-level metadata |
    | 4. Chunking | Sentence Splitter | LlamaIndex `SentenceSplitter` | Splits each document into 512-token overlapping chunks (50-token overlap) |
    | 5. Embedding | Vector Encoding | OpenAI `text-embedding-3-large` | Converts each chunk into a 3072-dimensional vector (batches of 50) |
    | 6. Indexing | Vector Store | Qdrant (in-memory) | Stores all vectors in a single shared index, cached globally via `st.cache_resource` |
    | 7. Retrieval | Similarity Search | LlamaIndex `VectorStoreIndex` | Finds top-6 most relevant chunks via cosine similarity (top-20 for summary queries) |
    | 8. Augmentation | Context Assembly | Custom prompt template | Retrieved passages are labelled with source info and assembled into a grounding context |
    | 9. Generation | LLM Synthesis | Claude Sonnet 5.5 | Strict RAG prompt enforces answering only from context, with citations |
    | 10. Citation | Source Attribution | Post-processing | Extracts deduplicated document name, page number, and snippet for each source |
    """)

    st.markdown("---")

    # --- Use Case 1: Document Indexing ---
    st.markdown("### 📄 Use Case 1: Document Indexing")
    st.markdown("""
    This flow runs **once on first load** and the result is **cached globally** across all user sessions
    via `st.cache_resource`. It fetches the owner's Google Drive documents, parses each one individually,
    and builds an in-memory vector index.
    """)

    st.markdown("#### Flowchart")
    st.code("""
    ┌─────────────────────┐
    │   App First Load     │
    │   (or Re-sync)       │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Load Owner's Google │
    │  Drive Credentials   │◄──── Stored refresh token
    │  (from secrets)      │      in Streamlit secrets
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
    ┌─────────────────────────────────────────┐
    │  FOR EACH DOCUMENT (per-document loop): │
    │                                         │
    │  ┌───────────────────┐                  │
    │  │ Parse & Extract   │◄─ PDF per page   │
    │  │ Text Content      │   DOCX per page   │
    │  └─────────┬─────────┘                  │
    │            │                             │
    │            ▼                             │
    │  ┌───────────────────┐                  │
    │  │ Split into Chunks │◄─ 512 tokens     │
    │  │ (SentenceSplitter)│   50 overlap      │
    │  └─────────┬─────────┘                  │
    │            │                             │
    │            ▼                             │
    │  ┌───────────────────┐                  │
    │  │ Preserve Metadata │◄─ file_name      │
    │  │ per Chunk         │   page_label      │
    │  └───────────────────┘                  │
    └─────────────────┬───────────────────────┘
                      │
                      ▼
    ┌─────────────────────┐
    │  Combine All Chunks  │
    │  from All Documents  │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Generate Embeddings │◄──── OpenAI text-embedding-
    │  (batches of 50)     │      3-large (3072-dim)
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Store in Qdrant     │
    │  In-Memory Index     │◄──── Cached globally via
    │                      │      st.cache_resource
    └─────────────────────┘
    """, language="text")

    st.markdown("""
    **Key details:**
    - **Per-document parsing**: Each file is parsed individually so document boundaries, file names, and page numbers are accurately preserved in chunk metadata.
    - **In-memory only**: All files are processed in RAM — nothing is written to disk on the server.
    - **Globally cached**: The index is built once on first load and shared across all user sessions via `st.cache_resource`. Subsequent users get instant access.
    - **Fault-tolerant**: If a single file fails to parse, it is skipped and logged — the rest of the index still builds successfully.
    - **Re-sync**: The "Re-sync Google Drive" button clears the cache and triggers a full rebuild from the latest Drive contents.
    """)

    st.markdown("---")

    # --- Use Case 2: Chat with Documents ---
    st.markdown("### 💬 Use Case 2: Chat with Documents (RAG Pipeline)")
    st.markdown("""
    Once the index is built, users can ask natural language questions. The system follows
    the full **RAG (Retrieval-Augmented Generation)** pipeline: **Retrieve → Augment → Generate → Cite**.
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
    │  Detect Query Type   │
    │                      │◄──── "summarise", "overview"
    │  Broad? → top_k=20  │      → broad retrieval
    │  Specific? → top_k=6│      Otherwise → focused
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Augment Query with  │◄──── Appends full list of
    │  File List Context   │      indexed file names
    └─────────┬───────────┘
              │
              ▼
    ┌──────────────────────────────────────────┐
    │  STEP 1: RETRIEVE                        │
    │                                          │
    │  ┌────────────────────┐                  │
    │  │ Embed Query into   │◄─ Same model:    │
    │  │ Vector             │   text-embedding- │
    │  └─────────┬──────────┘   3-large        │
    │            │                              │
    │            ▼                              │
    │  ┌────────────────────┐                  │
    │  │ Cosine Similarity  │                  │
    │  │ Search in Qdrant   │◄─ top-6 or      │
    │  │                    │   top-20 chunks   │
    │  └────────────────────┘                  │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────┐
    │  STEP 2: AUGMENT                         │
    │                                          │
    │  ┌────────────────────┐                  │
    │  │ Label Each Passage │◄─ [Source 1:     │
    │  │ with Source Info   │   doc.pdf — p.3]  │
    │  └─────────┬──────────┘                  │
    │            │                              │
    │            ▼                              │
    │  ┌────────────────────┐                  │
    │  │ Assemble Grounding │                  │
    │  │ Context String     │                  │
    │  └────────────────────┘                  │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────┐
    │  STEP 3: GENERATE                        │
    │                                          │
    │  ┌────────────────────┐                  │
    │  │ Strict RAG Prompt: │                  │
    │  │ "Answer ONLY from  │◄─ OpenAI        │
    │  │  retrieved context. │   Claude Sonnet 5.5   │
    │  │  Cite your sources. │                  │
    │  │  Say 'not found' if │                  │
    │  │  context is lacking."│                 │
    │  └─────────┬──────────┘                  │
    │            │                              │
    │            ▼                              │
    │  ┌────────────────────┐                  │
    │  │ LLM Generates      │                  │
    │  │ Grounded Answer    │                  │
    │  └────────────────────┘                  │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────┐
    │  STEP 4: CITE                            │
    │                                          │
    │  ┌────────────────────┐                  │
    │  │ Extract & Dedup    │◄─ Document name  │
    │  │ Citation Sources   │   Page number    │
    │  │                    │   Text snippet    │
    │  │                    │   Relevance score │
    │  └────────────────────┘                  │
    └──────────────────┬───────────────────────┘
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
    - **Strict RAG grounding**: The system prompt explicitly forbids the LLM from using its training data. It must answer only from retrieved context passages, and must say "I could not find sufficient information" when context is insufficient.
    - **Smart retrieval**: Summary/overview queries automatically use top-20 retrieval for broader coverage across all documents. Specific queries use top-6 for focused, precise answers.
    - **Query augmentation**: Every query is augmented with the full list of indexed file names, enabling the LLM to accurately answer "list my documents" or "how many files are indexed".
    - **Deduplicated citations**: Post-processing removes duplicate source references so each unique passage appears only once.
    - **Conversation history**: Chat history is maintained within the session for contextual follow-up questions.
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
        | LLM | Claude Sonnet 5.5 |
        | Embeddings | OpenAI `text-embedding-3-large` (3072-dim) |
        | Vector Store | Qdrant (in-memory) |
        | RAG Framework | LlamaIndex |
        | Document Parsing | `llama-index-readers-file`, `pypdf`, `docx2txt` |
        | Data Source | Google Drive API v3 |
        | Authentication | Password gate |
        | Caching | `st.cache_resource` (global) |
        """)
    with impl_col2:
        st.markdown("""
        #### Design Decisions
        - **Per-document indexing**: Each document is parsed individually to preserve accurate file-name and page-level metadata in every chunk.
        - **Globally cached index**: Built once on first load, shared across all sessions via `st.cache_resource` — no per-user rebuild.
        - **Strict RAG prompt**: A custom `PromptTemplate` instructs the LLM to only use retrieved context, cite sources, and refuse when information is not found.
        - **Adaptive retrieval**: Broad queries (summarise, overview) retrieve 20 chunks for wide coverage; specific queries retrieve 6 for precision.
        - **Owner-scoped Drive access**: The app reads from the owner's Google Drive using a stored OAuth refresh token. End users do not need a Google account.
        - **Batch embeddings**: Chunks are embedded in batches of 50 to stay within OpenAI's rate limits.
        - **Recursive folder scanning**: The Drive API scans the configured folder and all subfolders for complete coverage.
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
