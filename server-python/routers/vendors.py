from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.get("", response_model=List[schemas.VendorResponse])
def get_vendors(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, keyword: str = None):
    query = db.query(models.Vendor)
    if keyword:
        query = query.filter(models.Vendor.name.ilike(f"%{keyword}%"))
    return query.order_by(models.Vendor.id.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=schemas.VendorResponse)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    if not vendor.name or not vendor.name.strip():
        raise HTTPException(status_code=400, detail="外协厂商名称不能为空")
        
    for m in (vendor.contact_methods or []):
        if not m.get('type') or not str(m.get('type')).strip():
            raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
        if not m.get('value') or not str(m.get('value')).strip():
            raise HTTPException(status_code=400, detail="联系方式的值不能为空")
    
    db_vendor = models.Vendor(**vendor.model_dump())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

@router.put("/{vendor_id}", response_model=schemas.VendorResponse)
def update_vendor(vendor_id: int, vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    db_vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
        
    if not vendor.name or not vendor.name.strip():
        raise HTTPException(status_code=400, detail="外协厂商名称不能为空")
        
    for m in (vendor.contact_methods or []):
        if not m.get('type') or not str(m.get('type')).strip():
            raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
        if not m.get('value') or not str(m.get('value')).strip():
            raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    update_data = vendor.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_vendor, key, value)
        
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    db_vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
        
    db.delete(db_vendor)
    db.commit()
    return {"ok": True}
