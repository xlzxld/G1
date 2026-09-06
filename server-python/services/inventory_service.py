"""库存服务层——库存写入的唯一入口。

铁律（CEO 计划 D10）：InventoryItem.total / reserved 只能由本模块刷新，
任何 router 不得直接写这两列；"手改数字"不存在，一切变更必须留下流水。

事务模型（eng 评审修正）：
    with_for_update 锁定物料行 → 插入 StockMovement → 事务内刷新缓存列 → commit；
    预警评估在 commit 之后执行——通知引擎（trigger_notification_rules）内部自带
    commit，绝不能进入本事务，否则行锁提前释放、流水无法整体回滚。
    阈值穿越判定以 before/after 可用量为参数（不再重查），同一低水位下
    的连续变动不会重复告警。

领料-预留转换矩阵（外部声音 #2）：
    领料带订单   → 同事务消耗该订单的预留行（部分领料按实际数消耗）
    超领/无预留  → 允许：全额记 OUTBOUND，预留只扣实际存在的部分
    退料带订单   → RETURN 入账；订单未完成时按数量恢复预留
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

import models

MOVEMENT_TYPES = {"OPENING", "INBOUND", "OUTBOUND", "RETURN", "ADJUSTMENT"}


# ────────────────────────── 内部：缓存列刷新与预警 ──────────────────────────

def _apply_movement(db: Session, item: models.InventoryItem, mtype: str,
                    signed_qty: int, source_type: str, source_id,
                    batch_no: str, unit_cost, note: str, operator_id) -> models.StockMovement:
    """在已锁定物料行上插入流水并增量刷新 total 缓存列。调用方负责事务提交。"""
    if mtype not in MOVEMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"未知的流水类型 {mtype}")
    new_total = (item.total or 0) + signed_qty
    if new_total < 0:
        raise HTTPException(status_code=400, detail="库存不足：操作后总量为负")
    mv = models.StockMovement(
        item_id=item.id,
        type=mtype,
        source_type=source_type,
        source_id=source_id,
        batch_no=batch_no or "",
        unit_cost=unit_cost,
        quantity=signed_qty,
        balance_after=new_total,
        operator_id=operator_id,
        note=note or "",
    )
    db.add(mv)
    item.total = new_total
    return mv


def evaluate_threshold_crossing(db: Session, item_id: int,
                                before_available: int, after_available: int) -> None:
    """提交后调用：仅在可用量向下穿越 min_stock 时触发一次预警（D19 防轰炸）。"""
    try:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
        if not item:
            return
        if before_available > item.min_stock and after_available <= item.min_stock:
            from routers.notifications import trigger_notification_rules
            trigger_notification_rules("inventory_alert", {
                "id": item.id,
                "item_id": item.id,
                "name": item.name,
                "spec": item.spec or "",
                "total": item.total,
                "reserved": item.reserved,
                "available": after_available,
                "min_stock": item.min_stock,
            }, db)
    except Exception as e:
        # 通知是旁路：失败记日志，绝不影响已提交的库存事务
        import logging
        logging.getLogger("inventory").warning(
            "inventory alert evaluate failed item=%s %s -> %s: %s",
            item_id, before_available, after_available, e
        )


def _lock_item(db: Session, item_id: int) -> models.InventoryItem:
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id
    ).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="物料不存在")
    if item.is_archived:
        raise HTTPException(status_code=400, detail="物料已归档，不能进行库存操作")
    return item


# ────────────────────────── 物料生命周期 ──────────────────────────

def create_item_with_opening(db: Session, *, name, spec="", category="", location="",
                             unit="件", min_stock=5, opening_qty=0, operator_id=None) -> models.InventoryItem:
    if not name or not str(name).strip():
        raise HTTPException(status_code=400, detail="物料名称不能为空")
    if opening_qty < 0:
        raise HTTPException(status_code=400, detail="期初数量不能小于0")
    item = models.InventoryItem(
        name=name.strip(), spec=spec or "", category=category or "",
        location=location or "", unit=unit or "件", min_stock=min_stock or 0,
        total=0, reserved=0,
    )
    db.add(item)
    db.flush()  # 取 item.id 供流水外键
    if opening_qty > 0:
        _apply_movement(db, item, "OPENING", opening_qty, "manual", None, "", None, "建物料期初", operator_id)
    db.commit()
    db.refresh(item)
    return item


def archive_item(db: Session, item_id: int) -> models.InventoryItem:
    """归档守卫：未完结采购单 / 有效预留 / BOM 引用存在时拒绝归档——
    否则 PO 永远无法到货（_lock_item 拒绝已归档物料），形成死锁（ENG-10/PROD-4）。"""
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物料不存在")
    open_po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.item_id == item_id,
        models.PurchaseOrder.status.in_(["draft", "ordered"]),
    ).count()
    if open_po:
        raise HTTPException(status_code=400, detail="该物料存在未完结采购单，请先取消/完结采购单再归档")
    active_res = db.query(models.InventoryReservation).filter(
        models.InventoryReservation.item_id == item_id
    ).count()
    if active_res:
        raise HTTPException(status_code=400, detail="该物料存在订单预留，请先释放预留再归档")
    item.is_archived = 1
    db.commit()
    db.refresh(item)
    return item


def unarchive_item(db: Session, item_id: int) -> models.InventoryItem:
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物料不存在")
    item.is_archived = 0
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> None:
    """删除守卫：存在流水/BOM 引用/预留/采购单的物料禁止 DELETE（D19，保护审计链）。"""
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物料不存在")
    if db.query(models.StockMovement).filter(models.StockMovement.item_id == item_id).count() > 0:
        raise HTTPException(status_code=400, detail="该物料存在库存流水，禁止删除；请使用归档保留审计链")
    if db.query(models.BOMItem).filter(models.BOMItem.item_id == item_id).count() > 0:
        raise HTTPException(status_code=400, detail="该物料被 BOM 用料模板引用，禁止删除；请使用归档")
    if db.query(models.InventoryReservation).filter(models.InventoryReservation.item_id == item_id).count() > 0:
        raise HTTPException(status_code=400, detail="该物料存在订单预留，请先释放预留")
    if db.query(models.PurchaseOrder).filter(models.PurchaseOrder.item_id == item_id).count() > 0:
        raise HTTPException(status_code=400, detail="该物料存在采购单，禁止删除；请使用归档")
    db.delete(item)
    db.commit()


# ────────────────────────── 预留 ──────────────────────────

def reserve_for_order(db: Session, *, item_id: int, order_id: int, quantity: int,
                      operator_id=None) -> models.InventoryItem:
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="预留数量必须大于0")
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在（8/6 报告数据完整性 #7）")

    item = _lock_item(db, item_id)
    available = (item.total or 0) - (item.reserved or 0)
    if quantity > available:
        raise HTTPException(status_code=400, detail=f"可用库存不足：当前可用 {available}")

    row = db.query(models.InventoryReservation).filter(
        models.InventoryReservation.order_id == order_id,
        models.InventoryReservation.item_id == item_id,
    ).first()
    if row:
        row.quantity = (row.quantity or 0) + quantity
    else:
        db.add(models.InventoryReservation(order_id=order_id, item_id=item_id, quantity=quantity))
    item.reserved = (item.reserved or 0) + quantity

    before_available = available
    after_available = available - quantity
    db.commit()
    evaluate_threshold_crossing(db, item_id, before_available, after_available)
    return item


def release_reservation(db: Session, reservation: models.InventoryReservation) -> models.InventoryItem:
    """删除一条预留并同步回退 reserved 缓存列（删订单/删用料共用）。"""
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == reservation.item_id
    ).with_for_update().first()
    if item:
        item.reserved = max(0, (item.reserved or 0) - (reservation.quantity or 0))
    db.delete(reservation)
    return item


def release_order_reservations(db: Session, order: models.Order) -> None:
    """订单删除前调用：释放全部预留并回退 reserved（8/6 报告数据完整性 #1 修复）。"""
    reservations = db.query(models.InventoryReservation).filter(
        models.InventoryReservation.order_id == order.id
    ).all()
    for res in reservations:
        release_reservation(db, res)


