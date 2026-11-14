"""Real RAG pipeline: per-document indexing, filtered queries, quiz generation."""
import json
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
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterCondition
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

_RAG_PROMPT_TEMPLATE = (
    "You are AskOtter, a public sector RAG (Retrieval-Augmented Generation) "
    "document assistant built for the AI Champion Bootcamp.\n\n"
    "ABOUT YOURSELF:\n"
    "- You are powered by OpenAI gpt-4o as the language model.\n"
    "- You use text-embedding-3-large for document embeddings.\n"
    "- You use LlamaIndex as the RAG framework with Qdrant as the in-memory vector store.\n"
    "- You are deployed on Streamlit Community Cloud.\n"
    "- Your documents are sourced from a pre-configured Google Drive folder.\n\n"
    "{personalisation_section}"
    "RULES:\n"
    "1. For questions about document CONTENT (facts, policies, procedures): "
    "answer using ONLY the retrieved context below. Cite document name and page.\n"
    "2. For questions about the documents THEMSELVES (listing files, counting, "
    "sorting, comparing file names): use the COMPLETE FILE LIST below and "
    "apply your own reasoning (sorting, formatting, etc.).\n"
    "3. For questions about yourself (what model, how you work, your architecture): "
    "answer using the ABOUT YOURSELF section above.\n"
    "4. For follow-up or conversational questions: answer helpfully based on "
    "the context and conversation.\n"
    "5. Only say you cannot find information when the user asks about specific "
    "content that is genuinely not in any retrieved passage.\n"
    "6. When listing files, always sort them in ascending order by name.\n\n"
    "{file_list_section}"
    "-----\n"
    "CONTEXT FROM RETRIEVED DOCUMENTS:\n"
    "{context_str}\n"
    "-----\n\n"
    "USER QUESTION: {query_str}\n\n"
    "ANSWER:"
)


def _build_rag_prompt(file_names: list[str] | None = None, user_profile: dict | None = None) -> PromptTemplate:
    if file_names:
        sorted_names = sorted(file_names)
        file_list = "\n".join(f"  - {name}" for name in sorted_names)
        file_section = f"COMPLETE LIST OF ALL INDEXED FILES ({len(sorted_names)} files, sorted):\n{file_list}\n\n"
    else:
        file_section = ""

    if user_profile:
        parts = ["USER PROFILE (personalise your response accordingly):\n"]
        if user_profile.get("name"):
            parts.append(f"- Name: {user_profile['name']}\n")
        if user_profile.get("role"):
            parts.append(f"- Role: {user_profile['role']}\n")
        if user_profile.get("experience"):
            parts.append(f"- AI/LLM Experience Level: {user_profile['experience']}\n")
        if user_profile.get("answer_style"):
            parts.append(f"- Preferred Answer Style: {user_profile['answer_style']}\n")
        if user_profile.get("topics"):
            parts.append(f"- Topics of Interest: {', '.join(user_profile['topics'])}\n")
        parts.append("Adjust your tone, detail level, and vocabulary to match this user's profile.\n\n")
        personalisation_section = "".join(parts)
    else:
        personalisation_section = ""

    prompt_text = _RAG_PROMPT_TEMPLATE.replace(
        "{file_list_section}", file_section
    ).replace(
        "{personalisation_section}", personalisation_section
    )
    return PromptTemplate(prompt_text)

COLLECTION_NAME = "ask_otter_docs"

PLATFORM_API_BASE = os.getenv("PLATFORM_API_BASE", "https://api.ai.tech.gov.sg/platform/models/v1")
PLATFORM_API_KEY = os.getenv("PLATFORM_API_KEY", "")


def _configure_models():
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-large",
        api_key=openai_key,
        embed_batch_size=50,
    )

    Settings.llm = OpenAI(model="gpt-4o", api_key=openai_key)

    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)


def _file_type_from_name(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        ".pdf": "PDF",
        ".docx": "DOCX",
        ".xlsx": "XLSX",
        ".txt": "TXT",
        ".md": "Markdown",
    }.get(ext, ext.upper().lstrip(".") or "Unknown")


def build_index_from_memory(files: list[tuple[str, bytes]]):
    """Builds an in-memory vector index, processing each document individually.

    Returns (index, chunk_count, doc_stats) where doc_stats is a list of dicts
    with per-document metadata: file_name, file_type, page_count, chunk_count.
    """
    _ensure_nltk()

    if not files:
        raise ValueError("No files to index.")

    _configure_models()

    all_nodes = []
    doc_stats = []

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

        doc_stats.append({
            "file_name": name,
            "file_type": _file_type_from_name(name),
            "page_count": len(documents),
            "chunk_count": len(nodes),
        })

    if not all_nodes:
        raise ValueError("No content could be extracted from the uploaded files.")

    logger.info(f"Embedding {len(all_nodes)} total chunks across {len(files)} documents...")
    qdrant_client = QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(all_nodes, storage_context=storage_context, show_progress=True)

    return index, len(all_nodes), doc_stats


