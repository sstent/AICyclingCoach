from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from backend.app.services.import_service import ImportService
import logging
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/import/validate")
async def validate_import(
    file: UploadFile = File(...),
):
    try:
        importer = ImportService()
        validation_result = await importer.validate_import(file)
        return JSONResponse(content=validation_result)
    except Exception as e:
        logger.error(f"Import validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/import")
async def execute_import(
    file: UploadFile = File(...),
    conflict_resolution: str = Form("skip"),
    resolutions: Optional[str] = Form(None),
):
    try:
        importer = ImportService()
        import_result = await importer.execute_import(
            file,
            conflict_resolution,
            resolutions
        )
        return JSONResponse(content=import_result)
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e