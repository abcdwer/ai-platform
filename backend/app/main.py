"""Main FastAPI application."""
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.routes import chat, agents, models, conversations, auth, tools, knowledge, workflow, multi_agent, finetune, mcp, export_import, monitoring
from app.services.model_dispatcher import get_model_dispatcher


# Startup time for uptime calculation
_start_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize model dispatcher
    try:
        dispatcher = get_model_dispatcher()
        health = await dispatcher.health_check_all()
        for provider, status in health.items():
            if status.get("status") == "online":
                logger.info(f"{provider} provider is online")
            else:
                logger.warning(f"{provider} provider: {status.get('error', 'unknown error')}")
    except Exception as e:
        logger.error(f"Failed to initialize model dispatcher: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Platform - Unified interface for local and cloud AI models",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        """Middleware to track request metrics."""
        import time
        from app.api.routes.monitoring import record_request
        
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Record metrics for API endpoints
        if request.url.path.startswith("/api"):
            record_request(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=round(process_time, 2),
                status_code=response.status_code
            )
        
        # Add response time header
        response.headers["X-Process-Time"] = str(round(process_time, 2))
        return response
    
    # Include routers
    app.include_router(chat.router)
    app.include_router(agents.router)
    app.include_router(models.router)
    app.include_router(conversations.router)
    app.include_router(auth.router)
    app.include_router(tools.router)
    app.include_router(knowledge.router)
    app.include_router(workflow.router)
    app.include_router(multi_agent.router)
    app.include_router(finetune.router)
    app.include_router(mcp.router)
    app.include_router(export_import.router)
    app.include_router(monitoring.router)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "api": "/api"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    @app.get("/api/status")
    async def system_status():
        """Get system status including provider health."""
        global _start_time
        
        dispatcher = get_model_dispatcher()
        provider_health = await dispatcher.health_check_all()
        models_by_provider = await dispatcher.list_all_models()
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - _start_time).total_seconds()
        
        # Count connected models
        connected_models = sum(len(models) for models in models_by_provider.values())
        
        # Determine overall status
        all_online = all(h.get("status") == "online" for h in provider_health.values())
        any_online = any(h.get("status") == "online" for h in provider_health.values())
        
        if all_online:
            status = "online"
        elif any_online:
            status = "degraded"
        else:
            status = "offline"
        
        return {
            "status": status,
            "version": settings.APP_VERSION,
            "uptime_seconds": uptime_seconds,
            "providers": {
                provider: {
                    "status": health.get("status", "unknown"),
                    "error": health.get("error"),
                    "model_count": len(models_by_provider.get(provider, []))
                }
                for provider, health in provider_health.items()
            },
            "connected_models": connected_models,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return app


app = create_app()
