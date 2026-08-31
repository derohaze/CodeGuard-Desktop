from app.infrastructure.ai.providers.openai.client import OpenAIProvider


class GrokProvider(OpenAIProvider):
    id = "grok"
    name = "Grok (xAI)"
    default_base_url = "https://api.x.ai/v1"
    docs_url = "https://docs.x.ai"
