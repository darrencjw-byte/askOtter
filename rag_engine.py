"""Real RAG pipeline: document ingestion, Qdrant vector storage, LlamaIndex retrieval."""
import os
import stat
import tempfile
from pathlib import Path

_nltk_ready = False

def _ensure_nltk():
    """Download NLTK data to a private directory with correct permissions for Python 3.14."""
    global _nltk_ready
    if _nltk_ready:
        return
    import nltk

    nltk_dir = os.path.join(tempfile.gettempdir(), "nltk_private")
    os.makedirs(nltk_dir, exist_ok=True)
    try:
        os.chmod(nltk_dir, stat.S_IRWXU)
    except OSError:
        pass

    os.environ["NLTK_DATA"] = nltk_dir
    nltk.data.path = [nltk_dir]

    nltk.download("stopwords", download_dir=nltk_dir, quiet=True)
    nltk.download("punkt_tab", download_dir=nltk_dir, quiet=True)

    for root, dirs, _files in os.walk(nltk_dir):
        try:
            os.chmod(root, stat.S_IRWXU)
        except OSError:
            pass
        for fn in _files:
            try:
                os.chmod(os.path.join(root, fn), stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
    _nltk_ready = True

# Override LlamaIndex's internal NLTK cache path BEFORE importing it
_llama_nltk_cache = os.path.join(tempfile.gettempdir(), "nltk_private")
os.environ["NLTK_DATA"] = _llama_nltk_cache

from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

_rag_root = Path(tempfile.gettempdir()) / ".rag_data"
DATA_DIR = _rag_root / "documents"
QDRANT_PATH = str(_rag_root / "qdrant")
COLLECTION_NAME = "ask_otter_docs"


def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Path(QDRANT_PATH).mkdir(parents=True, exist_ok=True)


def _configure_models():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key, embed_batch_size=100)
    Settings.llm = OpenAI(model="gpt-4o-mini", api_key=api_key)
    Settings.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=100)


def _get_vector_store() -> QdrantVectorStore:
    client = QdrantClient(path=QDRANT_PATH)
    return QdrantVectorStore(client=client, collection_name=COLLECTION_NAME)


def save_uploaded_files(uploaded_files) -> int:
    """Write Streamlit UploadedFile objects to the documents folder. Returns count saved."""
    _ensure_dirs()
    count = 0
    for f in uploaded_files:
        dest = DATA_DIR / f.name
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        count += 1
    return count


def list_documents() -> list[str]:
    _ensure_dirs()
    return sorted(p.name for p in DATA_DIR.glob("*") if p.is_file())


def has_index() -> bool:
    _ensure_dirs()
    return QdrantClient(path=QDRANT_PATH).collection_exists(COLLECTION_NAME)


def build_index() -> int:
    """(Re)builds the vector index from every file currently in DATA_DIR. Returns chunk count."""
    _ensure_nltk()
    _ensure_dirs()
    _configure_models()

    files = [str(p) for p in DATA_DIR.glob("*") if p.is_file()]
    if not files:
        raise ValueError("No documents to index. Upload a file first.")

    documents = SimpleDirectoryReader(input_files=files).load_data()

    client = QdrantClient(path=QDRANT_PATH)
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    nodes = Settings.node_parser.get_nodes_from_documents(documents)
    index = VectorStoreIndex(nodes, storage_context=storage_context)

    return len(nodes)


def build_index_from_memory(files: list[tuple[str, bytes]], progress=None):
    """Builds an in-memory (non-persisted) vector index from in-memory file bytes."""
    def _log(msg):
        if progress:
            progress.write(msg)

    _log("  ↳ Downloading NLTK data...")
    _ensure_nltk()

    if not files:
        raise ValueError("No Drive files were found to import.")

    _log("  ↳ Configuring OpenAI models...")
    _configure_models()

    _log("  ↳ Verifying OpenAI API key...")
    import openai
    client_test = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=15, max_retries=1)
    try:
        client_test.embeddings.create(input="test", model="text-embedding-3-small")
    except openai.RateLimitError as exc:
        raise ValueError(f"OpenAI quota exhausted — add credits at https://platform.openai.com/settings/organization/billing/: {exc}")
    except Exception as exc:
        raise ValueError(f"OpenAI API key check failed: {exc}")

    _log("  ↳ Parsing documents...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_paths = []
        for name, content in files:
            dest = Path(tmp_dir) / name
            with open(dest, "wb") as out:
                out.write(content)
            tmp_paths.append(str(dest))

        documents = SimpleDirectoryReader(input_files=tmp_paths).load_data()

    _log(f"  ↳ Splitting into chunks ({len(documents)} document sections)...")
    nodes = Settings.node_parser.get_nodes_from_documents(documents)

    _log(f"  ↳ Embedding {len(nodes)} chunks via OpenAI (this may take a moment)...")
    qdrant_client = QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes, storage_context=storage_context)

    return index, len(nodes)


def query_index(index, question: str, top_k: int = 4) -> dict:
    """Runs a grounded query against an in-memory index (see build_index_from_memory)."""
    _configure_models()
    query_engine = index.as_query_engine(similarity_top_k=top_k)

    response = query_engine.query(question)

    sources = []
    for node in response.source_nodes:
        metadata = node.node.metadata or {}
        sources.append(
            {
                "title": metadata.get("file_name", "Unknown document"),
                "page": metadata.get("page_label", "—"),
                "snippet": node.node.get_content()[:280].strip().replace("\n", " "),
                "score": round(node.score, 3) if node.score is not None else None,
            }
        )

    return {"answer": str(response), "sources": sources}


def query(question: str, top_k: int = 4) -> dict:
    """Runs a grounded query against the indexed documents. Returns answer + source citations."""
    if not has_index():
        raise ValueError("No index found. Upload documents and build the index first.")

    _configure_models()
    vector_store = _get_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store)
    query_engine = index.as_query_engine(similarity_top_k=top_k)

    response = query_engine.query(question)

    sources = []
    for node in response.source_nodes:
        metadata = node.node.metadata or {}
        sources.append(
            {
                "title": metadata.get("file_name", "Unknown document"),
                "page": metadata.get("page_label", "—"),
                "snippet": node.node.get_content()[:280].strip().replace("\n", " "),
                "score": round(node.score, 3) if node.score is not None else None,
            }
        )

    return {"answer": str(response), "sources": sources}
