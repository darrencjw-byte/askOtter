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
# 4. INDEX BUILDER (runs once per session, uses owner's Drive credentials)
# -----------------------------------------------------------------------------
def ensure_index_built():
    status = st.session_state.memory_index_status
    if status is not None and status != "building":
        return

    st.session_state.memory_index_status = "building"
    try:
        progress = st.status("Building index from Google Drive...", expanded=True)

        progress.write("🔑 Loading Drive credentials...")
        credentials = google_auth.get_credentials()

        gdrive_url = os.getenv("GDRIVE_URL", "")
        progress.write("📂 Listing Google Drive files...")
        drive_files = drive_sync.list_files(credentials, folder_url=gdrive_url or None)

        if not drive_files:
            progress.update(label="No files found", state="complete")
            st.session_state.memory_index_status = "empty"
            return

        progress.write(f"📥 Downloading {len(drive_files)} file(s)...")
        service = drive_sync._build_service("drive", "v3", credentials)
        in_memory_files = []
        indexed_file_names = []
        for i, f in enumerate(drive_files, 1):
            progress.write(f"  ↳ ({i}/{len(drive_files)}) {f['name']}")
            content, final_name = drive_sync.download_file(credentials, f["id"], f["mimeType"], f["name"], service=service)
            in_memory_files.append((final_name, content))
            indexed_file_names.append(final_name)
        st.session_state["indexed_file_names"] = indexed_file_names

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set. Add it to your Streamlit Cloud secrets.")

        progress.write("🧠 Chunking documents and generating embeddings...")
        index, _chunk_count = rag_engine.build_index_from_memory(in_memory_files, progress=progress)

        st.session_state.memory_index = index
        st.session_state.memory_index_status = "ready"
        progress.update(label=f"Index ready — {_chunk_count} chunks from {len(drive_files)} file(s)", state="complete")
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
    st.title("ℹ️ About AskOtter")
    st.markdown("### Public Sector AI Innovation")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **AskOtter** is an enterprise Retrieval-Augmented Generation (RAG) agent developed for the **AI Champion Bootcamp (August – November 2026)**.

        #### Primary Objectives:
        * **Automate Document Discovery**: Index institutional memory from a configured Google Drive folder.
        * **Zero Hallucination Target**: Enforce strict source citations on every query answer.
        * **Secure Access**: Password-gated access to the portal.
        """)
    with col2:
        st.info("""
        #### Key Metadata
        * **Repo Slug:** `askOtter`
        * **Deployment Runtime:** Streamlit Community Cloud
        * **Submission Portal:** LaunchPad
        * **Target Grading Focus:** Session State, Prompt Engineering, Agent Tools (25% Weightage)
        """)


# PAGE 3: METHODOLOGY
def page_methodology():
    st.title("⚙️ System Methodology & Architecture")
    st.markdown("### Technical Framework & Flowchart")

    st.markdown("""
    #### 1. End-to-End Data Flow
    1. **Ingestion Layer**: On each session start, documents (`.pdf`, `.docx`, `.xlsx`) are fetched from a pre-configured Google Drive folder via the Google Drive API using stored owner credentials.
    2. **Vector Indexing**: Documents are parsed into overlapping chunks and converted to vector embeddings using OpenAI `text-embedding-3-small`. The index lives entirely in RAM (Qdrant in-memory) — nothing is written to disk.
    3. **Query Engine**: Streamlit passes user queries to the LlamaIndex retriever, extracting the top-*k* relevant passages based on cosine similarity.
    4. **Grounded Synthesis**: Retrieved context and the user query are merged into a constrained system prompt before invoking OpenAI `gpt-4o-mini` for answer generation with source citations.
    """)

    st.markdown("#### 2. Process Architecture")
    st.code("""
[ Google Drive API ] ---> [ In-Memory Chunking & Embeddings ] ---> [ Qdrant In-Memory ]
          (owner credentials)                                              |
[ User Query ] ----------> [ Password Gate ] -------------------> [ Vector Retriever ]
                                                                          |
[ Grounded Answer + Citations ] <---------- [ LLM Synthesis ] <-----------+
    """, language="text")

    st.markdown("""
    #### 3. Key Design Decisions
    * **Fully in-memory**: No persistent vector database — the index is rebuilt fresh each session from the configured Drive folder.
    * **Owner-scoped Drive access**: The app reads from the owner's Google Drive using a stored refresh token — users do not need their own Google account.
    * **Password-gated access**: Simple password authentication protects the portal.
    * **Deployed on Streamlit Community Cloud**: Zero-infrastructure hosting with automatic redeployment from GitHub.
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
