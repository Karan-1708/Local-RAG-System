import logging

# Suppress Streamlit's ScriptRunContext warning that fires when RAG/RAGAS
# modules are imported outside of a Streamlit session (i.e. from the API server).
# A Filter is used instead of setLevel because Streamlit resets its own loggers
# during initialisation, which would override a simple level change.
class _SuppressScriptRunContext(logging.Filter):
    def filter(self, record):
        return "ScriptRunContext" not in record.getMessage()

logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").addFilter(
    _SuppressScriptRunContext()
)

from fastapi import FastAPI, HTTPException, Body, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
from src.generation import query_rag
from src.utils import log_startup_info
import config

app = FastAPI(
    title="🛡️ Local RAG System API",
    description="Standardized REST API for private technical Q&A. PROGRAMMATIC ACCESS REQUIRES X-API-Key header.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    log_startup_info()

# --- SECURITY ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == config.INTERNAL_API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials. Internal API Key is incorrect."
    )

class QueryRequest(BaseModel):
    query_text: str
    provider: str = "Ollama"
    model_name: str = config.LLM_MODEL
    api_key: Optional[str] = None
    enable_deep_eval: bool = False

class Citation(BaseModel):
    source: str
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    metrics: str
    citations: List[Citation]

@app.post("/api/v1/query", response_model=QueryResponse, tags=["RAG"], dependencies=[Security(get_api_key)])
async def run_query(request: QueryRequest = Body(...)):
    """
    Executes a RAG query through the pipeline. REQUIRES X-API-Key header.
    
    - **query_text**: Your technical question.
    - **provider**: Ollama, OpenAI, Google Gemini, or Anthropic.
    - **model_name**: The specific model ID (e.g., llama3, gpt-4o).
    - **api_key**: Required for cloud providers.
    - **enable_deep_eval**: If true, runs RAGAS scoring.
    """
    try:
        # Since query_rag is a generator, we collect all results
        full_answer = ""
        metrics = ""
        citations = []
        
        # Execute generator
        for chunk in query_rag(
            request.query_text,
            enable_deep_eval=request.enable_deep_eval,
            provider=request.provider,
            selected_model=request.model_name,
            api_key=request.api_key
        ):
            if isinstance(chunk, str):
                full_answer += chunk
            elif isinstance(chunk, dict) and chunk.get("type") == "metadata":
                metrics = chunk.get("metrics", "")
                citations = [Citation(**c) for c in chunk.get("citations", [])]
        
        if not full_answer:
            raise HTTPException(status_code=500, detail="Generation failed to return content.")

        return QueryResponse(
            answer=full_answer,
            metrics=metrics,
            citations=citations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
async def health_check():
    """Returns the status of the API server. Public access."""
    return {"status": "online", "system": "Local RAG"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
