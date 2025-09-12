import json
from pathlib import Path
from datetime import datetime
import zipfile
from backend.app.database import SessionLocal
from backend.app.models import Route, Rule, Plan
import tempfile
import logging
import shutil

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "cycling_exports"
        self.temp_dir.mkdir(exist_ok=True)
        
    async def create_export(self, export_types, export_format):
        """Main export creation entry point"""
        export_data = await self._fetch_export_data(export_types)
        export_path = self._generate_export_file(export_data, export_format, export_types)
        return export_path

    async def _fetch_export_data(self, export_types):
        """Fetch data from database based on requested types"""
        db = SessionLocal()
        try:
            data = {}
            
            if 'routes' in export_types:
                routes = db.query(Route).all()
                data['routes'] = [self._serialize_route(r) for r in routes]
                
            if 'rules' in export_types:
                rules = db.query(Rule).all()
                data['rules'] = [self._serialize_rule(r) for r in rules]
                
            if 'plans' in export_types:
                plans = db.query(Plan).all()
                data['plans'] = [self._serialize_plan(p) for p in plans]
                
            return data
        finally:
            db.close()

    def _generate_export_file(self, data, format, types):
        """Generate the export file in specified format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"export_{'_'.join(types)}_{timestamp}"
        
        if format == 'json':
            return self._create_json_export(data, base_name)
        elif format == 'zip':
            return self._create_zip_export(data, base_name)
        elif format == 'gpx':
            return self._create_gpx_export(data, base_name)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _create_json_export(self, data, base_name):
        """Create single JSON file export"""
        export_path = self.temp_dir / f"{base_name}.json"
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)
        return export_path

    def _create_zip_export(self, data, base_name):
        """Create ZIP archive with JSON and GPX files"""
        zip_path = self.temp_dir / f"{base_name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add JSON data
            json_path = self._create_json_export(data, base_name)
            zipf.write(json_path, arcname=json_path.name)
            
            # Add GPX files if exporting routes
            if 'routes' in data:
                gpx_dir = Path("/app/data/gpx")
                for route in data['routes']:
                    gpx_path = gpx_dir / route['gpx_file_path']
                    if gpx_path.exists():
                        zipf.write(gpx_path, arcname=f"gpx/{gpx_path.name}")
        
        return zip_path

    def _create_gpx_export(self, data, base_name):
        """Export only GPX files from routes"""
        if 'routes' not in data:
            raise ValueError("GPX export requires routes to be selected")
            
        zip_path = self.temp_dir / f"{base_name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            gpx_dir = Path("/app/data/gpx")
            for route in data['routes']:
                gpx_path = gpx_dir / route['gpx_file_path']
                if gpx_path.exists():
                    zipf.write(gpx_path, arcname=gpx_path.name)
        
        return zip_path

    def _serialize_route(self, route):
        return {
            "id": route.id,
            "name": route.name,
            "description": route.description,
            "category": route.category,
            "gpx_file_path": route.gpx_file_path,
            "created_at": route.created_at.isoformat(),
            "updated_at": route.updated_at.isoformat()
        }

    def _serialize_rule(self, rule):
        return {
            "id": rule.id,
            "name": rule.name,
            "natural_language": rule.natural_language,
            "jsonb_rules": rule.jsonb_rules,
            "version": rule.version,
            "created_at": rule.created_at.isoformat()
        }

    def _serialize_plan(self, plan):
        return {
            "id": plan.id,
            "name": plan.name,
            "jsonb_plan": plan.jsonb_plan,
            "version": plan.version,
            "created_at": plan.created_at.isoformat()
        }

    def cleanup_temp_files(self):
        """Clean up temporary export files older than 1 hour"""
        cutoff = datetime.now().timestamp() - 3600
        for file in self.temp_dir.glob("*"):
            if file.stat().st_mtime < cutoff:
                try:
                    file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {file}: {str(e)}")