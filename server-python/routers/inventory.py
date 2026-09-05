"""库存路由 V3——全部写操作经 services/inventory_service.py（单一写入口）。

Router 级鉴权：本前缀下所有端点要求登录（8/6 报告 P0-1）。
敏感操作两档分级（D13）：物料主数据增删改/盘点/归档/删除要求 is_admin（verify_admin）；
领料/退料/入库/预留等日常操作仅需登录身份。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from routers.auth import get_current_user, verify_admin
from services import inventory_service as svc
import models, schemas

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(get_current_user)])


@router.get("")
def get_inventory_items(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 100,
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="按分类过滤"),
    include_archived: int = Query(0, description="是否包含已归档物料"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向，asc/desc"),
):
    # sort_by 白名单化（eng 评审：getattr 任意属性访问加固）
    sortable = {"name", "spec", "category", "total", "reserved", "unit", "min_stock", "created_at", "updated_at"}
    query = db.query(models.InventoryItem)
    if not include_archived:
        query = query.filter(models.InventoryItem.is_archived == 0)

    if keyword and keyword.strip():
        from sqlalchemy import or_
        kw = f"%{keyword.strip()}%"
        query = query.filter(or_(
            models.InventoryItem.name.ilike(kw),
            models.InventoryItem.spec.ilike(kw),
            models.InventoryItem.category.ilike(kw),
        ))
    if category and category.strip():
        query = query.filter(models.InventoryItem.category == category.strip())

    from sqlalchemy import desc, asc
    if sort_by in sortable:
        column = getattr(models.InventoryItem, sort_by)
        query = query.order_by(asc(column) if sort_order == "asc" else desc(column))
    else:
        query = query.order_by(desc(models.InventoryItem.created_at))

    total = query.count()
    # limit > 1000 视为一次性全量拉取（前端翻页定位用），直接返回数组保持兼容
    if limit > 1000:
        return query.offset(0).limit(limit).all()
    data = query.offset((page - 1) * limit).limit(limit).all()
    return {"data": data, "total": total}


@router.get("/replenish", response_model=List[schemas.InventoryItemResponse])
def get_replenish_list(db: Session = Depends(get_db)):
    """补货意向清单：可用量 <= 安全库存的未归档物料（驾驶舱/采购页共用）。"""
    return svc.replenish_list(db)


@router.get("/{item_id}", response_model=schemas.InventoryItemResponse)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    return item


@router.get("/{item_id}/movements", response_model=List[schemas.StockMovementResponse])
def get_item_movements(item_id: int, db: Session = Depends(get_db), limit: int = Query(50, le=200)):
    """物料流水历史（谁/何时/动多少/余多少）。"""
    return svc.item_movements(db, item_id, limit)


@router.post("/{item_id}/movements")
def create_movement(
    item_id: int,
    req: schemas.MovementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """入库/领料/退料/盘点统一入口（quantity 一律为正，方向由 type 决定）。"""
    if req.type not in {"INBOUND", "OUTBOUND", "RETURN", "ADJUSTMENT"}:
        raise HTTPException(status_code=400, detail="type 必须为 INBOUND / OUTBOUND / RETURN / ADJUSTMENT")

    common = dict(batch_no=req.batch_no, note=req.note, operator_id=current_user.id)
    if req.type == "INBOUND":
        result = svc.inbound(db, item_id=item_id, quantity=req.quantity,
                             unit_cost=req.unit_cost, **common)
    elif req.type == "OUTBOUND":
        result = svc.pick_material(db, item_id=item_id, order_id=req.order_id,
                                   quantity=req.quantity, **common)
    elif req.type == "RETURN":
        result = svc.return_material(db, item_id=item_id, order_id=req.order_id,
                                     quantity=req.quantity, **common)
    else:  # ADJUSTMENT
        result = svc.stocktake_adjust(db, item_id=item_id, counted_qty=req.quantity,
                                      operator_id=current_user.id, note=req.note)

    item = result["item"]
    return {
        "ok": True,
        "item_id": item.id,
        "total": item.total,
        "reserved": item.reserved,
        "available": (item.total or 0) - (item.reserved or 0),
    }


@router.post("/reserve")
def reserve_inventory(req: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """订单预留（兼容原请求体 {item_id, order_id, quantity}）。"""
    try:
        item_id = int(req.get("item_id"))
        order_id = int(req.get("order_id"))
        quantity = int(req.get("quantity"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="item_id / order_id / quantity 必须为整数")
    item = svc.reserve_for_order(db, item_id=item_id, order_id=order_id, quantity=quantity,
                                 operator_id=current_user.id)
    return {"ok": True, "available": (item.total or 0) - (item.reserved or 0)}


@router.post("", response_model=schemas.InventoryItemResponse)
def create_inventory_item(
    item: schemas.InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_admin),
):
    """新建物料（管理员）：期初数量经 OPENING 流水入账，不再直接写 total。"""
    return svc.create_item_with_opening(
        db,
        name=item.name, spec=item.spec, category=item.category, location=item.location,
        unit=item.unit, min_stock=item.min_stock, opening_qty=item.total,
        operator_id=current_user.id,
    )


@router.put("/{item_id}", response_model=schemas.InventoryItemResponse)
def update_inventory_item(
    item_id: int,
    item: schemas.InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_admin),
):
    """编辑物料主数据（管理员）。total 不再接受直接修改——数量变更走出入库/盘点。"""
    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="物料不存在")
    if not item.name or not item.name.strip():
        raise HTTPException(status_code=400, detail="物料名称不能为空")

    db_item.name = item.name.strip()
    db_item.spec = item.spec or ""
    db_item.category = item.category or ""
    db_item.location = item.location or ""
    db_item.unit = item.unit or "件"
    db_item.min_stock = item.min_stock or 0
    db.commit()
    db.refresh(db_item)
    return db_item


@router.post("/{item_id}/archive", response_model=schemas.InventoryItemResponse)
def archive_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_admin),
):
    """归档（管理员）：有流水的物料用归档代替删除。"""
    return svc.archive_item(db, item_id)


@router.delete("/{item_id}")
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_admin),
):
    svc.delete_item(db, item_id)
    return {"ok": True}


@router.get("/{item_id}/locate")
def locate_inventory_page(
    item_id: int,
    db: Session = Depends(get_db),
    limit: int = 20,
    keyword: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    query = db.query(models.InventoryItem).filter(models.InventoryItem.is_archived == 0)
    if keyword:
        query = query.filter(models.InventoryItem.name.ilike(f"%{keyword}%"))

    target_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not target_item:
        raise HTTPException(status_code=404, detail="物料不存在")

    from sqlalchemy import desc, asc
    if sort_by and hasattr(models.InventoryItem, sort_by):
        column = getattr(models.InventoryItem, sort_by)
        query = query.order_by(asc(column) if sort_order == 'asc' else desc(column))
    else:
        query = query.order_by(desc(models.InventoryItem.created_at))

    all_ids = [r[0] for r in query.with_entities(models.InventoryItem.id).all()]
    try:
        idx = all_ids.index(item_id)
        return {"page": (idx // limit) + 1}
    except ValueError:
        return {"page": 1}
