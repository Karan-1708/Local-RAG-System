from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_function():
    """
    Returns the HuggingFace embedding model (all-MiniLM-L6-v2).
    Runs entirely locally.
    """
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'} # Change to 'cuda' if you have an NVIDIA GPU
    )
    
    return embeddings