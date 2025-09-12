import json
import zipfile
from pathlib import Path
import tempfile
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.models import Route, Rule, Plan
import shutil
import logging
from sqlalchemy import and_
from typing import Dict, List

logger = logging.getLogger(__name__)

class ImportService:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "cycling_imports"
        self.temp_dir.mkdir(exist_ok=True)
        
    async def validate_import(self, file: UploadFile) -> dict:
        """Validate import file and detect conflicts"""
        try:
            # Save uploaded file to temp location
            file_path = self.temp_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            # Extract data based on file type
            if file.filename.endswith('.zip'):
                data = self._process_zip_import(file_path)
            elif file.filename.endswith('.json'):
                data = self._process_json_import(file_path)
            else:
                raise ValueError("Unsupported file format")

            # Detect conflicts
            conflicts = []
            if 'routes' in data:
                conflicts += self._detect_route_conflicts(data['routes'])
            if 'rules' in data:
                conflicts += self._detect_rule_conflicts(data['rules'])
            if 'plans' in data:
                conflicts += self._detect_plan_conflicts(data['plans'])

            return {
                "valid": True,
                "conflicts": conflicts,
                "summary": {
                    "routes": len(data.get('routes', [])),
                    "rules": len(data.get('rules', [])),
                    "plans": len(data.get('plans', []))
                }
            }
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {"valid": False, "error": str(e)}

    async def execute_import(self, file: UploadFile, 
                           conflict_resolution: str, 
                           resolutions: List[dict]) -> dict:
        """Execute the import with specified conflict resolution"""
        db = SessionLocal()
        try:
            db.begin()
            
            # Process file
            file_path = self.temp_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            if file.filename.endswith('.zip'):
                data = self._process_zip_import(file_path)
                gpx_files = self._extract_gpx_files(file_path)
            elif file.filename.endswith('.json'):
                data = self._process_json_import(file_path)
                gpx_files = []
            else:
                raise ValueError("Unsupported file format")

            # Apply resolutions
            resolution_map = {r['id']: r['action'] for r in resolutions}
            
            # Import data
            results = {
                "imported": {"routes": 0, "rules": 0, "plans": 0},
                "skipped": {"routes": 0, "rules": 0, "plans": 0},
                "errors": []
            }

            # Import routes
            if 'routes' in data:
                for route_data in data['routes']:
                    action = resolution_map.get(route_data['id'], conflict_resolution)
                    try:
                        if self._should_import_route(route_data, action, db):
                            self._import_route(route_data, db)
                            results["imported"]["routes"] += 1
                        else:
                            results["skipped"]["routes"] += 1
                    except Exception as e:
                        results["errors"].append(f"Route {route_data['id']}: {str(e)}")

            # Import rules
            if 'rules' in data:
                for rule_data in data['rules']:
                    action = resolution_map.get(rule_data['id'], conflict_resolution)
                    try:
                        if self._should_import_rule(rule_data, action, db):
                            self._import_rule(rule_data, db)
                            results["imported"]["rules"] += 1
                        else:
                            results["skipped"]["rules"] += 1
                    except Exception as e:
                        results["errors"].append(f"Rule {rule_data['id']}: {str(e)}")

            # Import plans
            if 'plans' in data:
                for plan_data in data['plans']:
                    action = resolution_map.get(plan_data['id'], conflict_resolution)
                    try:
                        if self._should_import_plan(plan_data, action, db):
                            self._import_plan(plan_data, db)
                            results["imported"]["plans"] += 1
                        else:
                            results["skipped"]["plans"] += 1
                    except Exception as e:
                        results["errors"].append(f"Plan {plan_data['id']}: {str(e)}")

            # Save GPX files
            if gpx_files:
                gpx_dir = Path("/app/data/gpx")
                for gpx in gpx_files:
                    shutil.move(gpx, gpx_dir / gpx.name)

            db.commit()
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Import failed: {str(e)}")
            return {"error": str(e)}
        finally:
            db.close()
            self._cleanup_temp_files()

    def _process_zip_import(self, file_path: Path) -> dict:
        """Extract and process ZIP file import"""
        data = {}
        with zipfile.ZipFile(file_path, 'r') as zipf:
            # Find data.json
            json_files = [f for f in zipf.namelist() if f.endswith('.json')]
            if not json_files:
                raise ValueError("No JSON data found in ZIP file")
                
            with zipf.open(json_files[0]) as f:
                data = json.load(f)
                
        return data

    def _process_json_import(self, file_path: Path) -> dict:
        """Process JSON file import"""
        with open(file_path) as f:
            return json.load(f)

    def _extract_gpx_files(self, file_path: Path) -> List[Path]:
        """Extract GPX files from ZIP archive"""
        gpx_files = []
        extract_dir = self.temp_dir / "gpx"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(file_path, 'r') as zipf:
            for file in zipf.namelist():
                if file.startswith('gpx/') and file.endswith('.gpx'):
                    zipf.extract(file, extract_dir)
                    gpx_files.append(extract_dir / file)
                    
        return gpx_files

    def _detect_route_conflicts(self, routes: List[dict]) -> List[dict]:
        conflicts = []
        db = SessionLocal()
        try:
            for route in routes:
                existing = db.query(Route).filter(
                    (Route.id == route['id']) | 
                    (Route.name == route['name'])
                ).first()
                
                if existing:
                    conflict = {
                        "type": "route",
                        "id": route['id'],
                        "name": route['name'],
                        "existing_version": existing.updated_at,
                        "import_version": datetime.fromisoformat(route['updated_at']),
                        "resolution_options": ["overwrite", "rename", "skip"]
                    }
                    conflicts.append(conflict)
        finally:
            db.close()
        return conflicts

    def _should_import_route(self, route_data: dict, action: str, db) -> bool:
        existing = db.query(Route).filter(
            (Route.id == route_data['id']) | 
            (Route.name == route_data['name'])
        ).first()

        if not existing:
            return True
            
        if action == 'overwrite':
            return True
        elif action == 'rename':
            route_data['name'] = f"{route_data['name']} (Imported)"
            return True
        elif action == 'skip':
            return False
            
        return False

    def _import_route(self, route_data: dict, db):
        """Import a single route"""
        existing = db.query(Route).get(route_data['id'])
        if existing:
            # Update existing route
            existing.name = route_data['name']
            existing.description = route_data['description']
            existing.category = route_data['category']
            existing.gpx_file_path = route_data['gpx_file_path']
            existing.updated_at = datetime.fromisoformat(route_data['updated_at'])
        else:
            # Create new route
            route = Route(
                id=route_data['id'],
                name=route_data['name'],
                description=route_data['description'],
                category=route_data['category'],
                gpx_file_path=route_data['gpx_file_path'],
                created_at=datetime.fromisoformat(route_data['created_at']),
                updated_at=datetime.fromisoformat(route_data['updated_at'])
            )
            db.add(route)

    # Similar methods for rules and plans would follow...
    
    def _cleanup_temp_files(self):
        """Clean up temporary files older than 1 hour"""
        cutoff = datetime.now().timestamp() - 3600
        for file in self.temp_dir.glob("*"):
            if file.stat().st_mtime < cutoff:
                try:
                    if file.is_dir():
                        shutil.rmtree(file)
                    else:
                        file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean temp file {file}: {str(e)}")