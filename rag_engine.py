"""Real RAG pipeline: per-document indexing for accuracy."""
import os
import stat
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger("askotter")

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

from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex, PromptTemplate
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

RAG_SYSTEM_PROMPT = PromptTemplate(
    "You are AskOtter, a public sector document assistant. Your task is to "
    "answer questions accurately using ONLY the context passages retrieved "
    "from the user's indexed documents.\n\n"
    "STRICT RULES:\n"
    "1. ONLY use information from the context below. Do NOT use your training data.\n"
    "2. If the context does not contain enough information to answer, say "
    "\"I could not find sufficient information in the indexed documents to answer this question.\"\n"
    "3. Always cite which document and page the information comes from.\n"
    "4. Be precise and concise. Quote directly from the source when possible.\n"
    "5. If asked to list documents, list ALL documents mentioned in the context.\n\n"
    "-----\n"
    "CONTEXT FROM RETRIEVED DOCUMENTS:\n"
    "{context_str}\n"
    "-----\n\n"
    "USER QUESTION: {query_str}\n\n"
    "ANSWER (grounded in the context above):"
)

COLLECTION_NAME = "ask_otter_docs"


def _configure_models():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key, embed_batch_size=50)
    Settings.llm = OpenAI(model="gpt-4o-mini", api_key=api_key)
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)


def build_index_from_memory(files: list[tuple[str, bytes]]):
    """Builds an in-memory vector index, processing each document individually.

    Each file is parsed and chunked separately so document boundaries and
    metadata (file_name, page_label) are preserved accurately. All chunks
    are then embedded and added to a single shared Qdrant index.
    """
    _ensure_nltk()

    if not files:
        raise ValueError("No files to index.")

    _configure_models()

    all_nodes = []

    for i, (name, content) in enumerate(files, 1):
        logger.info(f"Parsing document ({i}/{len(files)}): {name}")
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / name
            with open(dest, "wb") as out:
                out.write(content)
            try:
                documents = SimpleDirectoryReader(input_files=[str(dest)]).load_data()
            except Exception as exc:
                logger.warning(f"Skipping {name}: {exc}")
                continue

        nodes = Settings.node_parser.get_nodes_from_documents(documents)
        logger.info(f"  → {len(documents)} pages, {len(nodes)} chunks")
        all_nodes.extend(nodes)

    if not all_nodes:
        raise ValueError("No content could be extracted from the uploaded files.")

    logger.info(f"Embedding {len(all_nodes)} total chunks across {len(files)} documents...")
    qdrant_client = QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(all_nodes, storage_context=storage_context, show_progress=True)

    return index, len(all_nodes)


def _is_broad_query(question: str) -> bool:
    """Detect queries that need broad coverage across all documents."""
    q = question.lower()
    broad_keywords = ["summarise", "summarize", "summary", "overview", "list all",
                      "list document", "list my", "all documents", "all files",
                      "key points", "main points", "what are the documents"]
    return any(kw in q for kw in broad_keywords)


def query_index(index, question: str, top_k: int = 6) -> dict:
    """RAG query: retrieve relevant chunks, then generate a grounded answer."""
    _configure_models()

    # Use broader retrieval for summary/overview queries
    effective_top_k = 20 if _is_broad_query(question) else top_k

    # Step 1: RETRIEVE — find the most relevant chunks via vector similarity
    retriever = index.as_retriever(similarity_top_k=effective_top_k)
    retrieved_nodes = retriever.retrieve(question)

    logger.info(f"RAG retrieval: {len(retrieved_nodes)} chunks (top_k={effective_top_k}) for: {question[:80]}...")
    for node in retrieved_nodes:
        meta = node.node.metadata or {}
        logger.info(f"  → [{meta.get('file_name', '?')} p.{meta.get('page_label', '?')}] score={node.score:.3f}")

    # Step 2: AUGMENT — build the context string from retrieved passages
    context_parts = []
    for i, node in enumerate(retrieved_nodes, 1):
        meta = node.node.metadata or {}
        source_label = f"[Source {i}: {meta.get('file_name', 'Unknown')} — Page {meta.get('page_label', '—')}]"
        context_parts.append(f"{source_label}\n{node.node.get_content()}")
    context_str = "\n\n".join(context_parts)

    # Step 3: GENERATE — send the grounded prompt to the LLM
    query_engine = index.as_query_engine(
        similarity_top_k=effective_top_k,
        text_qa_template=RAG_SYSTEM_PROMPT,
    )
    response = query_engine.query(question)

    # Step 4: Extract citation sources
    sources = []
    seen = set()
    for node in response.source_nodes:
        metadata = node.node.metadata or {}
        title = metadata.get("file_name", "Unknown document")
        page = metadata.get("page_label", "—")
        snippet = node.node.get_content()[:280].strip().replace("\n", " ")
        key = (title, page, snippet[:80])
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "title": title,
                "page": page,
                "snippet": snippet,
                "score": round(node.score, 3) if node.score is not None else None,
            }
        )

    return {"answer": str(response), "sources": sources}
