"""Model configuration schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ModelConfigBase(BaseModel):
    """Base model configuration schema."""
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    model_id: str = Field(..., min_length=1, max_length=100)
    api_base: Optional[str] = Field(None, max_length=500)
    supports_streaming: bool = Field(default=True)
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    default_temperature: float = Field(default=0.7, ge=0, le=2)
    default_max_tokens: int = Field(default=4096, ge=1)
    default_top_p: float = Field(default=0.9, ge=0, le=1)
    max_context_tokens: int = Field(default=4096, ge=1)


class ModelConfigCreate(ModelConfigBase):
    """Schema for creating model configuration."""
    api_key: Optional[str] = None


class ModelConfigUpdate(BaseModel):
    """Schema for updating model configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    model_id: Optional[str] = Field(None, min_length=1, max_length=100)
    api_base: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = None
    supports_streaming: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    default_temperature: Optional[float] = Field(None, ge=0, le=2)
    default_max_tokens: Optional[int] = Field(None, ge=1)
    default_top_p: Optional[float] = Field(None, ge=0, le=1)
    max_context_tokens: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    """Schema for model configuration response."""
    id: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @property
    def display_name(self) -> str:
        """Get display name for the model."""
        return f"{self.provider.title()}/{self.model_id}"


class ModelListResponse(BaseModel):
    """Schema for model list response."""
    items: list[ModelConfigResponse]
    total: int


class ModelInfo(BaseModel):
    """Simplified model info for quick listing."""
    id: str
    name: str
    provider: str
    model_id: str
    is_default: bool = False
    supports_streaming: bool = True
    supports_function_calling: bool = False


class AvailableModelsResponse(BaseModel):
    """Response for available models from all providers."""
    ollama: list[ModelInfo]
    openai: list[ModelInfo]
    all: list[ModelInfo]
