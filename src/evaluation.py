import torch
import math
import os
import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_ollama import ChatOllama
from src.embeddings import get_embedding_function
from ragas.metrics import Faithfulness, AnswerRelevancy
from ragas import evaluate
from datasets import Dataset
from src.utils import logger, get_device
import config

# We use a small, fast model just for scoring (not for generating answers)
EVAL_MODEL_NAME = "distilgpt2" 

class Evaluator:
    def __init__(self):
        try:
            is_offline = os.getenv("HF_HUB_OFFLINE", "0") == "1"
            device = get_device()
            logger.info(f"Loading evaluation model ({EVAL_MODEL_NAME}, Device: {device}, Offline: {is_offline})...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                EVAL_MODEL_NAME, 
                local_files_only=is_offline
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                EVAL_MODEL_NAME, 
                local_files_only=is_offline
            ).to(device)
            self.model.eval() # Set to evaluation mode
        except Exception as e:
            logger.error(f"Failed to load evaluation model: {e}")
            self.tokenizer = None
            self.model = None

    def calculate_perplexity(self, text: str) -> float:
        """
        Calculates the perplexity of a text.
        Lower is better. 
        < 20 = Very Fluent
        > 100 = Confused/Garbage
        """
        if not text or len(text.strip()) == 0 or self.model is None:
            return 0.0

        try:
            # Move inputs to the same device as the model
            encodings = self.tokenizer(text, return_tensors="pt").to(self.model.device)
            input_ids = encodings.input_ids
            
            with torch.no_grad():
                outputs = self.model(input_ids, labels=input_ids)
                loss = outputs.loss
                perplexity = torch.exp(loss)
                
            return float(perplexity.item())
        except Exception as e:
            logger.warning(f"Perplexity calculation failed: {e}")
            return 0.0

    def calculate_ragas(self, question: str, answer: str, contexts: list[str], provider: str = "Ollama", model_name: str = None, api_key: str = None) -> dict:
        """
        Calculates local or cloud RAGAS metrics (Faithfulness, Answer Relevancy).
        Uses the same provider/model as the generation phase.
        """
        try:
            logger.info(f"Initializing RAGAS evaluation using {provider}...")
            
            # 1. Setup LLM based on provider
            if provider == "Ollama":
                eval_llm = ChatOllama(model=model_name or config.LLM_MODEL)
            elif provider == "OpenAI":
                from langchain_openai import ChatOpenAI
                eval_llm = ChatOpenAI(model=model_name, api_key=api_key)
            elif provider == "Google Gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                eval_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
            elif provider == "Anthropic":
                from langchain_anthropic import ChatAnthropic
                eval_llm = ChatAnthropic(model_name=model_name, api_key=api_key)
            else:
                eval_llm = ChatOllama(model=config.LLM_MODEL)

            local_embeddings = get_embedding_function()
            
            # 2. Prepare Data
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts]
            }
            dataset = Dataset.from_dict(data)
            
            # 3. Setup Metrics
            metrics = [
                Faithfulness(),
                AnswerRelevancy()
            ]
            
            # 4. Run Evaluation
            logger.info("Computing RAGAS metrics...")
            result = evaluate(
                dataset,
                metrics=metrics,
                llm=eval_llm,
                embeddings=local_embeddings
            )
            
            return result.to_pandas().to_dict('records')[0]
            
        except Exception as e:
            logger.error(f"❌ RAGAS evaluation failed: {e}")
            return {}

    def is_ambiguous(self, retrieval_scores: list, threshold: float = None) -> bool:
        """
        Checks if the retrieved documents are relevant enough.
        """
        limit = threshold or config.SIMILARITY_THRESHOLD
        
        if not retrieval_scores:
            return True # No results = Ambiguous
            
        best_score = retrieval_scores[0] # Assumes sorted list (closest first)
        
        is_bad_match = best_score > limit
        
        if is_bad_match:
            logger.info(f"Ambiguity Alert: Best match score was {best_score} (Limit: {limit})")
            
        return is_bad_match

@st.cache_resource
def get_evaluator():
    """Returns a cached instance of the Evaluator."""
    return Evaluator()

# --- Cached Instance ---
evaluator = get_evaluator()
