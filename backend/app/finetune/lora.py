"""LoRA implementation utilities."""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LoRAAdapter:
    """LoRA adapter information."""
    path: str
    rank: int
    alpha: int
    target_modules: list[str]
    config: dict


class LoRAUtils:
    """
    LoRA utilities for model preparation and adapter management.
    
    This module provides helpers for:
    - Preparing models for LoRA training
    - Applying adapters to models
    - Merging adapters with base models
    - Saving and loading adapters
    """
    
    # Common target modules for different architectures
    TARGET_MODULES = {
        "llama": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "mistral": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "gpt2": ["c_attn", "c_proj"],
        "gpt_neox": ["query_key_value", "dense_h_to_4h", "dense_4h_to_h", "dense"],
        "mpt": ["Wqkv", "out_proj"],
        "falcon": ["query_key_value", "dense"],
        "bert": ["query", "key", "value", "dense"],
        "t5": ["q", "k", "v", "o"],
        "default": ["q_proj", "v_proj"],
    }
    
    @classmethod
    def get_target_modules(cls, model_name: str) -> list[str]:
        """Get target modules for a given model architecture."""
        model_lower = model_name.lower()
        
        for arch, modules in cls.TARGET_MODULES.items():
            if arch in model_lower:
                return modules
        
        return cls.TARGET_MODULES["default"]
    
    @classmethod
    def prepare_model_for_lora(
        cls,
        model: Any,
        model_name: str,
        lora_config: dict,
    ) -> Any:
        """
        Prepare a model for LoRA training.
        
        Args:
            model: The base model
            model_name: Name or path of the model
            lora_config: LoRA configuration dict
            
        Returns:
            Model with LoRA applied
        """
        try:
            from peft import get_peft_model, LoraConfig, TaskType
            
            # Auto-detect target modules if not specified
            if "target_modules" not in lora_config or lora_config["target_modules"] is None:
                lora_config["target_modules"] = cls.get_target_modules(model_name)
            
            # Convert bias
            bias = lora_config.get("bias", "none")
            if isinstance(bias, str):
                pass  # Already string
            
            # Create PEFT config
            task_type = TaskType.CAUSAL_LM
            if "task_type" in lora_config:
                task_type = TaskType[lora_config["task_type"]]
            
            peft_config = LoraConfig(
                r=lora_config.get("r", 8),
                lora_alpha=lora_config.get("lora_alpha", 16),
                lora_dropout=lora_config.get("lora_dropout", 0.05),
                target_modules=lora_config["target_modules"],
                bias=bias,
                task_type=task_type,
            )
            
            # Apply LoRA
            model = get_peft_model(model, peft_config)
            model.print_trainable_parameters()
            
            return model
            
        except ImportError:
            logger.warning("PEFT not available, returning model unchanged")
            return model
    
    @classmethod
    def merge_adapter(cls, model: Any, adapter_path: str) -> Any:
        """
        Merge LoRA adapter with base model.
        
        Args:
            model: Base model
            adapter_path: Path to LoRA adapter
            
        Returns:
            Merged model
        """
        try:
            from peft import PeftModel
            from transformers import AutoModelForCausalLM
            
            # Load adapter
            model = PeftModel.from_pretrained(model, adapter_path)
            
            # Merge
            merged_model = model.merge_and_unload()
            
            return merged_model
            
        except ImportError:
            logger.error("Failed to merge adapter: PEFT not available")
            raise
    
    @classmethod
    def save_adapter(
        cls,
        model: Any,
        output_path: str,
        config: dict,
    ) -> LoRAAdapter:
        """
        Save LoRA adapter.
        
        Args:
            model: Model with LoRA applied
            output_path: Directory to save adapter
            config: LoRA configuration
            
        Returns:
            LoRA adapter info
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save adapter
        model.save_pretrained(str(output_dir))
        
        # Save config
        adapter_config = {
            "base_model_name_or_path": config.get("base_model", "unknown"),
            "peft_type": "LORa",
            "task_type": "CAUSAL_LM",
            "rank": config.get("r", 8),
            "lora_alpha": config.get("lora_alpha", 16),
            "target_modules": config.get("target_modules", []),
        }
        
        config_path = output_dir / "adapter_config.json"
        with open(config_path, "w") as f:
            json.dump(adapter_config, f, indent=2)
        
        return LoRAAdapter(
            path=str(output_dir),
            rank=config.get("r", 8),
            alpha=config.get("lora_alpha", 16),
            target_modules=config.get("target_modules", []),
            config=adapter_config,
        )
    
    @classmethod
    def load_adapter(cls, base_model: Any, adapter_path: str) -> Any:
        """
        Load LoRA adapter into model.
        
        Args:
            base_model: Base model
            adapter_path: Path to adapter
            
        Returns:
            Model with adapter loaded
        """
        try:
            from peft import PeftModel
            
            model = PeftModel.from_pretrained(base_model, adapter_path)
            return model
            
        except ImportError:
            logger.error("Failed to load adapter: PEFT not available")
            raise
    
    @classmethod
    def get_adapter_info(cls, adapter_path: str) -> Optional[LoRAAdapter]:
        """Get information about a saved adapter."""
        config_path = Path(adapter_path) / "adapter_config.json"
        
        if not config_path.exists():
            return None
        
        with open(config_path) as f:
            config = json.load(f)
        
        return LoRAAdapter(
            path=adapter_path,
            rank=config.get("rank", config.get("r", 8)),
            alpha=config.get("lora_alpha", 16),
            target_modules=config.get("target_modules", []),
            config=config,
        )
    
    @classmethod
    def estimate_adapter_size(
        cls,
        base_model_params: int,
        rank: int,
        layer_types: list[str] = None,
    ) -> int:
        """
        Estimate LoRA adapter size in bytes.
        
        Args:
            base_model_params: Number of parameters in base model
            rank: LoRA rank
            layer_types: Types of layers being adapted
            
        Returns:
            Estimated adapter size in bytes
        """
        # LoRA updates are rank * (in_dim + out_dim) per layer
        # For typical attention layers, in_dim = out_dim = hidden_size
        # Assuming hidden_size = 4096 for 7B models
        
        if layer_types is None:
            layer_types = ["attention"]  # Most common
        
        # Rough estimation: adapter has ~0.1% of base model parameters
        # More precise: for rank r, we have r * (d + d) params per layer
        # With ~32 attention layers for 7B model
        
        num_layers = 32  # For 7B model
        hidden_size = 4096
        
        adapter_params = 0
        for layer_type in layer_types:
            if layer_type == "attention":
                # q, k, v, o projections
                adapter_params += 4 * rank * hidden_size * 2
            elif layer_type == "mlp":
                # Up and down projections
                adapter_params += 2 * rank * hidden_size * 2
        
        adapter_params *= num_layers
        
        # 2 bytes per parameter (float16)
        return int(adapter_params * 2)


def quantize_model_4bit(model: Any, config: dict = None) -> Any:
    """
    Quantize model to 4-bit for QLoRA.
    
    Args:
        model: Model to quantize
        config: Quantization config
        
    Returns:
        Quantized model
    """
    try:
        from transformers import BitsAndBytesConfig
        
        if config is None:
            config = {}
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=getattr(
                __import__("torch"),
                config.get("compute_dtype", "float16")
            ),
            bnb_4bit_quant_type=config.get("quant_type", "nf4"),
            bnb_4bit_use_double_quant=config.get("use_double_quant", True),
        )
        
        model = model.with_quantized_attention()
        return model
        
    except ImportError:
        logger.warning("BitsAndBytes not available, skipping quantization")
        return model


def apply_lora_to_model(
    model: Any,
    config: dict,
) -> Any:
    """
    Apply LoRA to a model.
    
    This is a convenience function that combines model preparation
    and LoRA application.
    """
    return LoRAUtils.prepare_model_for_lora(
        model=model,
        model_name=config.get("base_model", ""),
        lora_config=config.get("lora", {}),
    )
