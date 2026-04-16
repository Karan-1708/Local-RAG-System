import re
import math
import logging
import functools
from typing import List, Tuple, Optional, Dict, Generator, Any
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from src.embeddings import get_embedding_function
from src.evaluation import evaluator
from src.retrieval import get_bm25_retriever
from src.privacy import redact_text
from src.utils import logger, get_device
from src.prompts import RAG_SYSTEM_PROMPT
import config

# Global singleton for the re-ranker to avoid multiple loads
@functools.lru_cache(maxsize=1)
def get_reranker():
    logger.info("Loading Re-ranking model (Cross-Encoder)...")
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def get_llm(provider: str, model_name: str, api_key: str = None):
    """
    Factory function to initialize the requested LLM provider with friendly error messages.
    """
    try:
        if provider == "Ollama":
            return ChatOllama(
                model=model_name, 
                temperature=0.2, 
                num_ctx=8192,
                num_predict=-1
            )
        
        if provider == "OpenAI":
            if not api_key:
                raise ValueError("OpenAI API Key is missing.")
            return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.2)
        
        if provider == "Google Gemini":
            if not api_key:
                raise ValueError("Google API Key is missing.")
            return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)
        
        if provider == "Anthropic":
            if not api_key:
                raise ValueError("Anthropic API Key is missing.")
            return ChatAnthropic(model_name=model_name, api_key=api_key, temperature=0.2)
            
        raise ValueError(f"Unsupported provider: {provider}")
        
    except Exception as e:
        error_msg = str(e).lower()
        if "api_key" in error_msg or "invalid_api_key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
            raise ValueError(f"The API key provided for {provider} is incorrect or invalid. Please check your key and try again.")
        if "model_not_found" in error_msg or "model not found" in error_msg or "not found" in error_msg:
            raise ValueError(f"The model '{model_name}' does not exist or you do not have access to it on {provider}.")
        if "deprecated" in error_msg:
            raise ValueError(f"The model '{model_name}' has been deprecated by {provider}. Please select a newer version.")
        
        logger.error(f"Failed to initialize {provider}: {e}")
        raise e

def reciprocal_rank_fusion(vector_results: List[Document], bm25_results: List[Document], k: int = 60) -> List[Document]:
    """
    Combines vector and BM25 results using Reciprocal Rank Fusion.
    score(d) = sum(1 / (k + rank(d)))
    """
    fused_scores: Dict[str, float] = {}
    doc_lookup: Dict[str, Document] = {}

    # Helper to process a ranked list
    def process_results(results: List[Document]):
        for rank, doc in enumerate(results, start=1):
            # We use content and source as a unique key for the chunk
            doc_id = f"{doc.page_content}_{doc.metadata.get('source', '')}_{doc.metadata.get('page', '')}"
            
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0.0
                doc_lookup[doc_id] = doc
            
            fused_scores[doc_id] += 1.0 / (k + rank)

    process_results(vector_results)
    process_results(bm25_results)

    # Sort documents by their RRF score in descending order
    sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
    
    return [doc_lookup[did] for did in sorted_ids]

def contains_injection(text: str) -> bool:
    """
    Scans a document chunk for sophisticated prompt injection patterns.
    """
    patterns = [
        r"(ignore|disregard|skip|overwrite)\s+(all\s+)?(previous|existing|system)\s+(instructions|prompts|rules)",
        r"system\s+(override|notice|reset)",
        r"(become|act\s+as)\s+(now\s+)?(a|the)\s+",
        r"administrative\s+session",
        r"(reply|answer|respond)\s+only\s+as\s+",
        r"jailbreak",
        r"developer\s+mode\s+enabled",
        r"\[(system|admin)\]\s*:",
        r"print\s+the\s+system\s+prompt",
        r"reveal\s+your\s+(instructions|system\s+prompt)",
        r"===\s+IMPORTANT\s+UPDATE\s+===",
        r"<instruction>",
        r"\[INTERNAL\s+MEMO\]"
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"🚨 SECURITY QUARANTINE: Blocked chunk matching pattern '{pattern}'")
            return True
    return False

