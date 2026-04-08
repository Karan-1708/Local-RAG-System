import ollama
import config
from src.utils import logger
from typing import List, Generator, Dict

def get_local_models() -> List[str]:
    """
    Fetches the list of models currently available in the local Ollama instance.
    Returns a list of model names (strings).
    """
    try:
        response = ollama.list()
        
        # Handle different response formats (object vs list)
        if hasattr(response, 'models'):
            model_objects = response.models
        elif isinstance(response, dict) and 'models' in response:
            model_objects = response['models']
        else:
            model_objects = response # Assume it's already a list
            
        # Extract names and strip ':latest' for cleaner UI if preferred
        # But we'll keep the full name to ensure exact matching
        models = []
        for m in model_objects:
            if hasattr(m, 'model'):
                models.append(m.model)
            elif isinstance(m, dict) and 'name' in m:
                models.append(m['name'])
            elif isinstance(m, dict) and 'model' in m:
                models.append(m['model'])
                
        return models if models else [config.LLM_MODEL]
    except Exception as e:
        logger.error(f"Failed to fetch local Ollama models: {e}")
        return [config.LLM_MODEL]

def is_ollama_running() -> bool:
    """Checks if the local Ollama service is reachable."""
    try:
        ollama.list()
        return True
    except Exception:
        return False

def pull_new_model(model_name: str) -> Generator[Dict, None, None]:
    """
    Pull a new model from the Ollama library.
    Yields status updates (dict) during the pull process.
    """
    try:
        logger.info(f"Starting pull for model: {model_name}")
        stream = ollama.pull(model_name, stream=True)
        last_status = None
        for chunk in stream:
            status = chunk.get("status")
            # Only yield if the status has changed or if it has progress data
            if status != last_status or "completed" in chunk:
                yield chunk
                last_status = status
        logger.info(f"Successfully pulled model: {model_name}")
    except Exception as e:
        err_msg = str(e).lower()
        if "404" in err_msg or "not found" in err_msg:
            friendly_err = f"The model '{model_name}' was not found on the Ollama registry. Please check the name at ollama.com/library."
        else:
            friendly_err = f"Error pulling model: {str(e)}"
        
        logger.error(f"Error pulling model {model_name}: {friendly_err}")
        yield {"status": "error", "message": friendly_err}
