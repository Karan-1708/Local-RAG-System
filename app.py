import streamlit as st
import warnings
import nest_asyncio
import shutil
import os
import json
import uuid
import platform
import subprocess
import torch
from pathlib import Path
from datetime import datetime
from fpdf import FPDF, XPos, YPos

warnings.filterwarnings("ignore", category=DeprecationWarning)
nest_asyncio.apply()

from src.ingestion import load_documents
from src.chunks import split_documents
from src.vector_store import save_to_chroma, reset_database
from src.generation import query_rag
from src.utils import logger, get_safe_path, ensure_directory, get_device, get_hardware_info
from src.ollama_utils import get_local_models, pull_new_model, is_ollama_running
from src.api_config import FRONTIER_PROVIDERS
import config

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.csv', '.md', '.png', '.jpg', '.jpeg'}
STATE_FILE = config.BASE_DIR / "session_state.json"

def load_persistent_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    new_chat_id = str(uuid.uuid4())
    return {
        "active_chat_id": new_chat_id,
        "api_keys": {},
        "chats": {
            new_chat_id: {
                "name": "New Chat",
                "messages": [],
                "pinned": False,
                "enable_ragas": False,
                "created_at": datetime.now().isoformat()
            }
        }
    }

def save_persistent_state():
    state = {
        "active_chat_id": st.session_state.active_chat_id,
        "api_keys": st.session_state.api_keys,
        "chats": st.session_state.chats
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

if "state_loaded" not in st.session_state:
    persisted = load_persistent_state()
    st.session_state.chats = persisted.get("chats", {})
    st.session_state.api_keys = persisted.get("api_keys", {})
    st.session_state.active_chat_id = persisted.get("active_chat_id")
    st.session_state.confirm_reset = False
    st.session_state.state_loaded = True

for cid in st.session_state.chats:
    if "enable_ragas" not in st.session_state.chats[cid]:
        st.session_state.chats[cid]["enable_ragas"] = False


class PDF(FPDF):
    def header(self):
        self.set_fill_color(31, 119, 180)
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 22)
        self.cell(0, 15, "LOCAL RAG SYSTEM", ln=True, align='C')
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, "ANONYMIZED TECHNICAL ANALYSIS REPORT", ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential | Generated on {datetime.now().strftime('%Y-%m-%d')}", align='C')

    def draw_watermark(self):
        self.set_font("Helvetica", "B", 50)
        self.set_text_color(240, 240, 240)
        with self.rotation(45, 105, 148):
            self.text(40, 190, "SECURE REPORT")


