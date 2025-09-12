"""
Route service for TUI application.
Manages GPX routes and route visualization without HTTP dependencies.
"""
import gpxpy
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.route import Route
from backend.app.models.section import Section


class RouteService:
    """Service for route and GPX operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_routes(self) -> List[Dict]:
        """Get all routes."""
        try:
            result = await self.db.execute(
                select(Route).order_by(desc(Route.created_at))
            )
            routes = result.scalars().all()
            
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "total_distance": r.total_distance,
                    "elevation_gain": r.elevation_gain,
                    "gpx_file_path": r.gpx_file_path,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                } for r in routes
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching routes: {str(e)}")
    
    async def get_route(self, route_id: int) -> Optional[Dict]:
        """Get a specific route by ID."""
        try:
            route = await self.db.get(Route, route_id)
            if not route:
                return None
                
            return {
                "id": route.id,
                "name": route.name,
                "description": route.description,
                "total_distance": route.total_distance,
                "elevation_gain": route.elevation_gain,
                "gpx_file_path": route.gpx_file_path,
                "created_at": route.created_at.isoformat() if route.created_at else None
            }
            
        except Exception as e:
            raise Exception(f"Error fetching route {route_id}: {str(e)}")
    
    async def load_gpx_file(self, file_path: str) -> Dict:
        """Load and parse GPX file."""
        try:
            gpx_path = Path(file_path)
            if not gpx_path.exists():
                raise Exception(f"GPX file not found: {file_path}")
            
            with open(gpx_path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
            
            # Extract track points
            track_points = []
            total_distance = 0
            min_elevation = float('inf')
            max_elevation = float('-inf')
            
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        track_points.append({
                            "lat": point.latitude,
                            "lon": point.longitude,
                            "ele": point.elevation if point.elevation else 0,
                            "time": point.time.isoformat() if point.time else None
                        })
                        
                        if point.elevation:
                            min_elevation = min(min_elevation, point.elevation)
                            max_elevation = max(max_elevation, point.elevation)
            
            # Calculate total distance and elevation gain
            if track_points:
                total_distance = self._calculate_total_distance(track_points)
                elevation_gain = max_elevation - min_elevation if max_elevation != float('-inf') else 0
            
            return {
                "name": gpx_path.stem,
                "total_distance": total_distance,
                "elevation_gain": elevation_gain,
                "track_points": track_points,
                "gpx_file_path": file_path
            }
            
        except Exception as e:
            raise Exception(f"Error loading GPX file {file_path}: {str(e)}")
    
    def _calculate_total_distance(self, track_points: List[Dict]) -> float:
        """Calculate total distance from track points."""
        if len(track_points) < 2:
            return 0
        
        total_distance = 0
        for i in range(1, len(track_points)):
            prev_point = track_points[i-1]
            curr_point = track_points[i]
            
            # Simple haversine distance calculation
            distance = self._haversine_distance(
                prev_point["lat"], prev_point["lon"],
                curr_point["lat"], curr_point["lon"]
            )
            total_distance += distance
        
        return total_distance
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using haversine formula."""
        import math
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def create_route(self, name: str, description: str, gpx_file_path: str) -> Dict:
        """Create a new route from GPX data."""
        try:
            # Load GPX data
            gpx_data = await self.load_gpx_file(gpx_file_path)
            
            # Create route record
            db_route = Route(
                name=name,
                description=description,
                total_distance=gpx_data["total_distance"],
                elevation_gain=gpx_data["elevation_gain"],
                gpx_file_path=gpx_file_path
            )
            self.db.add(db_route)
            await self.db.commit()
            await self.db.refresh(db_route)
            
            return {
                "id": db_route.id,
                "name": db_route.name,
                "description": db_route.description,
                "total_distance": db_route.total_distance,
                "elevation_gain": db_route.elevation_gain,
                "gpx_file_path": db_route.gpx_file_path,
                "created_at": db_route.created_at.isoformat() if db_route.created_at else None
            }
            
        except Exception as e:
            raise Exception(f"Error creating route: {str(e)}")
    
    async def delete_route(self, route_id: int) -> Dict:
        """Delete a route."""
        try:
            route = await self.db.get(Route, route_id)
            if not route:
                raise Exception("Route not found")
            
            await self.db.delete(route)
            await self.db.commit()
            
            return {"message": "Route deleted successfully"}
            
        except Exception as e:
            raise Exception(f"Error deleting route: {str(e)}")
    
    async def get_route_sections(self, route_id: int) -> List[Dict]:
        """Get sections for a specific route."""
        try:
            result = await self.db.execute(
                select(Section).where(Section.route_id == route_id)
            )
            sections = result.scalars().all()
            
            return [
                {
                    "id": s.id,
                    "route_id": s.route_id,
                    "gpx_file_path": s.gpx_file_path,
                    "distance_m": s.distance_m,
                    "grade_avg": s.grade_avg,
                    "min_gear": s.min_gear,
                    "est_time_minutes": s.est_time_minutes
                } for s in sections
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching route sections: {str(e)}")