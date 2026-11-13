"""Real RAG pipeline: document ingestion, Qdrant vector storage, LlamaIndex retrieval."""
import os
import stat
import tempfile
from pathlib import Path

# Set NLTK data path BEFORE any imports that might trigger NLTK
_nltk_dir = os.path.join(tempfile.gettempdir(), "nltk_private")
os.makedirs(_nltk_dir, exist_ok=True)
try:
    os.chmod(_nltk_dir, stat.S_IRWXU)
except OSError:
    pass
os.environ["NLTK_DATA"] = _nltk_dir

_nltk_ready = False

def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    import nltk
    nltk.data.path = [_nltk_dir]
    nltk.download("stopwords", download_dir=_nltk_dir, quiet=True)
    nltk.download("punkt_tab", download_dir=_nltk_dir, quiet=True)
    for root, dirs, files in os.walk(_nltk_dir):
        try:
            os.chmod(root, stat.S_IRWXU)
        except OSError:
            pass
        for fn in files:
            try:
                os.chmod(os.path.join(root, fn), stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
    _nltk_ready = True

from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

COLLECTION_NAME = "ask_otter_docs"


def _configure_models():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key, embed_batch_size=50)
    Settings.llm = OpenAI(model="gpt-4o-mini", api_key=api_key)
    Settings.node_parser = SentenceSplitter(chunk_size=2048, chunk_overlap=200)


def build_index_from_memory(files: list[tuple[str, bytes]]):
    """Builds an in-memory vector index from file bytes. Returns (index, chunk_count)."""
    _ensure_nltk()

    if not files:
        raise ValueError("No files to index.")

    _configure_models()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_paths = []
        for name, content in files:
            dest = Path(tmp_dir) / name
            with open(dest, "wb") as out:
                out.write(content)
            tmp_paths.append(str(dest))
        documents = SimpleDirectoryReader(input_files=tmp_paths).load_data()

    nodes = Settings.node_parser.get_nodes_from_documents(documents)

    qdrant_client = QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes, storage_context=storage_context, show_progress=True)

    return index, len(nodes)


def query_index(index, question: str, top_k: int = 4) -> dict:
    """Runs a grounded query against an in-memory index."""
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
