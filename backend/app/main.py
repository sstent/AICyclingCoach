import logging
import json
from datetime import datetime
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from .routes import gpx as gpx_routes
from .routes import rule as rule_routes
from .routes import plan as plan_routes
from .routes import workouts as workout_routes
from .routes import prompts as prompt_routes
from .routes import dashboard as dashboard_routes
from .config import settings

# Configure structured JSON logging
class StructuredJSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
        }
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Set up logging
logger = logging.getLogger("ai_cycling_coach")
logger.setLevel(logging.INFO)

# Create console handler with structured JSON format
console_handler = logging.StreamHandler()
console_handler.setFormatter(StructuredJSONFormatter())
logger.addHandler(console_handler)

# Configure rotating file handler
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    filename="/app/logs/app.log",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(StructuredJSONFormatter())
logger.addHandler(file_handler)

app = FastAPI(
    title="AI Cycling Coach API",
    description="Backend service for AI-assisted cycling training platform",
    version="0.1.0"
)

# API Key Authentication Middleware
@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc") or request.url.path == "/health":
        return await call_next(request)
        
    api_key = request.headers.get("X-API-KEY")
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return await call_next(request)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gpx_routes.router)
app.include_router(rule_routes.router)
app.include_router(plan_routes.router)
app.include_router(workout_routes.router, prefix="/workouts", tags=["workouts"])
app.include_router(prompt_routes.router, prefix="/prompts", tags=["prompts"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/health")
async def health_check():
    """Simplified health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Cycling Coach API server")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)