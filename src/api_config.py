# --- Frontier API Configuration ---

FRONTIER_PROVIDERS = {
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "key_url": "https://platform.openai.com/api-keys",
        "env_key": "OPENAI_API_KEY"
    },
    "Google Gemini": {
        "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "key_url": "https://aistudio.google.com/app/apikey",
        "env_key": "GOOGLE_API_KEY"
    },
    "Anthropic": {
        "models": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "key_url": "https://console.anthropic.com/settings/keys",
        "env_key": "ANTHROPIC_API_KEY"
    }
}