def _is_broad_query(question: str) -> bool:
    """Detect queries that need broad coverage across all documents."""
    q = question.lower()
    broad_keywords = ["summarise", "summarize", "summary", "overview", "list all",
                      "list document", "list my", "all documents", "all files",
                      "key points", "main points", "what are the documents"]
    return any(kw in q for kw in broad_keywords)


def query_index(index, question: str, top_k: int = 6, file_names: list[str] | None = None, user_profile: dict | None = None) -> dict:
    """RAG query: retrieve relevant chunks, then generate a grounded answer."""
    _configure_models()

    effective_top_k = 20 if _is_broad_query(question) else top_k

    logger.info(f"Step 1: Retrieving top-{effective_top_k} chunks for: {question[:80]}...")
    retriever = index.as_retriever(similarity_top_k=effective_top_k)
    retrieved_nodes = retriever.retrieve(question)
    logger.info(f"Step 1 done: {len(retrieved_nodes)} chunks retrieved")

    logger.info("Step 2: Building RAG prompt...")
    rag_prompt = _build_rag_prompt(file_names, user_profile=user_profile)

    logger.info("Step 3: Sending to LLM (gpt-4o)...")
    query_engine = index.as_query_engine(
        similarity_top_k=effective_top_k,
        text_qa_template=rag_prompt,
    )
    response = query_engine.query(question)
    logger.info("Step 3 done: LLM response received")

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


def filtered_query(index, question: str, file_filter: list[str], top_k: int = 6, user_profile: dict | None = None) -> dict:
    """RAG query restricted to specific documents by file name."""
    _configure_models()

    filters = MetadataFilters(
        filters=[MetadataFilter(key="file_name", value=fn) for fn in file_filter],
        condition=FilterCondition.OR,
    )

    logger.info(f"Filtered query (files={file_filter}): {question[:80]}...")
    retriever = index.as_retriever(similarity_top_k=top_k, filters=filters)
    retrieved_nodes = retriever.retrieve(question)
    logger.info(f"Filtered retrieval: {len(retrieved_nodes)} chunks")

    rag_prompt = _build_rag_prompt(file_names=file_filter, user_profile=user_profile)
    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        text_qa_template=rag_prompt,
        node_postprocessors=[],
    )
    response = query_engine.query(question)

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
        sources.append({
            "title": title,
            "page": page,
            "snippet": snippet,
            "score": round(node.score, 3) if node.score is not None else None,
        })

    return {"answer": str(response), "sources": sources}


_QUIZ_PROMPT = """Based on the following document excerpts, generate exactly {num_questions} multiple-choice questions to test understanding of the topic "{topic}".

DOCUMENT EXCERPTS:
{context}

Return ONLY a valid JSON array. Each element must be an object with these exact keys:
- "question": the question text
- "options": an array of exactly 4 answer strings labelled A through D
- "correct": the letter of the correct answer ("A", "B", "C", or "D")
- "explanation": a brief explanation of why the correct answer is right, citing the source
- "source": the file name the question is based on

Example format:
[{{"question": "What is X?", "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"], "correct": "B", "explanation": "Because...", "source": "file.pdf"}}]

Return ONLY the JSON array, no other text."""


def generate_quiz(index, topic: str, num_questions: int = 5) -> list[dict]:
    """Generate multiple-choice quiz questions grounded in indexed documents."""
    _configure_models()

    retriever = index.as_retriever(similarity_top_k=15)
    nodes = retriever.retrieve(topic)

    if not nodes:
        return []

    context_parts = []
    for node in nodes:
        meta = node.node.metadata or {}
        label = f"[{meta.get('file_name', 'Unknown')} — Page {meta.get('page_label', '?')}]"
        context_parts.append(f"{label}\n{node.node.get_content()}")
    context = "\n\n".join(context_parts)

    prompt = _QUIZ_PROMPT.format(
        num_questions=num_questions,
        topic=topic,
        context=context,
    )

    llm = Settings.llm
    response = llm.complete(prompt)
    raw = str(response).strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        questions = json.loads(raw)
        if not isinstance(questions, list):
            raise ValueError("Response is not a list")
        return questions[:num_questions]
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(f"Quiz generation JSON parse failed: {exc}")
        logger.debug(f"Raw response: {raw[:500]}")
        return []
