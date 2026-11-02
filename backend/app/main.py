from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.database.init_db import init_db
from app.api.incidents import incidents_router
from app.api.metrics import metrics_router
from app.api.repositories import repositories_router
from app.api.evaluations import evaluations_router
from app.api.ws import ws_router
from app.api.rag import rag_router
from prometheus_client import make_asgi_app

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    try:
        await init_db()
        logger.info("Database initialization and schema validation complete.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Production Incident Investigator AI Platform API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/prometheus", metrics_app)

# Include API Routers
app.include_router(incidents_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(repositories_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "online"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": str(exc), "path": str(request.url.path)}
    )
