import torch
import math
from transformers import AutoModelForCausalLM, AutoTokenizer

# We use a small, fast model just for scoring (not for generating answers)
EVAL_MODEL_NAME = "distilgpt2" 

class Evaluator:
    def __init__(self):
        print(f"Loading evaluation model ({EVAL_MODEL_NAME})...")
        self.tokenizer = AutoTokenizer.from_pretrained(EVAL_MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(EVAL_MODEL_NAME)
        self.model.eval() # Set to evaluation mode

    def calculate_perplexity(self, text: str) -> float:
        """
        Calculates the perplexity of a text.
        Lower is better. 
        < 20 = Very Fluent
        > 100 = Confused/Garbage
        """
        if not text or len(text.strip()) == 0:
            return 0.0

        encodings = self.tokenizer(text, return_tensors="pt")
        input_ids = encodings.input_ids
        
        with torch.no_grad():
            outputs = self.model(input_ids, labels=input_ids)
            loss = outputs.loss
            perplexity = torch.exp(loss)
            
        return perplexity.item()

    def is_ambiguous(self, retrieval_scores: list, threshold: float = 0.6) -> bool:
        """
        Checks if the retrieved documents are relevant enough.
        ChromaDB (L2 Distance): Lower is better. 0 = Identical match.
        
        If the BEST match has a distance > threshold, the database 
        didn't find anything relevant.
        """
        if not retrieval_scores:
            return True # No results = Ambiguous
            
        best_score = retrieval_scores[0] # Assumes sorted list (closest first)
        
        # If the distance is huge (e.g. > 1.0), it's likely random noise
        # You may need to tune this threshold based on your data!
        is_bad_match = best_score > threshold
        
        if is_bad_match:
            print(f"Ambiguity Alert: Best match score was {best_score} (Threshold: {threshold})")
            
        return is_bad_match

# --- Singleton Instance ---
# We create one instance to reuse, so we don't reload the model every query
evaluator = Evaluator()