def release_completed_order_reservations(db: Session, order: models.Order) -> int:
    """已完成订单释放剩余预留（PROD-2：驾驶舱"已完成未领料"的解决动作）。
    返回释放的预留条数。仅允许对 completed 订单调用。"""
    if order.status != "completed":
        raise HTTPException(status_code=400, detail="仅已完成的订单可以释放剩余预留")
    reservations = db.query(models.InventoryReservation).filter(
        models.InventoryReservation.order_id == order.id
    ).all()
    for res in reservations:
        release_reservation(db, res)
    db.commit()
    return len(reservations)


# ────────────────────────── 出入库 / 领退料 / 盘点 ──────────────────────────

def pick_material(db: Session, *, item_id: int, order_id, quantity: int,
                  batch_no: str = "", note: str = "", operator_id=None) -> dict:
    """领料：OUTBOUND 流水（唯一减 total 的业务路径，D16）。

    带订单时优先消耗该订单的预留；超出预留部分照常出库（超领允许）。
    返回预警上下文，调用方在 commit 后触发 evaluate_threshold_crossing。
    """
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="领料数量必须大于0")
    order = None
    if order_id:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

    item = _lock_item(db, item_id)
    before_available = (item.total or 0) - (item.reserved or 0)

    consumed_reserved = 0
    if order:
        res = db.query(models.InventoryReservation).filter(
            models.InventoryReservation.order_id == order.id,
            models.InventoryReservation.item_id == item_id,
        ).first()
        if res and (res.quantity or 0) > 0:
            consumed_reserved = min(quantity, res.quantity)
            res.quantity -= consumed_reserved
            if res.quantity <= 0:
                db.delete(res)
        item.reserved = max(0, (item.reserved or 0) - consumed_reserved)

    _apply_movement(db, item, "OUTBOUND", -quantity,
                    "order" if order else "manual", order.id if order else None,
                    batch_no, None, note or (f"订单 {order.order_no} 领料" if order else "领料"),
                    operator_id)
    after_available = (item.total or 0) - (item.reserved or 0)
    db.commit()
    evaluate_threshold_crossing(db, item_id, before_available, after_available)
    return {"item": item, "picked_from_reserved": consumed_reserved}


