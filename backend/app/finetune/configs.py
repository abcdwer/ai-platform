"""Training configurations for LoRA/QLoRA fine-tuning."""
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class FinetuneMode(str, Enum):
    """Fine-tuning mode."""
    LORA = "lora"
    QLORA = "qlora"
    FULL = "full"


class QuantizationType(str, Enum):
    """Quantization type for QLoRA."""
    NONE = "none"
    NF4 = "nf4"
    Fp4 = "fp4"
    Fp8 = "fp8"
    Int8 = "int8"


class LoRAConfig(BaseModel):
    """LoRA configuration."""
    # LoRA parameters
    r: int = Field(default=8, ge=1, le=128, description="LoRA attention dimension")
    lora_alpha: int = Field(default=16, ge=1, description="LoRA alpha parameter")
    lora_dropout: float = Field(default=0.05, ge=0.0, le=1.0, description="LoRA dropout probability")
    
    # Target modules (default for common architectures)
    target_modules: Optional[list[str]] = Field(
        default=None,
        description="Target modules for LoRA. If None, auto-detect based on model type."
    )
    
    # Bias settings
    bias: str = Field(default="none", description="Bias type: 'none', 'all', or 'lora_only'")
    
    # Task type
    task_type: str = Field(default="CAUSAL_LM", description="Task type: CAUSAL_LM, SEQ2SEQ_LM, etc.")
    
    def to_peft_config(self) -> dict:
        """Convert to PEFT library config."""
        return {
            "r": self.r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": self.target_modules,
            "bias": self.bias,
            "task_type": self.task_type,
        }


class TrainingConfig(BaseModel):
    """Training configuration."""
    # Basic settings
    num_train_epochs: int = Field(default=3, ge=1, le=100, description="Number of training epochs")
    per_device_train_batch_size: int = Field(default=2, ge=1, le=64, description="Batch size per device")
    per_device_eval_batch_size: int = Field(default=2, ge=1, le=64, description="Batch size for evaluation")
    
    # Learning rate
    learning_rate: float = Field(default=2e-4, ge=1e-6, le=1e-2, description="Initial learning rate")
    weight_decay: float = Field(default=0.01, ge=0.0, le=1.0, description="Weight decay coefficient")
    warmup_ratio: float = Field(default=0.03, ge=0.0, le=1.0, description="Warmup ratio")
    
    # Optimization
    optim: str = Field(default="paged_adamw_8bit", description="Optimizer type")
    lr_scheduler_type: str = Field(default="cosine", description="Learning rate scheduler")
    max_grad_norm: float = Field(default=0.3, ge=0.0, description="Max gradient norm")
    
    # Memory optimization
    gradient_accumulation_steps: int = Field(default=4, ge=1, le=128, description="Gradient accumulation steps")
    
    # Mixed precision
    fp16: bool = Field(default=False, description="Use FP16 mixed precision")
    bf16: bool = Field(default=True, description="Use BF16 mixed precision")
    
    # Evaluation
    eval_strategy: str = Field(default="steps", description="Evaluation strategy: 'no', 'steps', 'epoch'")
    eval_steps: int = Field(default=100, ge=1, description="Evaluation frequency in steps")
    save_strategy: str = Field(default="steps", description="Save strategy: 'no', 'steps', 'epoch'")
    save_steps: int = Field(default=500, ge=1, description="Save frequency in steps")
    save_total_limit: int = Field(default=3, ge=1, description="Max checkpoints to keep")
    
    # Logging
    logging_strategy: str = Field(default="steps", description="Logging strategy")
    logging_steps: int = Field(default=10, ge=1, description="Logging frequency")
    
    # Other
    seed: int = Field(default=42, description="Random seed")
    dataloader_num_workers: int = Field(default=4, ge=0, description="DataLoader workers")
    remove_unused_columns: bool = Field(default=False, description="Remove unused columns")
    label_names: Optional[list[str]] = Field(default=None, description="Label column names")
    
    # Output
    output_dir: str = Field(default="./output", description="Output directory")
    report_to: str = Field(default="none", description="Report to: 'none', 'wandb', 'tensorboard'")
    
    def to_training_args(self) -> dict:
        """Convert to HuggingFace TrainingArguments."""
        return {
            "num_train_epochs": self.num_train_epochs,
            "per_device_train_batch_size": self.per_device_train_batch_size,
            "per_device_eval_batch_size": self.per_device_eval_batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "warmup_ratio": self.warmup_ratio,
            "optim": self.optim,
            "lr_scheduler_type": self.lr_scheduler_type,
            "max_grad_norm": self.max_grad_norm,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "fp16": self.fp16,
            "bf16": self.bf16,
            "eval_strategy": self.eval_strategy,
            "eval_steps": self.eval_steps,
            "save_strategy": self.save_strategy,
            "save_steps": self.save_steps,
            "save_total_limit": self.save_total_limit,
            "logging_strategy": self.logging_strategy,
            "logging_steps": self.logging_steps,
            "seed": self.seed,
            "dataloader_num_workers": self.dataloader_num_workers,
            "remove_unused_columns": self.remove_unused_columns,
            "label_names": self.label_names,
            "output_dir": self.output_dir,
            "report_to": self.report_to,
        }


