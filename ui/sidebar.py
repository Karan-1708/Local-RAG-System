import os
import platform
import subprocess
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Optional

from ui.state import ALLOWED_EXTENSIONS, STATE_FILE, save_persistent_state, new_chat_entry
from ui.pdf_export import export_chat_to_pdf
from ui.uploader import render_uploader
from src.vector_store import reset_database, delete_document, delete_chat_data
from src.ollama_utils import get_local_models, pull_new_model, is_ollama_running
from src.utils import get_hardware_info
from src.api_config import FRONTIER_PROVIDERS
import config


def open_folder(path: str):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def _render_conversations():
    st.header("💬 Conversations")
    if st.button("➕ New Conversation", use_container_width=True):
        cid, chat = new_chat_entry()
        st.session_state.chats[cid] = chat
        st.session_state.active_chat_id = cid
        save_persistent_state()
        st.rerun()

    pinned = [cid for cid, c in st.session_state.chats.items() if c.get("pinned")]
    recent = [cid for cid, c in st.session_state.chats.items() if not c.get("pinned")]

    if pinned:
        st.subheader("📌 Pinned")
        for cid in pinned:
            _render_chat_row(cid, is_pinned=True)

    st.subheader("🕒 Recent")
    for cid in recent:
        _render_chat_row(cid, is_pinned=False)


def _render_chat_row(cid: str, is_pinned: bool):
    chat = st.session_state.chats[cid]
    label = f"📍 {chat['name']}" if is_pinned else chat['name']
    col1, col2 = st.columns([0.8, 0.2])
    if col1.button(label, key=f"btn_{cid}", use_container_width=True):
        st.session_state.active_chat_id = cid
        st.rerun()
    with col2.popover("⚙️"):
        new_name = st.text_input("Rename", value=chat['name'], key=f"ren_{cid}")
        if new_name != chat['name']:
            st.session_state.chats[cid]['name'] = new_name
            save_persistent_state()
            st.rerun()
        if is_pinned:
            if st.button("📍 Unpin", key=f"unpin_{cid}"):
                st.session_state.chats[cid]['pinned'] = False
                save_persistent_state()
                st.rerun()
        else:
            num_pinned = sum(1 for c in st.session_state.chats.values() if c.get("pinned"))
            if st.button("📌 Pin", key=f"pin_{cid}", disabled=(num_pinned >= 3)):
                st.session_state.chats[cid]['pinned'] = True
                save_persistent_state()
                st.rerun()
        st.download_button("📄 PDF Export", data=export_chat_to_pdf(cid),
                           file_name=f"{chat['name']}.pdf", key=f"pdf_{cid}")
        if st.button("🗑️ Delete", key=f"del_{cid}", type="primary"):
            delete_chat_data(cid)
            del st.session_state.chats[cid]
            if not st.session_state.chats:
                cid_new, chat_new = new_chat_entry()
                st.session_state.chats[cid_new] = chat_new
                st.session_state.active_chat_id = cid_new
            elif st.session_state.active_chat_id == cid:
                st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
            save_persistent_state()
            st.rerun()


def _render_engine() -> tuple[str, str, Optional[str]]:
    st.header("🧠 Engine")
    provider = st.selectbox("LLM Provider", ["Ollama", "OpenAI", "Google Gemini", "Anthropic"])

    if provider == "Ollama":
        if is_ollama_running():
            st.sidebar.markdown("🟢 **Ollama Connected**")
            available_models = get_local_models()
            selected_model = st.selectbox("Active Model", available_models, index=0)
            with st.expander("⬇️ Pull New Model"):
                new_m = st.text_input("Model Name", placeholder="phi3")
                if st.button("Download"):
                    if new_m:
                        p = st.progress(0, text="Initializing...")
                        status_text = st.empty()
                        for chunk in pull_new_model(new_m):
                            if chunk.get("status") == "error":
                                st.error(chunk.get("message"))
                                p.empty()
                                status_text.empty()
                                break
                            status_text.markdown(f"📥 {chunk.get('status', 'Downloading...')}")
                            if "completed" in chunk and "total" in chunk:
                                p.progress(min(chunk["completed"] / chunk["total"], 1.0))
                        else:
                            st.success(f"Ready: {new_m}")
                            st.rerun()
        else:
            st.sidebar.markdown("🔴 **Ollama Offline**")
            selected_model = config.LLM_MODEL
        api_key = None

    else:
        saved_key = st.session_state.api_keys.get(provider, "")
        st.sidebar.markdown(f"🟢 **{provider} Ready**" if saved_key else f"🟡 **Waiting for Key**")
        m_list = FRONTIER_PROVIDERS[provider]["models"] + ["Other (Custom Name)"]
        choice = st.selectbox("Active Model", m_list)
        selected_model = (
            st.text_input("Name", value="" if choice == "Other (Custom Name)" else choice)
            if choice == "Other (Custom Name)" else choice
        )
        api_key = st.text_input("API Key", value=saved_key, type="password", key=f"key_{provider}")
        if api_key != saved_key:
            st.session_state.api_keys[provider] = api_key
            save_persistent_state()
            st.rerun()

    st.sidebar.caption(f"🎯 **Model:** {selected_model}")
    st.sidebar.success(f"**Hardware:** {get_hardware_info()}")
    return provider, selected_model, api_key