def return_material(db: Session, *, item_id: int, order_id=None, quantity: int,
                    batch_no: str = "", note: str = "", operator_id=None) -> dict:
    """退料：RETURN 流水入账；订单未完成时按数量恢复该订单预留。"""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="退料数量必须大于0")
    order = None
    if order_id:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

    item = _lock_item(db, item_id)
    before_available = (item.total or 0) - (item.reserved or 0)

    _apply_movement(db, item, "RETURN", quantity,
                    "order" if order else "manual", order.id if order else None,
                    batch_no, None, note or "退料入库", operator_id)

    if order and order.status != "completed":
        res = db.query(models.InventoryReservation).filter(
            models.InventoryReservation.order_id == order.id,
            models.InventoryReservation.item_id == item_id,
        ).first()
        if res:
            res.quantity = (res.quantity or 0) + quantity
        else:
            db.add(models.InventoryReservation(order_id=order.id, item_id=item_id, quantity=quantity))
        item.reserved = (item.reserved or 0) + quantity

    after_available = (item.total or 0) - (item.reserved or 0)
    db.commit()
    evaluate_threshold_crossing(db, item_id, before_available, after_available)
    return {"item": item}


def inbound(db: Session, *, item_id: int, quantity: int, batch_no: str = "",
            unit_cost=None, note: str = "", source_type: str = "manual",
            source_id=None, operator_id=None, commit: bool = True) -> dict:
    """入库（含采购到货：source_type=purchase）。commit=False 供调用方组合进更大事务。"""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="入库数量必须大于0")
    item = _lock_item(db, item_id)
    before_available = (item.total or 0) - (item.reserved or 0)
    _apply_movement(db, item, "INBOUND", quantity, source_type, source_id,
                    batch_no, unit_cost, note or "入库", operator_id)
    after_available = (item.total or 0) - (item.reserved or 0)
    if commit:
        db.commit()
        evaluate_threshold_crossing(db, item_id, before_available, after_available)
    return {"item": item}


def stocktake_adjust(db: Session, *, item_id: int, counted_qty: int,
                     note: str = "", operator_id=None) -> dict:
    """盘点：录入实盘数，系统计算差额生成 ADJUSTMENT 流水（无审批流）。"""
    item = _lock_item(db, item_id)
    if counted_qty < 0:
        raise HTTPException(status_code=400, detail="实盘数量不能为负")
    if counted_qty < (item.reserved or 0):
        raise HTTPException(
            status_code=400,
            detail=f"实盘数量小于已预留量（{item.reserved}）——请先领料或释放预留，再盘点",
        )
    before_available = (item.total or 0) - (item.reserved or 0)
    delta = counted_qty - (item.total or 0)
    if delta == 0:
        db.commit()
        return {"item": item, "delta": 0}
    _apply_movement(db, item, "ADJUSTMENT", delta, "stocktake", None,
                    "", None, note or f"盘点调整（实盘 {counted_qty}）", operator_id)
    after_available = (item.total or 0) - (item.reserved or 0)
    db.commit()
    evaluate_threshold_crossing(db, item_id, before_available, after_available)
    return {"item": item, "delta": delta}


