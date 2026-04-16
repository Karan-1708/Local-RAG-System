import torch
import math
import os
import logging
import streamlit as st
from typing import List
from transformers import AutoModelForCausalLM, AutoTokenizer

# Suppress the "loss_type=None is unrecognized" noise from older model configs
# (e.g. distilgpt2) when loaded with newer versions of transformers.
class _SuppressLossTypeWarning(logging.Filter):
    def filter(self, record):
        return "loss_type" not in record.getMessage()

logging.getLogger("transformers.modeling_utils").addFilter(_SuppressLossTypeWarning())

from langchain_ollama import ChatOllama
from src.embeddings import get_embedding_function
from ragas.metrics import Faithfulness, AnswerRelevancy
from ragas import evaluate
from datasets import Dataset
from src.utils import logger, get_device
import config

# gpt2 is used instead of distilgpt2 for two reasons:
#   1. It scores technical/domain text more accurately (distilgpt2's compression
#      degrades calibration on out-of-distribution vocabulary).
#   2. It provides a proper 1024-token context window with no silent truncation
#      — long answers are handled via the stride-based calculation below.
EVAL_MODEL_NAME = "gpt2"

# ---------------------------------------------------------------------------
# Fast evaluation model map
# When RAGAS runs, it makes 6-10 LLM calls per metric. Using the same large
# model that generated the answer (e.g. GPT-4o, Gemini 1.5 Pro) makes
# evaluation very slow and expensive. These mappings swap to the fastest
# available variant for each provider while keeping the same vendor so that
# scoring style remains consistent.
# ---------------------------------------------------------------------------
_FAST_EVAL_MODELS = {
    "OpenAI": {
        # Fastest / cheapest model in the lineup for evaluation calls
        "default":          "gpt-4o-mini",
        "gpt-5.4-nano":     "gpt-4o-mini",
        "gpt-5-nano":       "gpt-4o-mini",
        "o4-mini":          "gpt-4o-mini",
        "gpt-4o-mini":      "gpt-4o-mini",
    },
    "Google Gemini": {
        "default":                          "gemini-2.5-flash-lite",
        "gemini-3-flash-preview":           "gemini-2.5-flash-lite",
        "gemini-3.1-flash-lite-preview":    "gemini-2.5-flash-lite",
        "gemini-2.5-flash-lite":            "gemini-2.5-flash-lite",
    },
    "Anthropic": {
        "default":              "claude-haiku-4-5",
        "claude-sonnet-4-6":    "claude-haiku-4-5",
        "claude-haiku-4-5":     "claude-haiku-4-5",
        "claude-sonnet-4-5":    "claude-haiku-4-5",
        "claude-sonnet-4-0":    "claude-haiku-4-5",
    },
}

# Maximum number of context chunks passed to RAGAS.
# Passing all retrieved chunks inflates token usage; top-3 is sufficient
# for faithfulness and relevancy scoring.
_RAGAS_MAX_CONTEXT_CHUNKS = 3


