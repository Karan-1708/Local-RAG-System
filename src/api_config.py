# --- Frontier API Configuration ---

FRONTIER_PROVIDERS = {
    "OpenAI": {
        "models": ["gpt-5.4-nano", "gpt-5-nano", "o4-mini", "gpt-4o-mini"],
        "key_url": "https://platform.openai.com/api-keys",
        "env_key": "OPENAI_API_KEY"
    },
    "Google Gemini": {
        "models": ["gemini-3-flash-preview", "gemini-3.1-flash-lite-preview", "gemini-2.5-flash-lite"],
        "key_url": "https://aistudio.google.com/app/apikey",
        "env_key": "GOOGLE_API_KEY"
    },
    "Anthropic": {
        "models": ["claude-sonnet-4-6","claude-haiku-4-5", "claude-sonnet-4-5", "claude-sonnet-4-0"],
        "key_url": "https://console.anthropic.com/settings/keys",
        "env_key": "ANTHROPIC_API_KEY"
    }
}