# ────────────────────────── 采购 ──────────────────────────

def receive_purchase(db: Session, *, po: models.PurchaseOrder, received_qty: int,
                     batch_no: str = "", note: str = "", operator_id=None) -> models.PurchaseOrder:
    """到货确认：PO 行锁 + 流水与 PO 状态同一事务（ENG-4：防并发超收/中途失败双重入库）。
    支持分批到货；累计满额后状态置 closed。"""
    if received_qty <= 0:
        raise HTTPException(status_code=400, detail="到货数量必须大于0")

    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po.id).with_for_update().first()
    if po.status == "closed":
        raise HTTPException(status_code=400, detail="采购单已完结，不能重复入库")
    if po.status == "cancelled":
        raise HTTPException(status_code=400, detail="采购单已取消，不能入库")
    if po.status == "draft":
        raise HTTPException(status_code=400, detail="草稿状态请先确认下单再录入到货")
    remaining = po.quantity - (po.received_quantity or 0)
    if received_qty > remaining:
        raise HTTPException(status_code=400, detail=f"到货数量超过未收数量（剩余 {remaining}）")

    item = _lock_item(db, po.item_id)
    before_available = (item.total or 0) - (item.reserved or 0)
    _apply_movement(db, item, "INBOUND", received_qty, "purchase", po.id,
                    batch_no, None, note or f"采购单 {po.po_no} 到货", operator_id)
    po.received_quantity = (po.received_quantity or 0) + received_qty
    po.received_at = po.received_at or func.now()
    if po.received_quantity >= po.quantity:
        po.status = "closed"
    after_available = (item.total or 0) - (item.reserved or 0)
    db.commit()
    db.refresh(po)
    evaluate_threshold_crossing(db, po.item_id, before_available, after_available)
    return po


def cancel_purchase(db: Session, *, po: models.PurchaseOrder, note: str = "", operator_id=None) -> models.PurchaseOrder:
    """取消采购单（PROD-4：供应商无法交付时的出口）。仅 draft/ordered 可取消。"""
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po.id).with_for_update().first()
    if po.status not in ("draft", "ordered"):
        raise HTTPException(status_code=400, detail="仅草稿/已下单状态可以取消")
    po.status = "cancelled"
    if note:
        po.note = f"{(po.note or '')} | 取消：{note}".strip(" |")
    db.commit()
    db.refresh(po)
    return po


# ────────────────────────── 查询辅助 ──────────────────────────

def item_movements(db: Session, item_id: int, limit: int = 50):
    return (
        db.query(models.StockMovement)
        .filter(models.StockMovement.item_id == item_id)
        .order_by(models.StockMovement.created_at.desc(), models.StockMovement.id.desc())
        .limit(limit)
        .all()
    )


def replenish_list(db: Session):
    """补货意向清单：可用量低于安全库存的未归档物料（驾驶舱/采购页共用）。"""
    return (
        db.query(models.InventoryItem)
        .filter(
            models.InventoryItem.is_archived == 0,
            (models.InventoryItem.total - models.InventoryItem.reserved) <= models.InventoryItem.min_stock,
        )
        .order_by((models.InventoryItem.total - models.InventoryItem.reserved).asc())
        .all()
    )


def verify_ledger_consistency(db: Session, item_id: int) -> dict:
    """运维重算脚本用：校验单物料 total 缓存 = SUM(流水)，返回差额。"""
    ledger_sum = (
        db.query(func.coalesce(func.sum(models.StockMovement.quantity), 0))
        .filter(models.StockMovement.item_id == item_id)
        .scalar()
    )
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    return {
        "item_id": item_id,
        "cache_total": item.total if item else None,
        "ledger_sum": int(ledger_sum or 0),
        "drift": (item.total - int(ledger_sum)) if item else None,
    }
