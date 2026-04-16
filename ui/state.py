import json
import uuid
import streamlit as st
from datetime import datetime
from src.utils import logger
import config

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.csv', '.md', '.png', '.jpg', '.jpeg'}
STATE_FILE = config.BASE_DIR / "session_state.json"


def _new_chat() -> dict:
    return {
        "name": "New Chat",
        "messages": [],
        "pinned": False,
        "enable_ragas": False,
        "created_at": datetime.now().isoformat()
    }


def load_persistent_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    new_id = str(uuid.uuid4())
    return {
        "active_chat_id": new_id,
        "api_keys": {},
        "chats": {new_id: _new_chat()}
    }


def save_persistent_state():
    state = {
        "active_chat_id": st.session_state.active_chat_id,
        "api_keys": st.session_state.api_keys,
        "chats": st.session_state.chats,
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


def new_chat_entry() -> tuple[str, dict]:
    """Creates a new chat ID + dict and returns both."""
    cid = str(uuid.uuid4())
    return cid, _new_chat()


def init_session_state():
    """Initialise all session state on first Streamlit run."""
    if "startup_logged" not in st.session_state:
        from src.utils import log_startup_info
        log_startup_info()
        st.session_state.startup_logged = True

    if "state_loaded" not in st.session_state:
        persisted = load_persistent_state()
        st.session_state.chats = persisted.get("chats", {})
        st.session_state.api_keys = persisted.get("api_keys", {})
        st.session_state.active_chat_id = persisted.get("active_chat_id")
        st.session_state.confirm_reset = False
        st.session_state.state_loaded = True

    # Back-fill missing enable_ragas key for older persisted chats
    for cid in st.session_state.chats:
        if "enable_ragas" not in st.session_state.chats[cid]:
            st.session_state.chats[cid]["enable_ragas"] = False
