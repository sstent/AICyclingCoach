from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse
from backend.app.services.health_monitor import HealthMonitor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge
from pathlib import Path
import json

router = APIRouter()
monitor = HealthMonitor()

# Prometheus metrics
SYNC_QUEUE = Gauge('sync_queue_size', 'Current Garmin sync queue size')
PENDING_ANALYSES = Gauge('pending_analyses', 'Number of pending workout analyses')

@router.get("/health")
async def get_health():
    return monitor.check_system_health()

@router.get("/metrics")
async def prometheus_metrics():
    # Update metrics with latest values
    health_data = monitor.check_system_health()
    SYNC_QUEUE.set(health_data['services'].get('sync_queue_size', 0))
    PENDING_ANALYSES.set(health_data['services'].get('pending_analyses', 0))
    
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/dashboard/health", response_class=JSONResponse)
async def health_dashboard():
    """Health dashboard endpoint with aggregated monitoring data"""
    health_data = monitor.check_system_health()
    
    # Get recent logs (last 100 lines)
    log_file = Path("/app/logs/app.log")
    recent_logs = []
    try:
        with log_file.open() as f:
            lines = f.readlines()[-100:]
            recent_logs = [json.loads(line.strip()) for line in lines]
    except FileNotFoundError:
        pass

    return {
        "system": health_data,
        "logs": recent_logs,
        "statistics": {
            "log_entries": len(recent_logs),
            "error_count": sum(1 for log in recent_logs if log.get('level') == 'ERROR'),
            "warning_count": sum(1 for log in recent_logs if log.get('level') == 'WARNING')
        }
    }