from typing import Optional
import streamlit as st

from ui.state import save_persistent_state
from src.generation import query_rag


def render_chat_history(history_container, active_chat: dict):
    """Renders the full message history into the scrollable container."""
    with history_container:
        for m in active_chat["messages"]:
            with st.chat_message(m["role"], avatar="🛡️" if m["role"] == "assistant" else None):
                st.markdown(m["content"])
                if m.get("metrics"):
                    st.info(m["metrics"])
                if m.get("citations"):
                    with st.expander("📚 Sources & References"):
                        for c in m["citations"]:
                            st.markdown(f"**{c['source']}**")
                            st.caption(c['snippet'])


def render_chat_input(
    history_container,
    active_chat: dict,
    provider: str,
    selected_model: str,
    api_key: Optional[str]
):
    """Renders the chat input and handles streaming response generation."""
    prompt = st.chat_input("Ask about your architecture, code, or data...")

    if not prompt:
        return

    if not active_chat["messages"]:
        active_chat["name"] = prompt[:30] + "..."

    with history_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    current_history = [(m["role"], m["content"]) for m in active_chat["messages"]]
    active_chat["messages"].append({"role": "user", "content": prompt})

    with history_container:
        with st.chat_message("assistant", avatar="🛡️"):
            placeholder = st.empty()
            full_res = ""
            meta = None

            for chunk in query_rag(prompt, st.session_state.active_chat_id, active_chat["enable_ragas"], provider, selected_model, api_key, current_history):
                if isinstance(chunk, str):
                    full_res += chunk
                    placeholder.markdown(full_res + "▌")
                else:
                    meta = chunk

            placeholder.markdown(full_res)

            m_txt  = meta.get("metrics",   "") if meta else ""
            c_list = meta.get("citations", []) if meta else []

            if m_txt:
                st.info(m_txt)
            if c_list:
                with st.expander("📚 Sources & References"):
                    for c in c_list:
                        st.markdown(f"**{c['source']}**")
                        st.caption(c['snippet'])

    active_chat["messages"].append({
        "role": "assistant",
        "content": full_res,
        "metrics": m_txt,
        "citations": c_list
    })
    save_persistent_state()
    st.rerun()
