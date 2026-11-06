"""Real RAG pipeline: document ingestion, Qdrant vector storage, LlamaIndex retrieval."""
import os
import tempfile
from pathlib import Path

_nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
os.makedirs(_nltk_data_dir, exist_ok=True)
os.environ["NLTK_DATA"] = _nltk_data_dir

import nltk
nltk.data.path = [_nltk_data_dir]
nltk.download("stopwords", download_dir=_nltk_data_dir, quiet=True)
nltk.download("punkt_tab", download_dir=_nltk_data_dir, quiet=True)

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
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large", api_key=api_key)
    Settings.llm = OpenAI(model="gpt-4o-mini", api_key=api_key)
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)


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


def build_index_from_memory(files: list[tuple[str, bytes]]):
    """Builds an in-memory (non-persisted) vector index from in-memory file bytes.

    Used for the Google Drive auto-import flow: nothing here touches disk except a
    temp dir that is deleted immediately after parsing, and the Qdrant collection
    lives only in RAM for the lifetime of this session — never written to QDRANT_PATH.
    Returns the VectorStoreIndex object itself; caller keeps it in session state.
    """
    if not files:
        raise ValueError("No Drive files were found to import.")

    _configure_models()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_paths = []
        for name, content in files:
            dest = Path(tmp_dir) / name
            with open(dest, "wb") as out:
                out.write(content)
            tmp_paths.append(str(dest))

        documents = SimpleDirectoryReader(input_files=tmp_paths).load_data()

    client = QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    nodes = Settings.node_parser.get_nodes_from_documents(documents)
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
