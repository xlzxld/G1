from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("")
def get_inventory_items(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 100,
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向，asc/desc")
):
    query = db.query(models.InventoryItem)
    
    if keyword and keyword.strip():
        from sqlalchemy import or_
        query = query.filter(
            or_(
                models.InventoryItem.name.ilike(f"%{keyword}%"),
                models.InventoryItem.spec.ilike(f"%{keyword}%")
            )
        )
        
    from sqlalchemy import desc, asc
    if sort_by and hasattr(models.InventoryItem, sort_by):
        column = getattr(models.InventoryItem, sort_by)
        if sort_order == "asc":
            query = query.order_by(asc(column))
        else:
            query = query.order_by(desc(column))
    else:
        query = query.order_by(desc(models.InventoryItem.created_at))

    total = query.count()
    # limit > 1000 视为一次性全量拉取（前端翻页定位时用），直接返回数组保持兼容
    if limit > 1000:
        return query.offset(0).limit(limit).all()
    skip = (page - 1) * limit
    data = query.offset(skip).limit(limit).all()
    return {"data": data, "total": total}

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
    check_inventory_alert(db_item.id, db)
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
    check_inventory_alert(db_item.id, db)
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
    check_inventory_alert(req.item_id, db)
    return {"ok": True}

# ────────────────────────── 辅助警报校验 ──────────────────────────

def check_inventory_alert(item_id: int, db: Session):
    try:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
        if item:
            available = item.total - item.reserved
            if available <= item.alert_threshold:
                from routers.notifications import trigger_notification_rules
                context = {
                    "id": item.id,
                    "name": item.name,
                    "spec": item.spec or "",
                    "total": item.total,
                    "reserved": item.reserved,
                    "available": available,
                    "alert_threshold": item.alert_threshold
                }
                trigger_notification_rules("inventory_alert", context, db)
    except Exception as e:
        print(f"Check inventory alert failed: {e}")
