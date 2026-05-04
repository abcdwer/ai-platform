"""Fine-tuning API routes."""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.finetune_service import FinetuneService
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/finetune", tags=["Fine-tuning"])

# User ID dependency (simplified - in production, use proper auth)
async def get_user_id() -> str:
    return "default-user"


# ============== Dataset Routes ==============

@router.post("/datasets/upload")
async def upload_dataset(
    name: str = Form(...),
    file: UploadFile = File(...),
    format_type: str = Form(default="conversation"),
    description: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Upload a dataset file for fine-tuning."""
    try:
        # Read file content
        content = await file.read()
        
        service = DatasetService(db, user_id)
        dataset = await service.upload_dataset(
            name=name,
            content=content,
            file_name=file.filename,
            format_type=format_type,
            description=description,
        )
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "file_name": dataset.file_name,
            "file_size": dataset.file_size,
            "format_type": dataset.format_type,
            "total_samples": dataset.total_samples,
            "total_tokens": dataset.total_tokens,
            "is_validated": dataset.is_validated,
            "validation_errors": dataset.validation_errors,
            "created_at": dataset.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    validated_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """List all datasets."""
    service = DatasetService(db, user_id)
    datasets, total = await service.list_datasets(skip, limit, validated_only)
    
    return {
        "items": [
            {
                "id": d.id,
                "name": d.name,
                "file_name": d.file_name,
                "file_size": d.file_size,
                "format_type": d.format_type,
                "total_samples": d.total_samples,
                "total_tokens": d.total_tokens,
                "is_validated": d.is_validated,
                "created_at": d.created_at.isoformat(),
            }
            for d in datasets
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get dataset details."""
    service = DatasetService(db, user_id)
    dataset = await service.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "file_name": dataset.file_name,
        "file_size": dataset.file_size,
        "file_format": dataset.file_format,
        "format_type": dataset.format_type,
        "total_samples": dataset.total_samples,
        "total_tokens": dataset.total_tokens,
        "avg_turns": dataset.avg_turns,
        "is_validated": dataset.is_validated,
        "validation_errors": dataset.validation_errors,
        "train_ratio": dataset.train_ratio,
        "validation_ratio": dataset.validation_ratio,
        "created_at": dataset.created_at.isoformat(),
        "updated_at": dataset.updated_at.isoformat(),
    }


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Preview dataset samples."""
    service = DatasetService(db, user_id)
    samples = await service.preview_dataset(dataset_id, limit)
    
    if samples is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {"samples": samples}


@router.post("/datasets/{dataset_id}/split")
async def split_dataset(
    dataset_id: str,
    train_ratio: float = Query(default=0.9, ge=0.5, le=0.99),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Split dataset into train/validation sets."""
    try:
        service = DatasetService(db, user_id)
        result = await service.split_dataset(dataset_id, train_ratio)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Delete a dataset."""
    service = DatasetService(db, user_id)
    deleted = await service.delete_dataset(dataset_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {"status": "deleted"}


# ============== Job Routes ==============

@router.post("/jobs")
async def create_job(
    name: str = Form(...),
    dataset_id: str = Form(...),
    base_model: str = Form(...),
    config: str = Form(...),  # JSON string
    description: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Create a new fine-tuning job."""
    try:
        config_dict = json.loads(config)
        
        service = FinetuneService(db, user_id)
        job = await service.create_job(
            name=name,
            dataset_id=dataset_id,
            base_model=base_model,
            config=config_dict,
            description=description,
        )
        
        return {
            "id": job.id,
            "name": job.name,
            "dataset_id": job.dataset_id,
            "base_model": job.base_model,
            "status": job.status,
            "total_steps": job.total_steps,
            "created_at": job.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid config JSON: {e}")


@router.get("/jobs")
async def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """List all fine-tuning jobs."""
    service = FinetuneService(db, user_id)
    jobs, total = await service.list_jobs(skip, limit, status)
    
    return {
        "items": [
            {
                "id": j.id,
                "name": j.name,
                "dataset_id": j.dataset_id,
                "base_model": j.base_model,
                "status": j.status,
                "current_step": j.current_step,
                "total_steps": j.total_steps,
                "current_loss": j.current_loss,
                "best_loss": j.best_loss,
                "progress_pct": j.get_progress_percentage(),
                "created_at": j.created_at.isoformat(),
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get job details and current status."""
    service = FinetuneService(db, user_id)
    status = await service.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status


@router.post("/jobs/{job_id}/start")
async def start_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Start a fine-tuning job."""
    try:
        service = FinetuneService(db, user_id)
        job = await service.start_job(job_id)
        
        return {
            "id": job.id,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Pause a running job."""
    try:
        service = FinetuneService(db, user_id)
        job = await service.pause_job(job_id)
        
        return {"id": job.id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Resume a paused job."""
    try:
        service = FinetuneService(db, user_id)
        job = await service.resume_job(job_id)
        
        return {"id": job.id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/stop")
async def stop_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Stop a running job."""
    try:
        service = FinetuneService(db, user_id)
        job = await service.stop_job(job_id)
        
        return {"id": job.id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Delete a job."""
    service = FinetuneService(db, user_id)
    deleted = await service.delete_job(job_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"status": "deleted"}


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Stream job progress updates via SSE."""
    service = FinetuneService(db, user_id)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        async for data in service.stream_job_progress(job_id):
            yield data
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============== Model Routes ==============

@router.get("/models")
async def list_models(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """List all fine-tuned models."""
    service = FinetuneService(db, user_id)
    models, total = await service.list_models(skip, limit)
    
    return {
        "items": [
            {
                "id": m.id,
                "name": m.name,
                "job_id": m.job_id,
                "base_model": m.base_model,
                "model_type": m.model_type,
                "final_loss": m.final_loss,
                "is_deployed": m.is_deployed,
                "deployment_status": m.deployment_status,
                "file_size_mb": m.get_model_size_mb(),
                "created_at": m.created_at.isoformat(),
            }
            for m in models
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get fine-tuned model details."""
    service = FinetuneService(db, user_id)
    model = await service.get_model(model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "job_id": model.job_id,
        "base_model": model.base_model,
        "adapter_path": model.adapter_path,
        "merged_path": model.merged_path,
        "model_type": model.model_type,
        "quantization": model.quantization,
        "final_loss": model.final_loss,
        "final_perplexity": model.final_perplexity,
        "total_parameters": model.total_parameters,
        "trainable_parameters": model.trainable_parameters,
        "file_size_mb": model.get_model_size_mb(),
        "is_deployed": model.is_deployed,
        "deployment_status": model.deployment_status,
        "deployment_endpoint": model.deployment_endpoint,
        "model_config": model.model_config,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat(),
    }


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Deploy a fine-tuned model."""
    try:
        service = FinetuneService(db, user_id)
        model = await service.deploy_model(model_id)
        
        return {
            "id": model.id,
            "is_deployed": model.is_deployed,
            "deployment_status": model.deployment_status,
            "deployment_endpoint": model.deployment_endpoint,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/undeploy")
async def undeploy_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Undeploy a fine-tuned model."""
    try:
        service = FinetuneService(db, user_id)
        model = await service.undeploy_model(model_id)
        
        return {
            "id": model.id,
            "is_deployed": model.is_deployed,
            "deployment_status": model.deployment_status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Delete a fine-tuned model."""
    service = FinetuneService(db, user_id)
    deleted = await service.delete_model(model_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "deleted"}
