from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.services.gpx import parse_gpx, store_gpx_file
from backend.app.schemas.gpx import RouteCreate, Route as RouteSchema
from backend.app.models import Route
import os

router = APIRouter(prefix="/gpx", tags=["GPX Routes"])

@router.post("/upload", response_model=RouteSchema)
async def upload_gpx_route(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Store GPX file
    gpx_path = await store_gpx_file(file)
    
    # Parse GPX file
    gpx_data = await parse_gpx(gpx_path)
    
    # Create route in database
    route_data = RouteCreate(
        name=file.filename,
        description=f"Uploaded from {file.filename}",
        total_distance=gpx_data['total_distance'],
        elevation_gain=gpx_data['elevation_gain'],
        gpx_file_path=gpx_path
    )
    db_route = Route(**route_data.dict())
    db.add(db_route)
    await db.commit()
    await db.refresh(db_route)
    
    return db_route