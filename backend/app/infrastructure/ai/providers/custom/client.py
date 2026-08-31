from app.infrastructure.ai.providers.openai.client import OpenAIProvider


class CustomProvider(OpenAIProvider):
    id = "custom"
    name = "Custom (OpenAI-compatible)"
    default_base_url = None
    docs_url = None

    def resolve_base_url(self, base_url: str | None) -> str:
        if not base_url:
            raise ValueError("Custom provider requires base_url")
        return base_url.rstrip("/")
