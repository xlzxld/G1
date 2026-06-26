from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
import os

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("", response_model=schemas.DocumentResponse)
async def upload_document(
    order_id: int = Form(...),
    title: str = Form(""),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # This integrates with the order detail page as planned
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    db_doc = models.Document(
        order_id=order_id,
        filename=file.filename,
        original_name=file.filename,
        file_path=file_path,
        title=title,
        description=description,
        file_size=len(content)
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc
