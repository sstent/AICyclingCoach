import os
import uuid
import logging
from fastapi import UploadFile, HTTPException
import gpxpy
from backend.app.config import settings

logger = logging.getLogger(__name__)

async def store_gpx_file(file: UploadFile) -> str:
    """Store uploaded GPX file and return path"""
    try:
        file_ext = os.path.splitext(file.filename)[1]
        if file_ext.lower() != '.gpx':
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(settings.GPX_STORAGE_PATH, file_name)
        
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        return file_path
    except Exception as e:
        logger.error(f"Error storing GPX file: {e}")
        raise HTTPException(status_code=500, detail="Error storing file")

async def parse_gpx(file_path: str) -> dict:
    """Parse GPX file and extract key metrics"""
    try:
        with open(file_path, 'r') as f:
            gpx = gpxpy.parse(f)
            
        total_distance = 0.0
        elevation_gain = 0.0
        points = []
        
        for track in gpx.tracks:
            for segment in track.segments:
                total_distance += segment.length_3d()
                for i in range(1, len(segment.points)):
                    elevation_gain += max(0, segment.points[i].elevation - segment.points[i-1].elevation)
                
                points = [{
                    'lat': point.latitude,
                    'lon': point.longitude,
                    'ele': point.elevation,
                    'time': point.time.isoformat() if point.time else None
                } for point in segment.points]
        
        return {
            'total_distance': total_distance,
            'elevation_gain': elevation_gain,
            'points': points
        }
    except Exception as e:
        logger.error(f"Error parsing GPX file: {e}")
        raise HTTPException(status_code=500, detail="Error parsing GPX file")