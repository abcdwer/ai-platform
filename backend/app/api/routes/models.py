"""Models API routes."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas.model_config import (
    ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse, ModelListResponse,
    ModelInfo, AvailableModelsResponse
)
from app.services.model_dispatcher import get_model_dispatcher, ModelInfo as DispatcherModelInfo

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("", response_model=AvailableModelsResponse)
async def list_available_models():
    """List all available models from all configured providers."""
    dispatcher = get_model_dispatcher()
    models_by_provider = await dispatcher.list_all_models()
    
    all_models = []
    ollama_models = []
    openai_models = []
    
    for provider, models in models_by_provider.items():
        model_infos = [
            ModelInfo(
                id=m.id,
                name=m.name,
                provider=m.provider,
                model_id=m.id,
                is_default=(provider == "ollama" and m.id == "llama2"),
                supports_streaming=m.supports_streaming,
                supports_function_calling=m.supports_function_calling
            )
            for m in models
        ]
        all_models.extend(model_infos)
        
        if provider == "ollama":
            ollama_models = model_infos
        elif provider == "openai":
            openai_models = model_infos
    
    return AvailableModelsResponse(
        ollama=ollama_models,
        openai=openai_models,
        all=all_models
    )


@router.get("/health")
async def check_all_providers_health():
    """Check health of all model providers."""
    dispatcher = get_model_dispatcher()
    health_status = await dispatcher.health_check_all()
    
    # Determine overall status
    all_online = all(h.get("status") == "online" for h in health_status.values())
    any_online = any(h.get("status") == "online" for h in health_status.values())
    
    if all_online:
        overall_status = "healthy"
    elif any_online:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "providers": health_status
    }


@router.get("/health/{provider}")
async def check_provider_health(provider: str):
    """Check health of a specific provider."""
    dispatcher = get_model_dispatcher()
    
    try:
        status = await dispatcher.get_provider_status(provider)
        return {
            "provider": provider,
            **status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/status")
async def get_models_status():
    """Get status of all model providers with model counts."""
    dispatcher = get_model_dispatcher()
    health_status = await dispatcher.health_check_all()
    models_by_provider = await dispatcher.list_all_models()
    
    result = []
    for provider, health in health_status.items():
        models = models_by_provider.get(provider, [])
        result.append({
            "provider": provider,
            "status": health.get("status", "unknown"),
            "error": health.get("error"),
            "model_count": len(models),
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "supports_streaming": m.supports_streaming,
                    "supports_function_calling": m.supports_function_calling
                }
                for m in models
            ]
        })
    
    return {"providers": result}
