"""
Media API for AI Campus Companion.
Handles file uploads (images, notes, etc.)
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse

from app.core.auth import get_current_active_user
from app.models import UserInDB
from app.core.database import get_database

router = APIRouter(prefix="/media", tags=["media"])

# Configure media storage
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".txt", ".md"}


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    user: UserInDB = Depends(get_current_active_user)
):
    """
    Upload a media file (image, document, etc.)
    """
    # Validate file extension
    extension = get_file_extension(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        ) from e
    
    # Save file info to database
    db = await get_database()
    file_record = {
        "file_id": file_id,
        "user_id": str(user.id),
        "filename": file.filename,
        "file_path": file_path,
        "content_type": file.content_type,
        "extension": extension,
        "size": len(content),
        "uploaded_at": datetime.utcnow(),
    }
    
    await db.media_files.insert_one(file_record)
    
    # Return the file URL
    return {
        "success": True,
        "file_id": file_id,
        "url": f"/api/media/{file_id}",
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
    }


@router.get("/{file_id}")
async def get_media(file_id: str):
    """
    Get a media file by ID
    """
    db = await get_database()
    file_record = await db.media_files.find_one({"file_id": file_id})
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if file exists
    if not os.path.exists(file_record["file_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_record["file_path"],
        media_type=file_record["content_type"],
        filename=file_record["filename"],
    )
