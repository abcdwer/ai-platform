"""Fine-tuning job service."""
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional, AsyncIterator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.finetune import FinetuneJob, FinetuneModel, Dataset
from app.finetune.engine import get_finetune_engine_manager, TrainingCallback
from app.finetune.monitor import create_training_monitor, get_training_monitor, TrainingMetrics
from app.finetune.configs import FinetuneJobConfig, TrainingConfig, LoRAConfig
from app.services.dataset_service import DatasetService
from app.core.config import settings


class FinetuneService:
    """Service for managing fine-tuning jobs."""
    
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.engine_manager = get_finetune_engine_manager()
        self.output_dir = Path(settings.DATA_DIR) / "finetune"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_job(
        self,
        name: str,
        dataset_id: str,
        base_model: str,
        config: dict,
        description: Optional[str] = None,
    ) -> FinetuneJob:
        """Create a new fine-tuning job."""
        # Validate dataset
        dataset_service = DatasetService(self.db, self.user_id)
        dataset = await dataset_service.get_dataset(dataset_id)
        
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        if not dataset.is_validated:
            raise ValueError("Dataset must be validated before training")
        
        job_id = str(uuid.uuid4())
        
        # Parse configurations
        job_config = FinetuneJobConfig.from_dict({
            "base_model": base_model,
            **config
        })
        
        # Calculate total steps
        batch_size = (
            job_config.training.per_device_train_batch_size *
            job_config.training.gradient_accumulation_steps
        )
        steps_per_epoch = dataset.total_samples // batch_size
        total_steps = steps_per_epoch * job_config.training.num_train_epochs
        
        job = FinetuneJob(
            id=job_id,
            user_id=self.user_id,
            dataset_id=dataset_id,
            name=name,
            description=description,
            base_model=base_model,
            base_model_type=job_config.base_model_type,
            training_config=job_config.training.to_dict(),
            lora_config=job_config.lora.to_dict(),
            status="pending",
            total_steps=total_steps,
            total_epochs=job_config.training.num_train_epochs,
            metrics_history={"steps": [], "losses": [], "learning_rates": []},
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        return job
    
    async def get_job(self, job_id: str) -> Optional[FinetuneJob]:
        """Get job by ID."""
        result = await self.db.execute(
            select(FinetuneJob).where(
                FinetuneJob.id == job_id,
                FinetuneJob.user_id == self.user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_jobs(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[FinetuneJob], int]:
        """List jobs with pagination."""
        query = select(FinetuneJob).where(FinetuneJob.user_id == self.user_id)
        count_query = select(func.count(FinetuneJob.id)).where(
            FinetuneJob.user_id == self.user_id
        )
        
        if status:
            query = query.where(FinetuneJob.status == status)
            count_query = count_query.where(FinetuneJob.status == status)
        
        total = (await self.db.execute(count_query)).scalar()
        
        query = query.order_by(FinetuneJob.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        jobs = result.scalars().all()
        
        return list(jobs), total
    
    async def start_job(self, job_id: str) -> FinetuneJob:
        """Start a fine-tuning job."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status not in ["pending", "paused"]:
            raise ValueError(f"Cannot start job with status: {job.status}")
        
        # Update status
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.error_message = None
        await self.db.commit()
        
        # Create output directory for this job
        job_output_dir = self.output_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        config = FinetuneJobConfig.from_dict({
            "base_model": job.base_model,
            "base_model_type": job.base_model_type,
            "training": job.training_config,
            "lora": job.lora_config,
        })
        
        engine = await self.engine_manager.create_engine(
            job_id=job_id,
            config=config,
            output_dir=str(job_output_dir),
        )
        
        # Create training monitor
        monitor = create_training_monitor(job_id)
        await monitor.start()
        
        # Create callback for progress updates
        async def on_progress(data: dict):
            if data["type"] == "step":
                metrics = data["metrics"]
                job.current_step = metrics["step"]
                job.current_loss = metrics["loss"]
                job.best_loss = metrics.get("best_loss", job.best_loss)
                job.learning_rate = metrics["learning_rate"]
                job.current_epoch = metrics["epoch"]
                
                # Update metrics history
                history = job.metrics_history or {"steps": [], "losses": [], "learning_rates": []}
                history["steps"].append(metrics["step"])
                history["losses"].append(metrics["loss"])
                history["learning_rates"].append(metrics["learning_rate"])
                job.metrics_history = history
                
                await self.db.commit()
                
                # Record metrics to monitor
                training_metrics = TrainingMetrics(
                    timestamp=datetime.utcnow().isoformat(),
                    step=metrics["step"],
                    epoch=metrics["epoch"],
                    loss=metrics["loss"],
                    learning_rate=metrics["learning_rate"],
                    gpu_memory_used=0,
                    gpu_utilization=0.0,
                    samples_per_second=0.0,
                    steps_per_second=0.0,
                    best_loss=metrics.get("best_loss", metrics["loss"]),
                    progress_pct=metrics.get("progress_pct", 0),
                )
                await monitor.record_metrics(training_metrics)
        
        # Start training in background
        callback = TrainingCallback(on_progress=on_progress)
        
        # Get dataset path
        dataset_service = DatasetService(self.db, self.user_id)
        dataset = await dataset_service.get_dataset(job.dataset_id)
        train_path = dataset.file_path if dataset else ""
        
        asyncio.create_task(self._run_training(job_id, engine, train_path, callback))
        
        await self.db.refresh(job)
        return job
    
    async def _run_training(
        self,
        job_id: str,
        engine,
        train_path: str,
        callback,
    ) -> None:
        """Run training job in background."""
        try:
            results = await engine.train(train_path, callback=callback)
            
            # Update job with results
            job = await self.get_job(job_id)
            if job:
                job.status = results["status"]
                job.completed_at = datetime.utcnow()
                job.current_loss = results.get("final_loss")
                job.best_loss = results.get("best_loss")
                
                if results["status"] == "completed":
                    # Create model record
                    await self._create_model_from_job(job, engine)
                
                await self.db.commit()
                
        except Exception as e:
            job = await self.get_job(job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                await self.db.commit()
    
    async def _create_model_from_job(self, job: FinetuneJob, engine) -> Optional[FinetuneModel]:
        """Create a model record after successful training."""
        model_id = str(uuid.uuid4())
        model_output_dir = self.output_dir / job.id / "model"
        
        # Export model
        export_result = await engine.export_model(str(model_output_dir))
        
        model = FinetuneModel(
            id=model_id,
            user_id=self.user_id,
            job_id=job.id,
            name=f"{job.name} (Fine-tuned)",
            description=job.description,
            base_model=job.base_model,
            adapter_path=export_result["adapter_path"],
            merged_path=export_result.get("merged_path"),
            final_loss=job.best_loss,
            model_type=job.lora_config.get("mode", "lora"),
            file_size=(export_result.get("file_size_mb", 0) or 0) * 1024 * 1024,
        )
        
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        
        return model
    
    async def pause_job(self, job_id: str) -> FinetuneJob:
        """Pause a running job."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status != "running":
            raise ValueError(f"Cannot pause job with status: {job.status}")
        
        engine = self.engine_manager.get_engine(job_id)
        if engine:
            engine.pause()
        
        job.status = "paused"
        await self.db.commit()
        await self.db.refresh(job)
        
        return job
    
    async def resume_job(self, job_id: str) -> FinetuneJob:
        """Resume a paused job."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status != "paused":
            raise ValueError(f"Cannot resume job with status: {job.status}")
        
        engine = self.engine_manager.get_engine(job_id)
        if engine:
            engine.resume()
        
        job.status = "running"
        await self.db.commit()
        await self.db.refresh(job)
        
        return job
    
    async def stop_job(self, job_id: str) -> FinetuneJob:
        """Stop a running job."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status not in ["running", "paused"]:
            raise ValueError(f"Cannot stop job with status: {job.status}")
        
        engine = self.engine_manager.get_engine(job_id)
        if engine:
            engine.stop()
        
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(job)
        
        return job
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        if job.status == "running":
            await self.stop_job(job_id)
        
        # Cleanup
        job_dir = self.output_dir / job_id
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir)
        
        await self.db.delete(job)
        await self.db.commit()
        
        return True
    
    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get detailed job status."""
        job = await self.get_job(job_id)
        if not job:
            return None
        
        engine = self.engine_manager.get_engine(job_id)
        engine_status = engine.get_status() if engine else {}
        
        monitor = get_training_monitor(job_id)
        loss_curve = monitor.get_loss_curve() if monitor else {}
        
        return {
            "job": {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "current_step": job.current_step,
                "total_steps": job.total_steps,
                "current_epoch": job.current_epoch,
                "total_epochs": job.total_epochs,
                "current_loss": job.current_loss,
                "best_loss": job.best_loss,
                "learning_rate": job.learning_rate,
                "progress_pct": job.get_progress_percentage(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
            },
            "engine": engine_status,
            "loss_curve": loss_curve,
        }
    
    async def stream_job_progress(self, job_id: str) -> AsyncIterator[str]:
        """Stream job progress as SSE."""
        monitor = get_training_monitor(job_id)
        if not monitor:
            return
        
        sub_id, queue = monitor.subscribe()
        
        try:
            async for update in monitor.stream_updates(sub_id):
                yield f"data: {json.dumps(update)}\n\n"
        finally:
            monitor.unsubscribe(sub_id)
    
    # Model management
    async def get_model(self, model_id: str) -> Optional[FinetuneModel]:
        """Get model by ID."""
        result = await self.db.execute(
            select(FinetuneModel).where(
                FinetuneModel.id == model_id,
                FinetuneModel.user_id == self.user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_models(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[FinetuneModel], int]:
        """List fine-tuned models."""
        count_query = select(func.count(FinetuneModel.id)).where(
            FinetuneModel.user_id == self.user_id
        )
        total = (await self.db.execute(count_query)).scalar()
        
        query = select(FinetuneModel).where(
            FinetuneModel.user_id == self.user_id
        ).order_by(FinetuneModel.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return list(models), total
    
    async def deploy_model(self, model_id: str) -> FinetuneModel:
        """Deploy a fine-tuned model."""
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        if model.is_deployed:
            raise ValueError("Model is already deployed")
        
        # In production, this would deploy to a serving endpoint
        model.is_deployed = True
        model.deployment_status = "deployed"
        model.deployment_endpoint = f"/api/models/deployed/{model.id}"
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return model
    
    async def undeploy_model(self, model_id: str) -> FinetuneModel:
        """Undeploy a fine-tuned model."""
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        model.is_deployed = False
        model.deployment_status = "not_deployed"
        model.deployment_endpoint = None
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return model
    
    async def delete_model(self, model_id: str) -> bool:
        """Delete a fine-tuned model."""
        model = await self.get_model(model_id)
        if not model:
            return False
        
        if model.is_deployed:
            await self.undeploy_model(model_id)
        
        # Cleanup files
        if model.merged_path:
            import shutil
            path = Path(model.merged_path)
            if path.exists():
                shutil.rmtree(path)
        
        await self.db.delete(model)
        await self.db.commit()
        
        return True
