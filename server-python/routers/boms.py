"""BOM 用料模板路由——与工艺模板同构；建单自动带料的数据源。

product_type 为受控枚举（D17）：保存时校验非空，下拉候选来自 /boms/product-types
（BOM 与 Order 两端已有类型的并集），禁止自由文本以消除静默失配。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from routers.auth import get_current_user, verify_admin
from services import inventory_service as svc
import models, schemas

router = APIRouter(prefix="/boms", tags=["boms"], dependencies=[Depends(get_current_user)])


def _serialize(bom: models.BOM) -> dict:
    return {
        "id": bom.id, "name": bom.name, "product_type": bom.product_type,
        "version": bom.version, "is_active": bom.is_active, "note": bom.note,
        "created_at": bom.created_at, "updated_at": bom.updated_at,
        "items": [{
            "id": bi.id, "item_id": bi.item_id,
            "quantity_per_set": bi.quantity_per_set, "note": bi.note or "",
            "item_name": bi.item.name if bi.item else "",
            "item_spec": bi.item.spec if bi.item else "",
            "item_unit": bi.item.unit if bi.item else "",
        } for bi in bom.items],
    }


@router.get("")
def list_boms(db: Session = Depends(get_db), keyword: str = None, product_type: str = None):
    query = db.query(models.BOM)
    if keyword and keyword.strip():
        query = query.filter(models.BOM.name.ilike(f"%{keyword.strip()}%"))
    if product_type and product_type.strip():
        query = query.filter(models.BOM.product_type == product_type.strip())
    boms = query.order_by(models.BOM.updated_at.desc()).all()
    return [_serialize(b) for b in boms]


@router.get("/product-types")
def get_product_types(db: Session = Depends(get_db)):
    """受控枚举候选：BOM 与 Order 已用类型的并集（D17 静默失配防护）。"""
    bom_types = [r[0] for r in db.query(models.BOM.product_type).distinct().all() if r[0]]
    order_types = [r[0] for r in db.query(models.Order.product_type).distinct().all() if r[0]]
    return sorted(set(bom_types) | set(order_types))


@router.post("")
def create_bom(payload: schemas.BOMCreate, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    return _upsert_bom(db, payload, current_user)


def _upsert_bom(db: Session, payload: schemas.BOMCreate, current_user: models.User, bom: models.BOM = None) -> dict:
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="模板名称不能为空")
    if not payload.product_type or not payload.product_type.strip():
        raise HTTPException(status_code=400, detail="产品类型不能为空（受控枚举，禁止自由文本）")
    item_map = {i.id: i for i in db.query(models.InventoryItem).filter(
        models.InventoryItem.id.in_([x.item_id for x in payload.items] or [0])).all()}
    for x in payload.items:
        if x.item_id not in item_map:
            raise HTTPException(status_code=400, detail=f"物料 {x.item_id} 不存在")
        if x.quantity_per_set <= 0:
            raise HTTPException(status_code=400, detail="单套用量必须大于 0")

    if bom is None:
        bom = models.BOM(name=payload.name.strip(), product_type=payload.product_type.strip())
        db.add(bom)
    else:
        bom.name = payload.name.strip()
        bom.product_type = payload.product_type.strip()
    bom.note = payload.note or ""
    bom.is_active = 1 if payload.is_active else 0
    db.flush()

    db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom.id).delete()
    for x in payload.items:
        db.add(models.BOMItem(bom_id=bom.id, item_id=x.item_id,
                              quantity_per_set=x.quantity_per_set, note=x.note or ""))
    db.commit()
    db.refresh(bom)
    return _serialize(bom)


@router.put("/{bom_id}")
def update_bom(bom_id: int, payload: schemas.BOMCreate, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 模板不存在")
    return _upsert_bom(db, payload, current_user, bom)


@router.delete("/{bom_id}")
def delete_bom(bom_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 模板不存在")
    db.delete(bom)
    db.commit()
    return {"ok": True}


@router.post("/apply/{order_id}")
def apply_bom_to_order(order_id: int, payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """建单自动带料：按模板逐项预留；失效/缺料项跳过并写入警告清单（不静默失败）。"""
    bom_id = payload.get("bom_id")
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id, models.BOM.is_active == 1).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 模板不存在或已停用")
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "completed":
        raise HTTPException(status_code=400, detail="订单已完成，不能添加用料")

    reserved, warnings = 0, []
    for bi in bom.items:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == bi.item_id).first()
        if not item or item.is_archived:
            warnings.append(f"「{bi.item.name if bi.item else bi.item_id}」已失效，已跳过")
            continue
        available = (item.total or 0) - (item.reserved or 0)
        qty = min(bi.quantity_per_set, max(available, 0))
        if qty <= 0:
            warnings.append(f"「{item.name}」可用不足（需 {bi.quantity_per_set}，可用 {available}），请手动处理")
            continue
        if qty < bi.quantity_per_set:
            warnings.append(f"「{item.name}」库存不足，仅预留 {qty}/{bi.quantity_per_set}")
        try:
            svc.reserve_for_order(db, item_id=item.id, order_id=order_id, quantity=qty,
                                  operator_id=current_user.id)
            reserved += 1
        except HTTPException as e:
            warnings.append(f"「{item.name}」预留失败：{e.detail}")
    return {"ok": True, "reserved_items": reserved, "total_items": len(bom.items), "warnings": warnings}
