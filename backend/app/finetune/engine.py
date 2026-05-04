"""Fine-tuning engine for LoRA/QLoRA training."""
import os
import json
import asyncio
import logging
import math
from pathlib import Path
from typing import Optional, AsyncIterator, Callable, Any
from datetime import datetime
import uuid

from app.finetune.configs import FinetuneJobConfig, TrainingConfig, LoRAConfig

logger = logging.getLogger(__name__)


class TrainingCallback:
    """Callback for training progress updates."""
    
    def __init__(self, on_progress: Optional[Callable] = None):
        self.on_progress = on_progress
        self.metrics_buffer = []
    
    async def on_step_end(self, step: int, metrics: dict) -> None:
        """Called after each training step."""
        self.metrics_buffer.append({
            "step": step,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
        })
        
        if self.on_progress:
            await self.on_progress({
                "type": "step",
                "step": step,
                "metrics": metrics,
            })
    
    async def on_epoch_end(self, epoch: int, metrics: dict) -> None:
        """Called after each epoch."""
        if self.on_progress:
            await self.on_progress({
                "type": "epoch",
                "epoch": epoch,
                "metrics": metrics,
            })
    
    async def on_train_end(self, metrics: dict) -> None:
        """Called when training ends."""
        if self.on_progress:
            await self.on_progress({
                "type": "train_end",
                "metrics": metrics,
            })
    
    def get_metrics_history(self) -> list[dict]:
        """Get all recorded metrics."""
        return self.metrics_buffer