def _render_evaluation(active_chat: dict):
    st.header("📊 Evaluation")
    st.info("💡 **How it works:** This uses **RAGAS** (Retrieval-Augmented Generation Assessment) to score the quality of AI answers. It checks **Faithfulness** (no hallucinations) and **Answer Relevancy**.")
    is_eval_on = active_chat.get("enable_ragas", False)
    if st.button(
        "🚀 " + ("Advanced Eval: ON" if is_eval_on else "Standard Eval: OFF"),
        type="primary" if is_eval_on else "secondary",
        use_container_width=True
    ):
        active_chat["enable_ragas"] = not is_eval_on
        save_persistent_state()
        st.rerun()
    with st.expander("❓ When to use this?"):
        st.markdown("""
        - **Turn it ON:** When you need to verify that the AI is accurately citing your documents and not making things up.
        - **Turn it OFF:** When you just want quick answers and don't need the detailed quality scores.

        **📊 Understanding Metrics:**
        - **Faithfulness:** (0 to 1) Higher is better. Checks if the AI's answer is supported by your documents.
        - **Relevancy:** (0 to 1) Higher is better. Checks if the AI's answer actually addresses your question.
        - **Perplexity:** (0 to 100+) **Lower is better.**
            - **0 - 20:** Excellent. Very fluent and confident.
            - **20 - 50:** Good. Clear and readable.
            - **50 - 100:** Average. Might have minor oddities.
            - **100+:** Confused. The AI is likely struggling or hallucinating.

        *Note: Advanced evaluation takes extra time (30-60s) as it runs multiple quality checks.*
        """)


def _render_knowledge_base():
    st.header("📂 Knowledge Base")

    # Upload widget lives here — keeps the main chat area clear
    render_uploader()

    chat_id = st.session_state.active_chat_id
    chat_data_dir = config.DATA_DIR / chat_id
    if chat_data_dir.exists():
        files = [f for f in os.listdir(chat_data_dir) if Path(f).suffix.lower() in ALLOWED_EXTENSIONS]
    else:
        files = []

    if not files:
        st.caption("No documents in this chat yet.")
    else:
        st.caption(f"{len(files)} file(s) indexed in this chat")
        for f_name in files:
            col1, col2 = st.columns([0.8, 0.2])
            col1.text(f"📄 {f_name}")
            if col2.button("🗑️", key=f"del_doc_{f_name}"):
                if delete_document(f_name, chat_id):
                    st.success(f"Removed {f_name}")
                    st.rerun()
                else:
                    st.error("Failed to delete.")


def _render_storage():
    st.header("📂 Storage")
    chat_id = st.session_state.active_chat_id
    chat_data_dir = config.DATA_DIR / chat_id
    col1, col2 = st.columns(2)
    if col1.button("📁 Uploads", use_container_width=True):
        open_folder(str(chat_data_dir if chat_data_dir.exists() else config.DATA_DIR))
    if col2.button("🗄️ Database", use_container_width=True):
        open_folder(str(config.DB_DIR))

    if not st.session_state.confirm_reset:
        if st.button("🔄 System Reset", type="primary", use_container_width=True):
            st.session_state.confirm_reset = True
            st.rerun()
    else:
        st.warning("⚠️ Wipe Everything?")
        c1, c2 = st.columns(2)
        if c1.button("✅ Yes", type="primary", use_container_width=True):
            if reset_database():
                st.session_state.chats = {}
                st.session_state.api_keys = {}
                cid, chat = new_chat_entry()
                st.session_state.chats[cid] = chat
                st.session_state.active_chat_id = cid
                st.session_state.confirm_reset = False
                if STATE_FILE.exists():
                    os.remove(STATE_FILE)
                st.success("Wiped!")
                st.rerun()
        if c2.button("❌ No", use_container_width=True):
            st.session_state.confirm_reset = False
            st.rerun()


def render_sidebar() -> tuple[str, str, Optional[str]]:
    """Renders the full sidebar. Returns (provider, selected_model, api_key)."""
    with st.sidebar:
        st.markdown("""
        <style>
            [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }
            .sidebar-header {
                position: sticky; top: 0; background-color: white; z-index: 999;
                padding-top: 1.5rem; padding-bottom: 1rem;
                border-bottom: 1px solid #f0f2f6; text-align: center; margin-top: -1rem;
            }
            @media (prefers-color-scheme: dark) {
                .sidebar-header { background-color: #0e1117; border-bottom: 1px solid #262730; }
            }
            .centered-title { text-align: center; font-size: 1.8rem; font-weight: 700; margin-bottom: 0; }
            .centered-caption { text-align: center; font-size: 0.9rem; opacity: 0.7; margin-top: -0.5rem; }
        </style>
        <div class="sidebar-header">
            <div class="centered-title">🛡️ Local RAG</div>
            <div class="centered-caption">Private & Secure AI Reader</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        active_chat = st.session_state.chats[st.session_state.active_chat_id]
        st.info(f"📍 Viewing: **{active_chat['name']}**")

        _render_conversations()
        st.divider()
        provider, selected_model, api_key = _render_engine()
        st.divider()
        _render_evaluation(active_chat)
        st.divider()
        _render_knowledge_base()
        st.divider()
        _render_storage()

    return provider, selected_model, api_key
