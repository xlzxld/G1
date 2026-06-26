from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("", response_model=List[schemas.InventoryItemResponse])
def get_inventory_items(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    items = db.query(models.InventoryItem).offset(skip).limit(limit).all()
    return items

@router.get("/{item_id}", response_model=schemas.InventoryItemResponse)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("", response_model=schemas.InventoryItemResponse)
def create_inventory_item(item: schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    if not item.name or not item.name.strip():
        raise HTTPException(status_code=400, detail="物料名称不能为空")
    if item.total < 0:
        raise HTTPException(status_code=400, detail="总量不能小于0")
        
    db_item = models.InventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{item_id}", response_model=schemas.InventoryItemResponse)
def update_inventory_item(item_id: int, item: schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if not item.name or not item.name.strip():
        raise HTTPException(status_code=400, detail="物料名称不能为空")
    if item.total < 0:
        raise HTTPException(status_code=400, detail="总量不能小于0")
        
    update_data = item.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"ok": True}

from pydantic import BaseModel
class ReserveRequest(BaseModel):
    item_id: int
    order_id: int
    quantity: int

@router.post("/reserve")
def reserve_inventory(req: ReserveRequest, db: Session = Depends(get_db)):
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="预留数量必须大于0")
        
    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == req.item_id).with_for_update().first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    available = db_item.total - db_item.reserved
    if req.quantity > available:
        raise HTTPException(status_code=400, detail="可用库存不足")
        
    db_item.reserved += req.quantity
    
    # Also record the reservation
    record = models.InventoryReservation(
        item_id=req.item_id,
        order_id=req.order_id,
        quantity=req.quantity
    )
    db.add(record)
    
    db.commit()
    return {"ok": True}