class FinetuneEngine:
    """
    Fine-tuning engine supporting LoRA, QLoRA, and full fine-tuning.
    
    This is a simplified implementation that demonstrates the architecture.
    In production, this would integrate with actual training libraries.
    """
    
    def __init__(
        self,
        job_id: str,
        config: FinetuneJobConfig,
        output_dir: str,
    ):
        self.job_id = job_id
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.callback: Optional[TrainingCallback] = None
        self._is_running = False
        self._is_paused = False
        self._should_stop = False
        
        # State
        self.current_step = 0
        self.current_epoch = 0
        self.current_loss = 0.0
        self.best_loss = float("inf")
        self.learning_rate = config.training.learning_rate
        
        # Simulated training data
        self._total_steps = self._calculate_total_steps()
    
    def _calculate_total_steps(self) -> int:
        """Calculate total training steps."""
        # Simplified calculation
        batch_size = (
            self.config.training.per_device_train_batch_size *
            self.config.training.gradient_accumulation_steps
        )
        # Assuming 1000 samples
        samples = 1000
        epochs = self.config.training.num_train_epochs
        
        return (samples // batch_size) * epochs
    
    async def train(
        self,
        train_data_path: str,
        eval_data_path: Optional[str] = None,
        callback: Optional[TrainingCallback] = None,
    ) -> dict:
        """
        Execute training job.
        
        Args:
            train_data_path: Path to training data
            eval_data_path: Optional path to evaluation data
            callback: Progress callback
            
        Returns:
            Training results dictionary
        """
        self.callback = callback or TrainingCallback()
        self._is_running = True
        self._should_stop = False
        
        logger.info(f"Starting training job {self.job_id}")
        logger.info(f"Config: {self.config.model_dump_json()}")
        
        start_time = datetime.utcnow()
        metrics_history = []
        
        try:
            # Simulate training loop
            for epoch in range(1, self.config.training.num_train_epochs + 1):
                if self._should_stop:
                    logger.info(f"Job {self.job_id} stopped by user")
                    break
                
                self.current_epoch = epoch
                
                # Simulate steps within epoch
                steps_per_epoch = self._total_steps // self.config.training.num_train_epochs
                
                for step in range(1, steps_per_epoch + 1):
                    # Check for pause/stop
                    while self._is_paused and not self._should_stop:
                        await asyncio.sleep(1)
                    
                    if self._should_stop:
                        break
                    
                    self.current_step = (epoch - 1) * steps_per_epoch + step
                    
                    # Simulate loss calculation (in real impl, this comes from training)
                    loss = self._simulate_loss(self.current_step)
                    self.current_loss = loss
                    
                    if loss < self.best_loss:
                        self.best_loss = loss
                    
                    # Update learning rate (cosine schedule simulation)
                    self.learning_rate = self._get_lr_for_step(self.current_step)
                    
                    metrics = {
                        "loss": round(loss, 4),
                        "learning_rate": self.learning_rate,
                        "epoch": self.current_epoch,
                        "step": self.current_step,
                        "total_steps": self._total_steps,
                        "best_loss": round(self.best_loss, 4),
                        "progress_pct": round((self.current_step / self._total_steps) * 100, 2),
                    }
                    
                    metrics_history.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        **metrics,
                    })
                    
                    # Call progress callback
                    await self.callback.on_step_end(self.current_step, metrics)
                    
                    # Simulate training time
                    await asyncio.sleep(0.1)  # 100ms per step for demo
            
            # Training completed
            end_time = datetime.utcnow()
            training_time = (end_time - start_time).total_seconds()
            
            results = {
                "status": "completed" if not self._should_stop else "stopped",
                "final_loss": self.current_loss,
                "best_loss": self.best_loss,
                "total_steps": self.current_step,
                "epochs_completed": self.current_epoch,
                "training_time_seconds": training_time,
                "metrics_history": metrics_history,
            }
            
            logger.info(f"Training job {self.job_id} finished: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Training job {self.job_id} failed: {e}")
            raise
        
        finally:
            self._is_running = False
    
    def _simulate_loss(self, step: int) -> float:
        """Simulate loss curve for demo purposes."""
        import math
        # Start high, decrease with some noise
        initial_loss = 2.5
        final_loss = 0.8
        decay_rate = step / self._total_steps
        
        # Add some variation
        noise = math.sin(step * 0.1) * 0.1
        
        loss = initial_loss - (initial_loss - final_loss) * decay_rate + noise
        return max(loss, final_loss * 0.9)
    
    def _get_lr_for_step(self, step: int) -> float:
        """Calculate learning rate for current step (cosine schedule)."""
        warmup_steps = int(self._total_steps * self.config.training.warmup_ratio)
        
        if step <= warmup_steps:
            # Linear warmup
            return self.config.training.learning_rate * (step / warmup_steps)
        else:
            # Cosine decay
            progress = (step - warmup_steps) / (self._total_steps - warmup_steps)
            return self.config.training.learning_rate * (0.5 * (1 + math.cos(math.pi * progress)))
    
    def pause(self) -> None:
        """Pause training."""
        logger.info(f"Pausing job {self.job_id}")
        self._is_paused = True
    
    def resume(self) -> None:
        """Resume training."""
        logger.info(f"Resuming job {self.job_id}")
        self._is_paused = False
    
    def stop(self) -> None:
        """Stop training."""
        logger.info(f"Stopping job {self.job_id}")
        self._should_stop = True
        self._is_paused = False
    
    def get_status(self) -> dict:
        """Get current training status."""
        return {
            "job_id": self.job_id,
            "is_running": self._is_running,
            "is_paused": self._is_paused,
            "current_step": self.current_step,
            "total_steps": self._total_steps,
            "current_epoch": self.current_epoch,
            "current_loss": self.current_loss,
            "best_loss": self.best_loss,
            "learning_rate": self.learning_rate,
            "progress_pct": round((self.current_step / self._total_steps) * 100, 2) if self._total_steps > 0 else 0,
        }
    
    async def export_model(self, output_path: Optional[str] = None) -> dict:
        """
        Export trained model.
        
        In production, this would:
        1. Merge LoRA adapter with base model (if applicable)
        2. Save model to disk
        3. Generate model card
        """
        if output_path is None:
            output_path = str(self.output_dir / "final_model")
        
        logger.info(f"Exporting model to {output_path}")
        
        # Simulate export
        await asyncio.sleep(2)
        
        return {
            "status": "exported",
            "output_path": output_path,
            "adapter_path": str(self.output_dir / "adapter"),
            "merged_path": str(Path(output_path) / "merged") if self.config.mode.value != "lora" else None,
            "file_size_mb": 450,  # Simulated
            "model_type": self.config.mode.value,
        }
    
    async def get_gpu_stats(self) -> dict:
        """Get current GPU utilization stats."""
        # In production, use nvidia-ml-py3 or similar
        return {
            "gpu_memory_used_mb": 8192,
            "gpu_memory_total_mb": 24576,
            "gpu_utilization_pct": 85,
            "temperature_c": 65,
        }


class FinetuneEngineManager:
    """Manages multiple fine-tuning engine instances."""
    
    def __init__(self):
        self._engines: dict[str, FinetuneEngine] = {}
        self._locks: dict[str, asyncio.Lock] = {}
    
    def get_lock(self, job_id: str) -> asyncio.Lock:
        """Get or create lock for a job."""
        if job_id not in self._locks:
            self._locks[job_id] = asyncio.Lock()
        return self._locks[job_id]
    
    async def create_engine(
        self,
        job_id: str,
        config: FinetuneJobConfig,
        output_dir: str,
    ) -> FinetuneEngine:
        """Create a new fine-tuning engine."""
        engine = FinetuneEngine(job_id, config, output_dir)
        self._engines[job_id] = engine
        return engine
    
    def get_engine(self, job_id: str) -> Optional[FinetuneEngine]:
        """Get an existing engine."""
        return self._engines.get(job_id)
    
    async def remove_engine(self, job_id: str) -> None:
        """Remove an engine."""
        engine = self._engines.pop(job_id, None)
        if engine:
            engine.stop()
        self._locks.pop(job_id, None)


# Global instance
_engine_manager = FinetuneEngineManager()


def get_finetune_engine_manager() -> FinetuneEngineManager:
    """Get the global finetune engine manager."""
    return _engine_manager
