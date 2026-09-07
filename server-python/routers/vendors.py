from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
from database import get_db
from routers.auth import get_current_user
import models, schemas

# Router 级鉴权（8/6 报告 P0-1）
def sync_legacy_contact_fields(obj):
    """同 customers：从 contacts JSON 推导全部四个遗留列（含清空场景）。"""
    first = (obj.contacts or [{}])[0] if obj.contacts else {}
    obj.contact = (first.get("name") or "") if first else ""
    methods = (first.get("contact_methods") or []) if first else []
    by_type = {m.get("type"): m.get("value", "") for m in methods if isinstance(m, dict)}
    obj.phone = by_type.get("电话", "")
    obj.wechat = by_type.get("微信", "")
    obj.email = by_type.get("邮箱", "")


router = APIRouter(prefix="/vendors", tags=["vendors"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=List[schemas.VendorResponse])
def get_vendors(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, keyword: str = None):
    query = db.query(models.Vendor)
    if keyword:
        query = query.filter(models.Vendor.name.ilike(f"%{keyword}%"))
    return query.order_by(models.Vendor.name).offset(skip).limit(limit).all()

@router.post("", response_model=schemas.VendorResponse)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    if not vendor.name or not vendor.name.strip():
        raise HTTPException(status_code=400, detail="外协厂商名称不能为空")
        
    for m in (vendor.contact_methods or []):
        if not m.get('type') or not str(m.get('type')).strip():
            raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
        if not m.get('value') or not str(m.get('value')).strip():
            raise HTTPException(status_code=400, detail="联系方式的值不能为空")
    
    for c in (vendor.contacts or []):
        if not c.name or not c.name.strip():
            raise HTTPException(status_code=400, detail="联系人姓名不能为空")
        for m in (c.contact_methods or []):
            if not m.type or not m.type.strip():
                raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
            if not m.value or not m.value.strip():
                raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    db_vendor = models.Vendor(**vendor.model_dump())
    sync_legacy_contact_fields(db_vendor)
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

    for c in (vendor.contacts or []):
        if not c.name or not c.name.strip():
            raise HTTPException(status_code=400, detail="联系人姓名不能为空")
        for m in (c.contact_methods or []):
            if not m.type or not m.type.strip():
                raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
            if not m.value or not m.value.strip():
                raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    update_data = vendor.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_vendor, key, value)
        
    sync_legacy_contact_fields(db_vendor)
        
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    db_vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # vendor_id 无 FK（Integer 列），删除厂商会让工序上的引用变悬空整数
    step_refs = db.query(models.ProcessStep).filter(models.ProcessStep.vendor_id == vendor_id).count()
    if step_refs:
        raise HTTPException(status_code=400, detail=f"该厂商被 {step_refs} 道工序引用，请先清理工序的外协指向")

    db.delete(db_vendor)
    db.commit()
    return {"ok": True}


# ────────────────────────── 外协总览（T7） ──────────────────────────

@router.get("/outsourcing/overview")
def outsourcing_overview(db: Session = Depends(get_db)):
    """外协生命周期总览：在外协件 + 按厂商成本汇总。

    在外协件 = status='outsourced' 的工序（含订单/产品/厂商/发出天数）；
    成本汇总 = 全部已收回外协工序的 cost 按厂商聚合。"""
    from datetime import datetime

    active_rows = (
        db.query(models.ProcessStep, models.Order, models.Vendor)
        .join(models.ProcessFlow, models.ProcessStep.flow_id == models.ProcessFlow.id)
        .join(models.Order, models.ProcessFlow.order_id == models.Order.id)
        .outerjoin(models.Vendor, models.ProcessStep.vendor_id == models.Vendor.id)
        .filter(models.ProcessStep.status == "outsourced")
        .order_by(models.ProcessStep.sent_date.asc())
        .all()
    )
    today = datetime.now()
    active = [{
        "step_id": s.id,
        "order_id": o.id,
        "order_no": o.order_no,
        "product_name": o.product_name,
        "step_name": s.name,
        "vendor_id": s.vendor_id,
        "vendor_name": v.name if v else "未知厂商",
        "sent_date": str(s.sent_date.date()) if s.sent_date else "",
        "days_out": (today - s.sent_date).days if s.sent_date else 0,
    } for s, o, v in active_rows]

    cost_rows = (
        db.query(
            models.Vendor.id,
            models.Vendor.name,
            func.count(models.ProcessStep.id).label("steps_count"),
            func.coalesce(func.sum(models.ProcessStep.cost), 0).label("total_cost"),
        )
        .join(models.ProcessStep, models.ProcessStep.vendor_id == models.Vendor.id)
        .filter(models.ProcessStep.cost != None)  # noqa: E711
        .group_by(models.Vendor.id, models.Vendor.name)
        .order_by(func.coalesce(func.sum(models.ProcessStep.cost), 0).desc())
        .all()
    )
    costs = [{"vendor_id": r.id, "vendor_name": r.name, "steps_count": r.steps_count,
              "total_cost": float(r.total_cost)} for r in cost_rows]

    return {
        "active": active,
        "active_count": len(active),
        "costs": costs,
        "total_cost": sum(c["total_cost"] for c in costs),
    }