def _get_fast_eval_model(provider: str, model_name: str) -> str:
    """Returns the fastest available evaluation model for the given provider."""
    provider_map = _FAST_EVAL_MODELS.get(provider, {})
    return provider_map.get(model_name, provider_map.get("default", model_name))


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
            self.model.eval()
        except Exception as e:
            logger.error(f"Failed to load evaluation model: {e}")
            self.tokenizer = None
            self.model = None

    def calculate_perplexity(self, text: str) -> float:
        """
        Calculates perplexity using a stride-based sliding window over the
        full token sequence.  This avoids silently truncating long answers
        (gpt2 has a 1024-token context) and gives an accurate score for
        responses of any length by averaging NLL across overlapping windows.

        Scale (gpt2, technical content):
          <= 30   Excellent — very fluent and coherent
          <= 80   Good      — clear and readable
          <= 160  Okay      — minor awkwardness
          >  160  Confused  — likely off-topic or garbled
        """
        if not text or len(text.strip()) == 0 or self.model is None:
            return 0.0
        try:
            max_length = self.model.config.n_positions  # 1024 for gpt2
            stride = max_length // 2                    # 512 — 50% overlap

            encodings = self.tokenizer(text, return_tensors="pt")
            seq_len = encodings.input_ids.size(1)

            nlls = []
            prev_end = 0
            for begin in range(0, seq_len, stride):
                end = min(begin + max_length, seq_len)
                target_len = end - prev_end

                input_ids = encodings.input_ids[:, begin:end].to(self.model.device)
                target_ids = input_ids.clone()
                # Mask the overlapping prefix so it doesn't skew the loss
                target_ids[:, :-target_len] = -100

                with torch.no_grad():
                    outputs = self.model(input_ids, labels=target_ids)
                    nlls.append(outputs.loss)

                prev_end = end
                if end == seq_len:
                    break

            return float(torch.exp(torch.stack(nlls).mean()).item())
        except Exception as e:
            logger.warning(f"Perplexity calculation failed: {e}")
            return 0.0

    def calculate_ragas(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        provider: str = "Ollama",
        model_name: str = None,
        api_key: str = None
    ) -> dict:
        """
        Computes RAGAS Faithfulness and AnswerRelevancy.

        Speed optimisations applied here:
        - Uses a fast/cheap model variant (e.g. gpt-4o-mini instead of gpt-4o)
          to reduce per-call latency by 3-5x.
        - Caps context at _RAGAS_MAX_CONTEXT_CHUNKS chunks to reduce token count.
        - Passes raise_exceptions=False so RAGAS immediately returns NaN for any
          metric whose LLM call fails, instead of retrying multiple times.
        """
        try:
            # Select the fastest available evaluation model for this provider
            eval_model = _get_fast_eval_model(provider, model_name or "")
            logger.info(f"RAGAS evaluation using {provider} / {eval_model} (fast eval model)...")

            # Build the eval LLM
            if provider == "Ollama":
                eval_llm = ChatOllama(model=model_name or config.LLM_MODEL)
            elif provider == "OpenAI":
                from langchain_openai import ChatOpenAI
                eval_llm = ChatOpenAI(model=eval_model, api_key=api_key)
            elif provider == "Google Gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                eval_llm = ChatGoogleGenerativeAI(model=eval_model, google_api_key=api_key)
            elif provider == "Anthropic":
                from langchain_anthropic import ChatAnthropic
                eval_llm = ChatAnthropic(model_name=eval_model, api_key=api_key)
            else:
                eval_llm = ChatOllama(model=config.LLM_MODEL)

            local_embeddings = get_embedding_function()

            # Cap context chunks to reduce LLM token usage
            trimmed_contexts = contexts[:_RAGAS_MAX_CONTEXT_CHUNKS]

            data = {
                "question": [question],
                "answer":   [answer],
                "contexts": [trimmed_contexts],
            }
            dataset = Dataset.from_dict(data)

            # RAGAS 0.2+ requires LLM and embeddings injected directly into each
            # metric via wrapper classes. Without this, AnswerRelevancy cannot
            # access embeddings and silently returns NaN.
            # Fall back to the legacy evaluate() kwargs for RAGAS 0.1.x.
            try:
                from ragas.llms import LangchainLLMWrapper
                from ragas.embeddings import LangchainEmbeddingsWrapper
                wrapped_llm = LangchainLLMWrapper(eval_llm)
                wrapped_emb = LangchainEmbeddingsWrapper(local_embeddings)
                metrics = [
                    Faithfulness(llm=wrapped_llm),
                    AnswerRelevancy(llm=wrapped_llm, embeddings=wrapped_emb),
                ]
                use_wrappers = True
            except ImportError:
                metrics = [Faithfulness(), AnswerRelevancy()]
                use_wrappers = False

            # RunConfig adds per-metric retries so a single bad LLM response
            # doesn't immediately produce NaN — RAGAS retries up to max_retries
            # times before giving up.
            try:
                from ragas import RunConfig
                run_config = RunConfig(max_retries=3, max_wait=90, timeout=60)
            except (ImportError, TypeError):
                run_config = None

            # Run each metric independently so a failure in one does not null
            # out the other. Results are merged into a single dict at the end.
            logger.info("Computing RAGAS metrics (independent, raise_exceptions=False)...")
            combined = {}
            for metric in metrics:
                try:
                    eval_kwargs = {"metrics": [metric], "raise_exceptions": False}
                    if not use_wrappers:
                        eval_kwargs["llm"] = eval_llm
                        eval_kwargs["embeddings"] = local_embeddings
                    if run_config is not None:
                        eval_kwargs["run_config"] = run_config
                    r = evaluate(dataset, **eval_kwargs)
                    combined.update(r.to_pandas().to_dict('records')[0])
                except Exception as e:
                    logger.warning(f"RAGAS {metric.__class__.__name__} failed: {e}")

            return combined

        except Exception as e:
            logger.error(f"❌ RAGAS evaluation failed: {e}")
            return {}


@st.cache_resource
def get_evaluator():
    """Returns a cached instance of the Evaluator."""
    return Evaluator()

evaluator = get_evaluator()
