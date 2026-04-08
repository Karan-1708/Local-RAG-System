from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from src.utils import logger

# Initialize engines as global singletons to avoid repeated loading
try:
    logger.info("Initializing Microsoft Presidio engines...")
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
except Exception as e:
    logger.error(f"❌ Failed to initialize Presidio engines: {e}")
    analyzer = None
    anonymizer = None

def redact_text(text: str) -> str:
    """
    Detects and redacts PII (Personally Identifiable Information) from the given text.
    Entities include: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION, etc.
    """
    if not text or not analyzer or not anonymizer:
        return text

    try:
        # 1. Analyze text for PII entities
        # We specify common entities, or leave it empty to use all defaults
        results = analyzer.analyze(
            text=text, 
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "IP_ADDRESS"],
            language='en'
        )

        # 2. Anonymize the detected entities
        anonymized_result = anonymizer.anonymize(
            text=text,
            analyzer_results=results
        )

        return anonymized_result.text

    except Exception as e:
        logger.error(f"PII Redaction failed: {e}")
        # Fail-open: return original text to avoid system crash, 
        # but log the failure for security auditing.
        return text

if __name__ == "__main__":
    # Test block
    test_text = "My name is John Doe, my email is john.doe@example.com and I live in New York."
    print(f"Original: {test_text}")
    print(f"Redacted: {redact_text(test_text)}")
