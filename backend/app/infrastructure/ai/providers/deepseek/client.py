from app.infrastructure.ai.providers.openai.client import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    id = "deepseek"
    name = "DeepSeek"
    default_base_url = "https://api.deepseek.com/v1"
    docs_url = "https://api-docs.deepseek.com"