class FinetuneJobConfig(BaseModel):
    """Complete fine-tuning job configuration."""
    # Mode
    mode: FinetuneMode = Field(default=FinetuneMode.QLORA, description="Fine-tuning mode")
    
    # Base model
    base_model: str = Field(..., description="Base model name or path")
    base_model_type: str = Field(default="causal_lm", description="Model type: causal_lm, seq2seq")
    
    # Quantization (for QLoRA)
    quantization: QuantizationType = Field(default=QuantizationType.NF4, description="Quantization type")
    load_in_4bit: bool = Field(default=True, description="Load model in 4-bit")
    load_in_8bit: bool = Field(default=False, description="Load model in 8-bit")
    
    # Training
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    
    # LoRA
    lora: LoRAConfig = Field(default_factory=LoRAConfig)
    
    # Data
    max_seq_length: int = Field(default=2048, ge=64, le=8192, description="Max sequence length")
    
    # Advanced
    use_gradient_checkpointing: bool = Field(default=True, description="Use gradient checkpointing")
    use_flash_attention: bool = Field(default=True, description="Use Flash Attention 2")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "mode": self.mode.value,
            "base_model": self.base_model,
            "base_model_type": self.base_model_type,
            "quantization": self.quantization.value,
            "load_in_4bit": self.load_in_4bit,
            "load_in_8bit": self.load_in_8bit,
            "training": self.training.model_dump(),
            "lora": self.lora.model_dump(),
            "max_seq_length": self.max_seq_length,
            "use_gradient_checkpointing": self.use_gradient_checkpointing,
            "use_flash_attention": self.use_flash_attention,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FinetuneJobConfig":
        """Create from dictionary."""
        # Handle enum conversion
        if "mode" in data:
            data["mode"] = FinetuneMode(data["mode"])
        if "quantization" in data:
            data["quantization"] = QuantizationType(data["quantization"])
        
        return cls(**data)


# Preset configurations
PRESET_CONFIGS = {
    "quick_test": FinetuneJobConfig(
        mode=FinetuneMode.QLORA,
        base_model="meta-llama/Llama-2-7b-hf",
        training=TrainingConfig(
            num_train_epochs=1,
            per_device_train_batch_size=1,
            eval_steps=50,
            save_steps=100,
            max_seq_length=512,
        ),
    ),
    "standard_7b": FinetuneJobConfig(
        mode=FinetuneMode.QLORA,
        base_model="meta-llama/Llama-2-7b-hf",
        lora=LoRAConfig(r=16, lora_alpha=32),
    ),
    "standard_13b": FinetuneJobConfig(
        mode=FinetuneMode.QLORA,
        base_model="meta-llama/Llama-2-13b-hf",
        lora=LoRAConfig(r=16, lora_alpha=32),
        training=TrainingConfig(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
        ),
    ),
    "full_finetune": FinetuneJobConfig(
        mode=FinetuneMode.FULL,
        base_model="meta-llama/Llama-2-7b-hf",
        training=TrainingConfig(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=16,
            bf16=True,
        ),
    ),
}