def export_chat_to_pdf(chat_id):
    chat = st.session_state.chats[chat_id]
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.draw_watermark()
    w = pdf.w - 2 * pdf.l_margin
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"CHAT ID: {chat_id[:8].upper()}", ln=True)
    pdf.cell(0, 8, f"SUBJECT: {chat['name'].upper()}", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"EXCHANGE COUNT: {len(chat['messages'])} messages", ln=True)
    pdf.ln(10)
    for msg in chat['messages']:
        role = msg['role'].upper()
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(31, 119, 180)
        pdf.cell(0, 8, f" [{role}]", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        clean_text = msg['content'].replace("**", "").replace("*", "").replace("`", "")
        clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(w, 6, clean_text)
        if msg.get("metrics"):
            pdf.ln(3)
            pdf.set_fill_color(250, 253, 255)
            pdf.set_draw_color(200, 220, 240)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 100, 120)
            metrics_txt = f"EVALUATION METRICS: {msg['metrics']}".replace("**", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(w, 5, metrics_txt, border=1, fill=True)
        citations = msg.get("citations", [])
        if citations:
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, "DATA SOURCES:", ln=True)
            pdf.set_font("Helvetica", "", 8)
            for cite in citations:
                pdf.cell(5)
                pdf.cell(0, 4, f"- {cite['source'].encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        pdf.ln(10)
        pdf.set_draw_color(230, 230, 230)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(5)
    return bytes(pdf.output())


def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


st.set_page_config(page_title="Local RAG: Secure Q&A", page_icon="🛡️", layout="wide")

# =============================================================================
# CSS + JS  — pinned sidebar header & fixed bottom toolbar
# =============================================================================
st.markdown("""
<script>
(function () {
    "use strict";
    function qs(sel, root) { return (root || document).querySelector(sel); }

    function pinBottomBar() {
        if (document.getElementById("rag-bottom-bar")) return true;
        const dropzone = qs('[data-testid="stFileUploaderDropzone"]');
        if (!dropzone) return false;

        let block = dropzone.closest('[data-testid="stVerticalBlock"]');
        while (block) {
            if (qs('[data-testid="stChatInput"]', block)) break;
            const parent = block.parentElement;
            block = parent ? parent.closest('[data-testid="stVerticalBlock"]') : null;
        }
        if (!block) return false;

        const bar = document.createElement("div");
        bar.id = "rag-bottom-bar";
        block.parentNode.insertBefore(bar, block);
        bar.appendChild(block);

        const sidebar = qs('section[data-testid="stSidebar"]');
        function syncLeft() {
            bar.style.left = sidebar ? sidebar.getBoundingClientRect().width + "px" : "0px";
        }
        syncLeft();
        if (sidebar) new ResizeObserver(syncLeft).observe(sidebar);
        return true;
    }

    let attempts = 0;
    function tryInit() {
        if (!pinBottomBar() && attempts++ < 50) setTimeout(tryInit, 100);
    }
    setTimeout(tryInit, 200);

    new MutationObserver(() => { tryInit(); }).observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    # This container is caught by the CSS "first-child" rule and made sticky
    with st.container():
        st.markdown("# 🛡️ Local RAG")
        st.caption("## Private & Secure AI Reader")
    
    # Everything below this will scroll
    st.divider()
    active_chat = st.session_state.chats[st.session_state.active_chat_id]
    st.info(f"📍 Viewing: **{active_chat['name']}**")

    st.header("💬 Conversations")
    if st.button("➕ New Conversation", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"name": "New Chat", "messages": [], "pinned": False,
                                           "enable_ragas": False, "created_at": datetime.now().isoformat()}
        st.session_state.active_chat_id = new_id
        save_persistent_state(); st.rerun()

    pinned_chats = [cid for cid, c in st.session_state.chats.items() if c.get("pinned")]
    recent_chats  = [cid for cid, c in st.session_state.chats.items() if not c.get("pinned")]

    if pinned_chats:
        st.subheader("📌 Pinned")
        for cid in pinned_chats:
            chat = st.session_state.chats[cid]
            col1, col2 = st.columns([0.8, 0.2])
            if col1.button(f"📍 {chat['name']}", key=f"btn_{cid}", use_container_width=True):
                st.session_state.active_chat_id = cid; st.rerun()
            with col2.popover("⚙️"):
                new_name = st.text_input("Rename", value=chat['name'], key=f"ren_{cid}")
                if new_name != chat['name']:
                    st.session_state.chats[cid]['name'] = new_name
                    save_persistent_state(); st.rerun()
                if st.button("📍 Unpin", key=f"unpin_{cid}"):
                    st.session_state.chats[cid]['pinned'] = False
                    save_persistent_state(); st.rerun()
                st.download_button("📄 PDF Export", data=export_chat_to_pdf(cid),
                                   file_name=f"{chat['name']}.pdf", key=f"pdf_{cid}")
                if st.button("🗑️ Delete", key=f"del_{cid}", type="primary"):
                    del st.session_state.chats[cid]
                    if st.session_state.active_chat_id == cid:
                        st.session_state.active_chat_id = (
                            list(st.session_state.chats.keys())[0]
                            if st.session_state.chats else str(uuid.uuid4())
                        )
                    save_persistent_state(); st.rerun()

    st.subheader("🕒 Recent")
    for cid in recent_chats:
        chat = st.session_state.chats[cid]
        col1, col2 = st.columns([0.8, 0.2])
        if col1.button(chat['name'], key=f"btn_{cid}", use_container_width=True):
            st.session_state.active_chat_id = cid; st.rerun()
        with col2.popover("⚙️"):
            new_name = st.text_input("Rename", value=chat['name'], key=f"ren_{cid}")
            if new_name != chat['name']:
                st.session_state.chats[cid]['name'] = new_name
                save_persistent_state(); st.rerun()
            num_p = len([c for c in st.session_state.chats.values() if c.get("pinned")])
            if st.button("📌 Pin", key=f"pin_{cid}", disabled=(num_p >= 3)):
                st.session_state.chats[cid]['pinned'] = True
                save_persistent_state(); st.rerun()
            st.download_button("📄 PDF Export", data=export_chat_to_pdf(cid),
                               file_name=f"{chat['name']}.pdf", key=f"pdf_{cid}")
            if st.button("🗑️ Delete", key=f"del_{cid}", type="primary"):
                del st.session_state.chats[cid]
                if not st.session_state.chats:
                    new_id = str(uuid.uuid4())
                    st.session_state.chats[new_id] = {"name": "New Chat", "messages": [], "pinned": False,
                                                       "enable_ragas": False, "created_at": datetime.now().isoformat()}
                    st.session_state.active_chat_id = new_id
                elif st.session_state.active_chat_id == cid:
                    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
                save_persistent_state(); st.rerun()

    st.divider()
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
                                p.empty(); status_text.empty(); break
                            current_status = chunk.get("status", "Downloading...")
                            status_text.markdown(f"📥 {current_status}")
                            if "completed" in chunk and "total" in chunk:
                                p.progress(min(chunk["completed"] / chunk["total"], 1.0))
                        else:
                            st.success(f"Ready: {new_m}"); st.rerun()
        else:
            st.sidebar.markdown("🔴 **Ollama Offline**")
            selected_model = config.LLM_MODEL
        api_key = None
    else:
        saved_key = st.session_state.api_keys.get(provider, "")
        if saved_key: st.sidebar.markdown(f"🟢 **{provider} Ready**")
        else:         st.sidebar.markdown(f"🟡 **Waiting for Key**")
        m_list = FRONTIER_PROVIDERS[provider]["models"] + ["Other (Custom Name)"]
        choice = st.selectbox("Active Model", m_list)
        selected_model = (
            st.text_input("Name", value="" if choice == "Other (Custom Name)" else choice)
            if choice == "Other (Custom Name)" else choice
        )
        api_key = st.text_input("API Key", value=saved_key, type="password", key=f"key_{provider}")
        if api_key != saved_key:
            st.session_state.api_keys[provider] = api_key
            save_persistent_state(); st.rerun()

    st.sidebar.caption(f"🎯 **Model:** {selected_model}")
    st.sidebar.success(f"**Hardware:** {get_hardware_info()}")

    st.divider()
    st.header("📂 Storage")
    col_f1, col_f2 = st.columns(2)
    if col_f1.button("📁 Uploads",  use_container_width=True): open_folder(str(config.DATA_DIR))
    if col_f2.button("🗄️ Database", use_container_width=True): open_folder(str(config.DB_DIR))

    if not st.session_state.confirm_reset:
        if st.button("🔄 System Reset", type="primary", use_container_width=True):
            st.session_state.confirm_reset = True; st.rerun()
    else:
        st.warning("⚠️ Wipe Everything?")
        c1, c2 = st.columns(2)
        if c1.button("✅ Yes", type="primary", use_container_width=True):
            if reset_database():
                st.session_state.chats = {}
                st.session_state.api_keys = {}
                new_id = str(uuid.uuid4())
                st.session_state.chats[new_id] = {"name": "New Chat", "messages": [], "pinned": False,
                                                   "enable_ragas": False, "created_at": datetime.now().isoformat()}
                st.session_state.active_chat_id = new_id
                st.session_state.confirm_reset = False
                if STATE_FILE.exists(): os.remove(STATE_FILE)
                st.success("Wiped!"); st.rerun()
        if c2.button("❌ No", use_container_width=True):
            st.session_state.confirm_reset = False; st.rerun()


# =============================================================================
# MAIN UI
# =============================================================================
active_chat = st.session_state.chats[st.session_state.active_chat_id]

# Scrollable chat history
history_container = st.container()
with history_container:
    for m in active_chat["messages"]:
        with st.chat_message(m["role"], avatar="🛡️" if m["role"] == "assistant" else None):
            st.markdown(m["content"])
            if m.get("metrics"):
                st.markdown(f"<div style='margin-top:10px;'>{m['metrics']}</div>", unsafe_allow_html=True)
            if m.get("citations"):
                with st.expander("📚 Sources & References"):
                    for c in m["citations"]:
                        st.markdown(f"**{c['source']}**")
                        st.caption(c['snippet'])

# ── Bottom toolbar (JS detects the dropzone and wraps this whole section) ─────
st.divider()

uploaded_files = st.file_uploader(
    "📎 Drag & Drop Documents (PDF, DOCX, TXT, CSV, MD, PNG, JPG)",
    accept_multiple_files=True
)

if uploaded_files:
    invalid = [f.name for f in uploaded_files if Path(f.name).suffix.lower() not in ALLOWED_EXTENSIONS]
    if invalid:
        st.error(f"🚨 Unsupported formats: {', '.join(invalid)}")
    else:
        with st.status("🚀 Processing Knowledge Base...", expanded=True) as status:
            ensure_directory(config.DATA_DIR)
            for f in uploaded_files:
                with open(get_safe_path(config.DATA_DIR, f.name), "wb") as file:
                    file.write(f.getbuffer())
            docs = load_documents(str(config.DATA_DIR))
            if docs:
                chunks = split_documents(docs)
                save_to_chroma(chunks)
                status.update(label=f"✅ Knowledge Base Updated ({len(chunks)} chunks)", state="complete")

col_input, col_eval = st.columns([0.88, 0.12], vertical_alignment="bottom")

with col_eval:
    is_eval_on = active_chat.get("enable_ragas", False)
    if st.button(
        "📊 Eval",
        type="primary" if is_eval_on else "secondary",
        use_container_width=True,
        help="Blue = Advanced Evaluation ON | Grey = Standard OFF"
    ):
        active_chat["enable_ragas"] = not is_eval_on
        save_persistent_state(); st.rerun()

with col_input:
    prompt = st.chat_input("Ask about your architecture, code, or data...")

if prompt:
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
            gen = query_rag(prompt, active_chat["enable_ragas"], provider, selected_model, api_key, current_history)
            for chunk in gen:
                if isinstance(chunk, str):
                    full_res += chunk
                    placeholder.markdown(full_res + "▌")
                else:
                    meta = chunk
            placeholder.markdown(full_res)
            m_txt  = meta.get("metrics",   "") if meta else ""
            c_list = meta.get("citations", []) if meta else []
            if m_txt:   st.info(m_txt)
            if c_list:
                with st.expander("📚 Sources & References"):
                    for c in c_list:
                        st.markdown(f"**{c['source']}**")
                        st.caption(c['snippet'])

    active_chat["messages"].append({"role": "assistant", "content": full_res, "metrics": m_txt, "citations": c_list})
    save_persistent_state(); st.rerun()