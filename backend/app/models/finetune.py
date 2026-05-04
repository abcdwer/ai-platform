"""Finetune models for LoRA/QLoRA fine-tuning."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Boolean, Text, JSON, Integer, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Dataset(Base):
    """Dataset model for fine-tuning data."""
    
    __tablename__ = "datasets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # File information
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)  # jsonl, parquet, csv
    
    # Format type
    format_type: Mapped[str] = mapped_column(String(50), nullable=False, default="conversation")  # conversation, sharegpt, alpaca
    
    # Statistics
    total_samples: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_turns: Mapped[float] = mapped_column(Float, default=0.0)  # Average conversation turns
    
    # Validation
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Split ratios
    train_ratio: Mapped[float] = mapped_column(Float, default=0.9)
    validation_ratio: Mapped[float] = mapped_column(Float, default=0.1)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="datasets")
    finetune_jobs: Mapped[list["FinetuneJob"]] = relationship("FinetuneJob", back_populates="dataset")
    
    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, samples={self.total_samples})>"
    
    def get_sample_preview(self, limit: int = 5) -> dict:
        """Get preview of dataset samples."""
        return {
            "total_samples": self.total_samples,
            "total_tokens": self.total_tokens,
            "avg_turns": self.avg_turns,
            "format": self.format_type,
            "validated": self.is_validated,
        }


class FinetuneJob(Base):
    """Fine-tuning job model."""
    
    __tablename__ = "finetune_jobs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Job configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Base model
    base_model: Mapped[str] = mapped_column(String(255), nullable=False)
    base_model_type: Mapped[str] = mapped_column(String(50), nullable=False, default="causal_lm")  # causal_lm, seq2seq
    
    # Training configuration (stored as JSON)
    training_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # LoRA configuration
    lora_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, queued, running, paused, completed, failed, cancelled
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    
    # Progress metrics
    current_epoch: Mapped[float] = mapped_column(Float, default=0.0)
    total_epochs: Mapped[int] = mapped_column(Integer, default=3)
    
    # Metrics
    current_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    best_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    learning_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Metrics history (for charts)
    metrics_history: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_time_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resource usage
    gpu_memory_used: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # bytes
    gpu_utilization: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="finetune_jobs")
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="finetune_jobs")
    finetuned_model: Mapped[Optional["FinetuneModel"]] = relationship("FinetuneModel", back_populates="job", uselist=False)
    
    def __repr__(self) -> str:
        return f"<FinetuneJob(id={self.id}, name={self.name}, status={self.status})>"
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100
    
    def get_training_time(self) -> Optional[int]:
        """Get training time in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((datetime.utcnow() - self.started_at).total_seconds())
        return None


class FinetuneModel(Base):
    """Fine-tuned model output."""
    
    __tablename__ = "finetune_models"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    
    # Model information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Model paths
    base_model: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    merged_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Model metrics
    final_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_perplexity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_parameters: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    trainable_parameters: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Model config
    model_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Deployment status
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    deployment_endpoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    deployment_status: Mapped[str] = mapped_column(String(50), default="not_deployed")
    
    # Metadata
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    model_type: Mapped[str] = mapped_column(String(50), default="lora")  # lora, qlora, full
    quantization: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 4bit, 8bit, none
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="finetune_models")
    job: Mapped["FinetuneJob"] = relationship("FinetuneJob", back_populates="finetuned_model")
    
    def __repr__(self) -> str:
        return f"<FinetuneModel(id={self.id}, name={self.name}, deployed={self.is_deployed})>"
    
    def get_model_size_mb(self) -> Optional[float]:
        """Get model size in MB."""
        if self.file_size:
            return self.file_size / (1024 * 1024)
        return None
