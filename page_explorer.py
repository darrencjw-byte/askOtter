"""Document Explorer page — Use Case 2: browse, search, and quiz over indexed documents."""
import streamlit as st
import pandas as pd
from datetime import datetime

import rag_engine


def page_document_explorer():
    st.title("🔎 Document Explorer")
    st.caption("Browse, search, and test your knowledge across indexed documents")

    if st.session_state.get("memory_index") is None:
        st.warning("No index available. Please wait for the index to finish building on the Chat page.")
        return

    tab_overview, tab_search, tab_quiz = st.tabs([
        "📊 Document Overview",
        "🔍 Smart Search",
        "🧠 Knowledge Quiz",
    ])

    with tab_overview:
        _render_overview_tab()

    with tab_search:
        _render_search_tab()

    with tab_quiz:
        _render_quiz_tab()


# ---------------------------------------------------------------------------
# Tab 1: Document Overview
# ---------------------------------------------------------------------------
def _render_overview_tab():
    doc_stats = st.session_state.get("doc_stats", [])
    if not doc_stats:
        st.info("Document statistics are not available yet.")
        return

    total_files = len(doc_stats)
    total_pages = sum(d.get("page_count", 0) for d in doc_stats)
    total_chunks = sum(d.get("chunk_count", 0) for d in doc_stats)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Documents", total_files)
    col2.metric("Total Pages", total_pages)
    col3.metric("Total Chunks", total_chunks)

    st.markdown("---")

    st.markdown("#### Indexed Documents")
    df = pd.DataFrame(doc_stats)
    display_cols = {"file_name": "File Name", "file_type": "Type", "page_count": "Pages", "chunk_count": "Chunks"}
    df_display = df.rename(columns=display_cols)
    st.dataframe(
        df_display[list(display_cols.values())],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    st.markdown("#### Chunks per Document")
    chart_df = pd.DataFrame({
        "Document": [d["file_name"] for d in doc_stats],
        "Chunks": [d["chunk_count"] for d in doc_stats],
    }).set_index("Document")
    st.bar_chart(chart_df)


# ---------------------------------------------------------------------------
# Tab 2: Smart Search (personalised, filtered)
# ---------------------------------------------------------------------------
def _render_search_tab():
    file_names = st.session_state.get("indexed_file_names", [])
    if not file_names:
        st.info("No documents indexed yet.")
        return

    st.markdown("#### Personalised Document Search")
    st.caption("Filter by document, adjust result count and style to get tailored answers.")

    with st.form("smart_search_form"):
        query = st.text_input("Search query", placeholder="e.g. What is prompt engineering?")
        selected_docs = st.multiselect(
            "Search within specific documents (leave empty for all)",
            options=sorted(file_names),
            default=[],
        )
        col_k, col_style = st.columns(2)
        with col_k:
            num_results = st.select_slider("Number of results", options=[3, 6, 10], value=6)
        with col_style:
            style = st.radio("Response style", ["Concise", "Detailed", "Bullet points"], horizontal=True)

        submitted = st.form_submit_button("Search", use_container_width=True, type="primary")

    if submitted and query:
        index = st.session_state["memory_index"]
        with st.spinner("Searching documents..."):
            try:
                result = rag_engine.filtered_query(
                    index=index,
                    question=query,
                    file_filter=selected_docs if selected_docs else None,
                    top_k=num_results,
                    style=style,
                    file_names=st.session_state.get("indexed_file_names"),
                )
                st.markdown("#### Answer")
                st.markdown(result["answer"])

                if result["sources"]:
                    with st.expander("📚 Citation Sources"):
                        for idx, src in enumerate(result["sources"], 1):
                            st.markdown(f"**[{idx}] {src['title']}** (Page {src['page']})")
                            st.caption(f'"{src["snippet"]}"')

                    scores = [s["score"] for s in result["sources"] if s["score"] is not None]
                    if scores:
                        st.markdown("#### Relevance Scores")
                        score_df = pd.DataFrame({
                            "Source": [f"{s['title']} (p.{s['page']})" for s in result["sources"] if s["score"] is not None],
                            "Score": scores,
                        }).set_index("Source")
                        st.bar_chart(score_df)
            except Exception as exc:
                st.error(f"Search failed: {exc}")
    elif submitted:
        st.warning("Please enter a search query.")


# ---------------------------------------------------------------------------
# Tab 3: Knowledge Quiz
# ---------------------------------------------------------------------------
def _render_quiz_tab():
    if "quiz_history" not in st.session_state:
        st.session_state["quiz_history"] = []
    if "current_quiz" not in st.session_state:
        st.session_state["current_quiz"] = None
    if "quiz_answers" not in st.session_state:
        st.session_state["quiz_answers"] = {}
    if "quiz_checked" not in st.session_state:
        st.session_state["quiz_checked"] = False

    st.markdown("#### Test Your Knowledge")
    st.caption("Generate a quiz from the indexed documents to test your understanding.")

    col_topic, col_diff = st.columns(2)
    with col_topic:
        topic = st.text_input("Topic", placeholder="e.g. Prompt Engineering, Tokens, LLM Hallucinations", key="quiz_topic")
    with col_diff:
        difficulty = st.radio("Difficulty", ["Easy", "Medium", "Hard"], horizontal=True, key="quiz_difficulty")

    if st.button("Generate Quiz", type="primary", use_container_width=True):
        if not topic:
            st.warning("Please enter a topic.")
        else:
            index = st.session_state.get("memory_index")
            if index is None:
                st.error("No index available.")
                return
            with st.spinner(f"Generating {difficulty.lower()} quiz on '{topic}'..."):
                try:
                    questions = rag_engine.generate_quiz(index, topic, difficulty)
                    st.session_state["current_quiz"] = {"topic": topic, "difficulty": difficulty, "questions": questions}
                    st.session_state["quiz_answers"] = {}
                    st.session_state["quiz_checked"] = False
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to generate quiz: {exc}")

    quiz = st.session_state.get("current_quiz")
    if quiz and quiz.get("questions"):
        st.markdown(f"### Quiz: {quiz['topic']} ({quiz['difficulty']})")
        st.markdown("---")

        questions = quiz["questions"]
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}.** {q['question']}")
            answer_key = f"quiz_q_{i}"
            st.session_state["quiz_answers"][answer_key] = st.radio(
                f"Select answer for Q{i+1}",
                options=q.get("options", []),
                key=f"quiz_radio_{i}",
                label_visibility="collapsed",
            )
            if st.session_state["quiz_checked"]:
                user_ans = st.session_state["quiz_answers"].get(answer_key, "")
                correct_ans = q.get("correct", "")
                correct_letter = correct_ans[0] if correct_ans else ""
                user_letter = user_ans[0] if user_ans else ""
                if user_letter == correct_letter:
                    st.success(f"Correct! {q.get('explanation', '')}")
                else:
                    st.error(f"Incorrect. The correct answer is **{correct_ans}**. {q.get('explanation', '')}")
                if q.get("source"):
                    st.caption(f"Source: {q['source']}")
            st.markdown("---")

        if not st.session_state["quiz_checked"]:
            if st.button("Check Answers", type="primary", use_container_width=True):
                st.session_state["quiz_checked"] = True

                correct_count = 0
                for i, q in enumerate(questions):
                    user_ans = st.session_state["quiz_answers"].get(f"quiz_q_{i}", "")
                    correct_ans = q.get("correct", "")
                    if user_ans and correct_ans and user_ans[0] == correct_ans[0]:
                        correct_count += 1

                st.session_state["quiz_history"].append({
                    "topic": quiz["topic"],
                    "difficulty": quiz["difficulty"],
                    "score": correct_count,
                    "total": len(questions),
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
                st.rerun()
        else:
            correct_count = 0
            for i, q in enumerate(questions):
                user_ans = st.session_state["quiz_answers"].get(f"quiz_q_{i}", "")
                correct_ans = q.get("correct", "")
                if user_ans and correct_ans and user_ans[0] == correct_ans[0]:
                    correct_count += 1
            st.markdown(f"### Score: {correct_count} / {len(questions)}")

            if st.button("New Quiz", use_container_width=True):
                st.session_state["current_quiz"] = None
                st.session_state["quiz_answers"] = {}
                st.session_state["quiz_checked"] = False
                st.rerun()

    history = st.session_state.get("quiz_history", [])
    if history:
        st.markdown("---")
        st.markdown("#### Quiz History")
        hist_df = pd.DataFrame(history)
        hist_df["label"] = hist_df.apply(lambda r: f"{r['topic']} ({r['difficulty']}) @ {r['timestamp']}", axis=1)
        hist_df["percentage"] = (hist_df["score"] / hist_df["total"] * 100).round(0)
        chart_df = hist_df[["label", "percentage"]].set_index("label")
        chart_df.columns = ["Score (%)"]
        st.bar_chart(chart_df)
