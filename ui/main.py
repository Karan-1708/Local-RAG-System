import sys
from pathlib import Path

# Ensure the project root is on sys.path regardless of how streamlit was invoked.
# When running `streamlit run ui/main.py`, Streamlit inserts ui/ as sys.path[0],
# which breaks `from ui.xxx import ...` since it looks for ui/ inside ui/.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import warnings
import nest_asyncio
from dotenv import load_dotenv
import streamlit as st

# Must happen before any src imports
load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)
nest_asyncio.apply()

from ui.state import init_session_state
from ui.sidebar import render_sidebar
from ui.chat import render_chat_history, render_chat_input

st.set_page_config(page_title="Local RAG: Secure Q&A", page_icon="🛡️", layout="wide")

# Reduce Streamlit's default excessive top padding and leave room at the
# bottom so messages are never hidden behind the sticky chat input bar.
st.markdown("""
<style>
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 5rem !important;
}
</style>
""", unsafe_allow_html=True)

init_session_state()

# Sidebar — returns the active engine selection (uploader lives inside sidebar)
provider, selected_model, api_key = render_sidebar()

# Active chat reference (after sidebar may have changed it)
active_chat = st.session_state.chats[st.session_state.active_chat_id]

# Chat history — no fixed height, grows naturally with messages.
# Page scrolls normally; st.chat_input() pins itself to the bottom of the
# viewport automatically so it is always visible regardless of scroll position.
history_container = st.container(border=False)
render_chat_history(history_container, active_chat)

# Chat input — Streamlit pins this to the bottom of the viewport automatically
render_chat_input(history_container, active_chat, provider, selected_model, api_key)
