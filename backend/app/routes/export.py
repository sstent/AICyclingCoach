from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from app.services.export_service import ExportService
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/export")
async def export_data(
    types: str = Query(..., description="Comma-separated list of data types to export"),
    format: str = Query('json', description="Export format (json, zip, gpx)")
):
    valid_types = {'routes', 'rules', 'plans'}
    requested_types = set(types.split(','))
    
    # Validate requested types
    if not requested_types.issubset(valid_types):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid export types. Valid types are: {', '.join(valid_types)}"
        )
    
    try:
        exporter = ExportService()
        export_path = await exporter.create_export(
            export_types=list(requested_types),
            export_format=format
        )
        
        return FileResponse(
            export_path,
            media_type="application/zip" if format == 'zip' else "application/json",
            filename=f"export_{'_'.join(requested_types)}.{format}"
        )
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed") from e