import streamlit as st
import os
import shutil
from src.ingestion import load_documents
from src.chunks import split_documents
from src.vector_store import save_to_chroma, reset_database
from src.generation import query_rag

st.set_page_config(page_title="Local RAG System", page_icon="🤖", layout="wide")

st.title("🤖 Local RAG: Private Technical Q&A")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Document Management")
    
    # RESET BUTTON
    if st.button("🔄 Reset System (Clear Memory)", type="primary"):
        if reset_database():
            st.session_state.messages = []
            st.success("Memory wiped! System is fresh.")
            st.rerun()
        else:
            st.error("Could not delete database. Please restart the app.")

    uploaded_files = st.file_uploader(
        "Upload technical docs", 
        accept_multiple_files=True
    )
    
    if st.button("Process Documents"):
        if uploaded_files:
            with st.spinner("Processing..."):
                raw_dir = os.path.join(os.getcwd(), "data", "raw")
                
                if os.path.exists(raw_dir):
                    shutil.rmtree(raw_dir)
                os.makedirs(raw_dir)
                
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(raw_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                docs = load_documents(raw_dir)
                chunks = split_documents(docs)
                
                if not chunks:
                    st.error("❌ No text extracted. Please check your files.")
                else:
                    save_to_chroma(chunks)
                    st.success(f"✅ Processed {len(chunks)} chunks!")
        else:
            st.warning("Upload files first.")

# --- MAIN CHAT ---

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Analyzing documents..."):
            # No mode parameter needed anymore
            response_text, sources = query_rag(prompt)
            
            full_response = response_text
            if sources:
                unique_sources = list(set(sources))
                full_response += f"\n\n**Sources:** {', '.join(unique_sources)}"
            
            st.markdown(full_response)
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})