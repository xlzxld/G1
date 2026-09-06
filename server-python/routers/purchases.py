"""采购单雏形路由（仅管理员，D13）。

状态机：draft → ordered → closed（received_quantity 累计满额自动 closed）。
到货确认经服务层生成 INBOUND 流水（source_type=purchase），支持分批到货。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from routers.auth import get_current_user, verify_admin
from services import inventory_service as svc
import models, schemas

router = APIRouter(prefix="/purchases", tags=["purchases"], dependencies=[Depends(verify_admin)])


def _serialize(po: models.PurchaseOrder) -> dict:
    return {
        "id": po.id, "po_no": po.po_no, "item_id": po.item_id,
        "item_name": po.item.name if po.item else "",
        "item_unit": po.item.unit if po.item else "",
        "vendor_id": po.vendor_id,
        "vendor_name": po.vendor.name if po.vendor else "",
        "quantity": po.quantity, "received_quantity": po.received_quantity or 0,
        "status": po.status, "expected_date": po.expected_date,
        "received_at": po.received_at, "note": po.note or "",
        "created_at": po.created_at,
    }


@router.get("")
def list_purchases(db: Session = Depends(get_db), status: str = None, keyword: str = None):
    """手动序列化：item_name/vendor_name 是 relationship 派生值，response_model 的
    from_attributes 读不到（会静默落空字符串），必须在这里显式组装。"""
    query = db.query(models.PurchaseOrder)
    if status and status.strip():
        query = query.filter(models.PurchaseOrder.status == status.strip())
    if keyword and keyword.strip():
        query = query.join(models.InventoryItem).filter(models.InventoryItem.name.ilike(f"%{keyword.strip()}%"))
    pos = query.order_by(models.PurchaseOrder.created_at.desc()).limit(200).all()
    return [_serialize(po) for po in pos]


@router.post("")
def create_purchase(payload: schemas.PurchaseOrderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="采购数量必须大于 0")
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物料不存在")

    po_no = f"PO-{datetime.now().strftime('%Y%m%d')}-{db.query(models.PurchaseOrder).count() + 1:04d}"
    po = models.PurchaseOrder(
        po_no=po_no, item_id=payload.item_id, vendor_id=payload.vendor_id,
        quantity=payload.quantity, status="draft",
        expected_date=payload.expected_date, note=payload.note or "",
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return _serialize(po)


@router.put("/{po_id}/order")
def order_purchase(po_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    """下单确认：draft → ordered。"""
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="采购单不存在")
    if po.status != "draft":
        raise HTTPException(status_code=400, detail="只有草稿状态可以下单")
    po.status = "ordered"
    db.commit()
    db.refresh(po)
    return _serialize(po)


@router.post("/{po_id}/receive")
def receive_purchase(po_id: int, payload: schemas.PurchaseOrderReceive, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    """到货确认：生成 INBOUND 流水；分批到货，满额自动 closed（幂等守卫防重复入库）。"""
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="采购单不存在")
    if po.status == "draft":
        raise HTTPException(status_code=400, detail="草稿状态请先确认下单再录入到货")
    po = svc.receive_purchase(db, po=po, received_qty=payload.received_quantity,
                              note=payload.note, operator_id=current_user.id)
    return _serialize(po)


@router.delete("/{po_id}")
def delete_purchase(po_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="采购单不存在")
    if po.status != "draft":
        raise HTTPException(status_code=400, detail="已下单的采购单不可删除")
    db.delete(po)
    db.commit()
    return {"ok": True}
