from fastapi import APIRouter, HTTPException

from app.application.dto.runtime_settings_contracts import ProviderInfo, ProviderModelsResponse, ProviderTestRequest, ProviderTestResponse
from app.infrastructure.ai.providers.registry import get_provider, list_providers

router = APIRouter()


@router.get("/settings/providers", response_model=list[ProviderInfo])
async def list_all_providers() -> list[ProviderInfo]:
    return [ProviderInfo(**p) for p in list_providers()]


@router.post("/settings/providers/test", response_model=ProviderTestResponse)
async def test_provider(payload: ProviderTestRequest) -> ProviderTestResponse:
    try:
        provider = get_provider(payload.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not payload.api_key or not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required")

    result = await provider.test_connection(
        api_key=payload.api_key.strip(),
        base_url=payload.base_url,
        model=payload.model,
    )
    return ProviderTestResponse(**result)


@router.post("/settings/providers/models", response_model=ProviderModelsResponse)
async def list_provider_models(payload: ProviderTestRequest) -> ProviderModelsResponse:
    # Reuse same request shape: provider, api_key, base_url
    try:
        provider = get_provider(payload.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not payload.api_key or not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required")

    try:
        models = await provider.list_models(api_key=payload.api_key.strip(), base_url=payload.base_url)
    except Exception as e:
        # Use HTTPException with detail from provider error
        msg = str(e)[:500]
        # If httpx error, try to extract response
        raise HTTPException(status_code=400, detail=f"Failed to list models: {msg}")

    return ProviderModelsResponse(models=models)
