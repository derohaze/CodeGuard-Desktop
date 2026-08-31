from app.infrastructure.ai.providers.openai.client import OpenAIProvider


class NvidiaProvider(OpenAIProvider):
    id = "nvidia"
    name = "NVIDIA"
    default_base_url = "https://integrate.api.nvidia.com/v1"
    docs_url = "https://docs.api.nvidia.com"
