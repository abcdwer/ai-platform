"""Monitoring and metrics endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.agent import Agent
from app.models.knowledge import KnowledgeBase
from app.models.document import Document
from app.models.workflow import Workflow, WorkflowExecution

router = APIRouter(tags=["Monitoring"])


class ServiceHealth(BaseModel):
    """Health status of a single service."""
    name: str
    status: str  # "online", "offline", "degraded"
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response with all services status."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    services: dict[str, ServiceHealth]
    uptime_seconds: float


class MetricsResponse(BaseModel):
    """System metrics response."""
    timestamp: str
    uptime_seconds: float
    statistics: dict
    requests: dict


# Global metrics storage (in production, use Redis or similar)
_metrics = {
    "total_requests": 0,
    "requests_by_endpoint": {},
    "requests_by_method": {},
    "response_times": [],
    "errors": 0,
}

_start_time = datetime.utcnow()


def record_request(endpoint: str, method: str, response_time_ms: float, status_code: int):
    """Record a request for metrics."""
    _metrics["total_requests"] += 1
    _metrics["requests_by_endpoint"][endpoint] = _metrics["requests_by_endpoint"].get(endpoint, 0) + 1
    _metrics["requests_by_method"][method] = _metrics["requests_by_method"].get(method, 0) + 1
    _metrics["response_times"].append(response_time_ms)
    
    # Keep only last 1000 response times
    if len(_metrics["response_times"]) > 1000:
        _metrics["response_times"] = _metrics["response_times"][-1000:]
    
    if status_code >= 400:
        _metrics["errors"] += 1


async def check_database_health(db: AsyncSession) -> ServiceHealth:
    """Check database connectivity."""
    import time
    start = time.time()
    try:
        await db.execute(select(func.count()).select_from(User))
        latency = (time.time() - start) * 1000
        return ServiceHealth(name="database", status="online", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceHealth(name="database", status="offline", error=str(e))


async def check_redis_health() -> ServiceHealth:
    """Check Redis connectivity."""
    import time
    from app.core.config import settings
    
    if not settings.REDIS_URL:
        return ServiceHealth(name="redis", status="degraded", error="Redis not configured")
    
    start = time.time()
    try:
        import redis.asyncio as redis
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        latency = (time.time() - start) * 1000
        await client.close()
        return ServiceHealth(name="redis", status="online", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceHealth(name="redis", status="offline", error=str(e))


async def check_chroma_health() -> ServiceHealth:
    """Check ChromaDB connectivity."""
    import time
    try:
        from app.rag.chroma_client import get_chroma_client
        start = time.time()
        client = get_chroma_client()
        # Try to get collection count
        client.list_collections()
        latency = (time.time() - start) * 1000
        return ServiceHealth(name="chromadb", status="online", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceHealth(name="chromadb", status="offline", error=str(e))


async def check_ollama_health() -> ServiceHealth:
    """Check Ollama connectivity."""
    import time
    from app.core.config import settings
    
    if not settings.OLLAMA_BASE_URL:
        return ServiceHealth(name="ollama", status="degraded", error="Ollama not configured")
    
    start = time.time()
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            latency = (time.time() - start) * 1000
            if response.status_code == 200:
                return ServiceHealth(name="ollama", status="online", latency_ms=round(latency, 2))
            else:
                return ServiceHealth(name="ollama", status="degraded", error=f"Status: {response.status_code}")
    except Exception as e:
        return ServiceHealth(name="ollama", status="offline", error=str(e))


@router.get("/api/health", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint returning status of all services.
    
    Checks the health of:
    - Database (PostgreSQL)
    - Redis cache
    - ChromaDB vector store
    - Ollama local models
    
    Returns overall status as:
    - **healthy**: All services operational
    - **degraded**: Some services have issues
    - **unhealthy**: Critical services down
    """
    # Check all services in parallel
    import asyncio
    
    db_health, redis_health, chroma_health, ollama_health = await asyncio.gather(
        check_database_health(db),
        check_redis_health(),
        check_chroma_health(),
        check_ollama_health(),
    )
    
    services = {
        "api": ServiceHealth(name="api", status="online", latency_ms=0),
        "database": db_health,
        "redis": redis_health,
        "chromadb": chroma_health,
        "ollama": ollama_health,
    }
    
    # Determine overall status
    offline_count = sum(1 for s in services.values() if s.status == "offline")
    degraded_count = sum(1 for s in services.values() if s.status == "degraded")
    
    if offline_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        services={k: v.model_dump() for k, v in services.items()},
        uptime_seconds=round(uptime, 2),
    )


@router.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get system metrics and statistics.
    
    Returns:
    - **statistics**: Counts of users, conversations, agents, etc.
    - **requests**: API request statistics
    - **uptime**: Application uptime
    """
    # Get database statistics
    user_count = await db.scalar(select(func.count()).select_from(User))
    conversation_count = await db.scalar(select(func.count()).select_from(Conversation))
    agent_count = await db.scalar(select(func.count()).select_from(Agent))
    knowledge_count = await db.scalar(select(func.count()).select_from(KnowledgeBase))
    document_count = await db.scalar(select(func.count()).select_from(Document))
    workflow_count = await db.scalar(select(func.count()).select_from(Workflow))
    
    # Get workflow execution count
    execution_count = await db.scalar(select(func.count()).select_from(WorkflowExecution))
    
    # Calculate average response time
    avg_response_time = 0
    if _metrics["response_times"]:
        avg_response_time = sum(_metrics["response_times"]) / len(_metrics["response_times"])
    
    # Calculate error rate
    error_rate = 0
    if _metrics["total_requests"] > 0:
        error_rate = (_metrics["errors"] / _metrics["total_requests"]) * 100
    
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    
    return MetricsResponse(
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=round(uptime, 2),
        statistics={
            "users": user_count or 0,
            "conversations": conversation_count or 0,
            "agents": agent_count or 0,
            "knowledge_bases": knowledge_count or 0,
            "documents": document_count or 0,
            "workflows": workflow_count or 0,
            "workflow_executions": execution_count or 0,
        },
        requests={
            "total": _metrics["total_requests"],
            "by_endpoint": _metrics["requests_by_endpoint"],
            "by_method": _metrics["requests_by_method"],
            "errors": _metrics["errors"],
            "error_rate_percent": round(error_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
        },
    )
