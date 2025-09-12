import psutil
from datetime import datetime
import logging
from typing import Dict, Any
from sqlalchemy import text
from backend.app.database import get_db
from backend.app.models.garmin_sync_log import GarminSyncLog, SyncStatus
import requests
from backend.app.config import settings

logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.warning_thresholds = {
            'cpu_percent': 80,
            'memory_percent': 75,
            'disk_percent': 85
        }

    def check_system_health(self) -> Dict[str, Any]:
        """Check vital system metrics and log warnings"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'services': self._check_service_health()
        }
        
        self._log_anomalies(metrics)
        return metrics

    def _check_service_health(self) -> Dict[str, str]:
        """Check critical application services"""
        return {
            'database': self._check_database(),
            'garmin_sync': self._check_garmin_sync(),
            'ai_service': self._check_ai_service(),
            'sync_queue_size': self._get_sync_queue_size(),
            'pending_analyses': self._count_pending_analyses()
        }

    def _get_sync_queue_size(self) -> int:
        """Get number of pending sync operations"""
        from backend.app.models.garmin_sync_log import GarminSyncLog, SyncStatus
        return GarminSyncLog.query.filter_by(status=SyncStatus.PENDING).count()

    def _count_pending_analyses(self) -> int:
        """Count workouts needing analysis"""
        from backend.app.models.workout import Workout
        return Workout.query.filter_by(analysis_status='pending').count()

    def _check_database(self) -> str:
        try:
            with get_db() as db:
                db.execute(text("SELECT 1"))
            return "ok"
        except Exception as e:
            logger.error("Database check failed", extra={"component": "database", "error": str(e)})
            return "down"

    def _check_garmin_sync(self) -> str:
        try:
            last_sync = GarminSyncLog.get_latest()
            if last_sync and last_sync.status == SyncStatus.FAILED:
                logger.warning("Garmin sync has failed status", extra={"component": "garmin_sync", "status": last_sync.status.value})
                return "warning"
            return "ok"
        except Exception as e:
            logger.error("Garmin sync check failed", extra={"component": "garmin_sync", "error": str(e)})
            return "down"

    def _check_ai_service(self) -> str:
        try:
            response = requests.get(
                f"{settings.AI_SERVICE_URL}/ping",
                timeout=5,
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
            )
            return "ok" if response.ok else "down"
        except Exception as e:
            logger.error("AI service check failed", extra={"component": "ai_service", "error": str(e)})
            return "down"

    def _log_anomalies(self, metrics: Dict[str, Any]):
        alerts = []
        for metric, value in metrics.items():
            if metric in self.warning_thresholds and value > self.warning_thresholds[metric]:
                alerts.append(f"{metric} {value}%")
                logger.warning("System threshold exceeded", extra={"metric": metric, "value": value, "threshold": self.warning_thresholds[metric]})
        
        if alerts:
            logger.warning("System thresholds exceeded", extra={"alerts": alerts})