def query_rag(
    query_text: str,
    chat_id: str = None,
    enable_deep_eval: bool = False,
    provider: str = "Ollama",
    selected_model: str = config.LLM_MODEL,
    api_key: str = None,
    chat_history: Optional[List[Tuple[str, str]]] = None
) -> Generator[Any, None, None]:
    """
    Executes the RAG pipeline as a streaming generator with conversational memory.
    Each chat_id has its own isolated ChromaDB collection and BM25 corpus.
    """
    if chat_history is None:
        chat_history = []

    if not query_text or not query_text.strip():
        yield "⚠️ Please enter a question."
        return

    try:
        # 1. 🛡️ PII REDACTION (User Prompt)
        logger.info("Scrubbing user prompt for PII...")
        safe_query_text = redact_text(query_text)
        if safe_query_text != query_text:
            logger.info("Privacy filter altered the user prompt to protect PII.")

        # 2. Prepare per-chat DB
        embedding_function = get_embedding_function()
        if not config.DB_DIR.exists():
            yield "📂 No documents uploaded yet. Please upload files to get started."
            return

        collection_name = f"chat_{chat_id.replace('-', '_')}" if chat_id else "default"
        db = Chroma(
            persist_directory=str(config.DB_DIR),
            embedding_function=embedding_function,
            collection_name=collection_name
        )

        # Check if this chat has any indexed documents
        existing = db.get(limit=1)
        if not existing.get('ids'):
            yield "📂 No documents uploaded in this chat yet. Upload files using the section below to get started."
            return

        # 3. HYBRID RETRIEVAL (Vector + BM25)
        logger.info(f"Retrieving chunks for: {safe_query_text[:50]}...")
        
        # 3a. Vector Retrieval
        vector_results_with_scores = db.similarity_search_with_score(safe_query_text, k=config.RETRIEVAL_K * 2)
        vector_results = [doc for doc, _score in vector_results_with_scores]
        
        # 3b. Keyword Retrieval (BM25)
        bm25_retriever = get_bm25_retriever(chat_id=chat_id, k=config.RETRIEVAL_K * 2)
        bm25_results = []
        if bm25_retriever:
            try:
                bm25_results = bm25_retriever.invoke(safe_query_text)
            except AttributeError:
                bm25_results = bm25_retriever.get_relevant_documents(safe_query_text)
        
        # 3c. Fusion (RRF)
        fused_results = reciprocal_rank_fusion(vector_results, bm25_results)
        
        if not fused_results:
            logger.info("No documents found in any retriever.")
            yield "No relevant documents found."
            return

        # 4. Re-Ranking (Cross-Encoder)
        reranker = get_reranker()
        pairs = [[safe_query_text, doc.page_content] for doc in fused_results]
        rerank_scores = reranker.predict(pairs)
        
        ranked_results = []
        for i in range(len(fused_results)):
            ranked_results.append((fused_results[i], rerank_scores[i]))
        
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        
        # 5. 🚨 Quarantine Loop 🚨
        safe_docs = []
        logger.info("Quarantining chunks for security...")
        for doc, score in ranked_results:
            if contains_injection(doc.page_content):
                continue 
            
            safe_docs.append(doc)
            if len(safe_docs) >= config.RETRIEVAL_K:
                break
                
        if not safe_docs:
            logger.error("All retrieved chunks were blocked by security quarantine.")
            yield "🚫 SECURITY BLOCK: Retrieved documents flagged as potentially malicious."
            return

        # 6. Context Preparation
        final_context = "\n\n".join([doc.page_content for doc in safe_docs])

        # 7. LLM Generation (Streaming)
        logger.info(f"Generating streaming answer with {provider} model {selected_model}...")
        
        # Convert history tuples to format LLM expects
        formatted_history = ""
        for role, content in chat_history[-5:]: # Keep last 5 exchanges for context
            formatted_history += f"\n{role.upper()}: {content}"

        prompt_template = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)
        prompt = prompt_template.format(
            context=final_context, 
            question=safe_query_text,
            chat_history=formatted_history
        )

        try:
            model = get_llm(provider, selected_model, api_key)
        except ValueError as ve:
            yield f"⚠️ Configuration Error: {str(ve)}"
            return
        except Exception as e:
            yield f"❌ Failed to connect to {provider}: {str(e)}"
            return
        
        full_answer = ""
        try:
            # STREAMING GENERATOR Logic
            for chunk in model.stream(prompt):
                # Normalize chunk content across providers:
                #   Ollama / OpenAI / Anthropic → chunk.content is a str
                #   Google Gemini              → chunk.content is a list of
                #                                content-part dicts, e.g.
                #                                [{'type': 'text', 'text': '…'}]
                content = getattr(chunk, 'content', '')
                if isinstance(content, list):
                    content = "".join(
                        part.get('text', '') if isinstance(part, dict) else str(part)
                        for part in content
                    )
                elif not isinstance(content, str):
                    content = str(content)
                if not content:
                    continue
                full_answer += content
                yield content
        except Exception as e:
            logger.error(f"{provider} streaming failed: {e}")
            yield f"❌ Error communicating with {provider}: {str(e)}"
            return

        # 8. Post-Processing & Evaluation
        ppl_score = evaluator.calculate_perplexity(full_answer)
        
        # Qualify Perplexity (calibrated for gpt2 on technical content)
        ppl_label = "Confused"
        if ppl_score <= 30:   ppl_label = "Excellent"
        elif ppl_score <= 80: ppl_label = "Good"
        elif ppl_score <= 160: ppl_label = "Okay"
        
        # Rich Visual Citations
        citation_data = [
            {
                "source": doc.metadata.get("source", "Unknown"),
                "snippet": doc.page_content[:250] + "..."
            } 
            for doc in safe_docs
        ]
        
        # Deep Evaluation (Optional RAGAS)
        metrics_string = ""
        if ppl_score > 0:
            metrics_string = f"📊 **Perplexity ({ppl_label}):** {ppl_score:.2f}"
        
        if enable_deep_eval:
            logger.info("Running RAGAS evaluation...")
            context_strings = [doc.page_content for doc in safe_docs]
            metrics = evaluator.calculate_ragas(
                safe_query_text, 
                full_answer, 
                context_strings,
                provider=provider,
                model_name=selected_model,
                api_key=api_key
            )
            if metrics:
                # Some providers (e.g. Gemini) cause RAGAS output-parser failures
                # for individual metrics, which RAGAS handles internally by setting
                # that metric to NaN.  Guard here so we never display "nan".
                def _safe(key):
                    val = metrics.get(key)
                    if val is None or (isinstance(val, float) and math.isnan(val)):
                        logger.warning(f"RAGAS metric '{key}' could not be computed (NaN) — skipping display.")
                        return None
                    return max(0.0, float(val))

                faith = _safe('faithfulness')
                relev = _safe('answer_relevancy')

                parts = []
                if faith is not None:
                    parts.append(f"🎯 **Faithfulness:** {faith:.2f}")
                if relev is not None:
                    parts.append(f"🎯 **Relevancy:** {relev:.2f}")
                if parts:
                    if metrics_string:
                        metrics_string += " | "
                    metrics_string += " | ".join(parts)

        # FINAL METADATA YIELD
        yield {
            "type": "metadata",
            "metrics": metrics_string,
            "citations": citation_data
        }

    except Exception as e:
        logger.critical(f"RAG Pipeline Failure: {e}", exc_info=True)
        yield f"❌ An internal error occurred: {str(e)}"
