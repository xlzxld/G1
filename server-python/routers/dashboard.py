"""驾驶舱聚合端点——风险优先（缺料/逾期/停滞/已完成未领料）+ 趋势。

口径统一：库存预警 = available = total - reserved <= min_stock（与库存页一致）。
前端 60s 轮询本端点（SSE 多 worker 修复延后，见 TODOS.md T2）。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, date, timedelta
import models
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])

STALLED_DAYS = 3          # 工序停滞判定：in_progress 超过 3 天
DUE_SOON_DAYS = 3         # 交期临近判定
TREND_DAYS = 14           # 趋势窗口


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()

    # ── 指标带 ──
    today_pending = db.query(models.Order).filter(models.Order.status == "paused").count()
    in_progress = db.query(models.Order).filter(models.Order.status == "in_progress").count()
    inventory_alert = db.query(models.InventoryItem).filter(
        models.InventoryItem.is_archived == 0,
        (models.InventoryItem.total - models.InventoryItem.reserved) <= models.InventoryItem.min_stock
    ).count()
    today_done = db.query(models.Order).filter(
        models.Order.status == "completed",
        cast(models.Order.updated_at, Date) == today
    ).count()

    recent_customers = db.query(models.Customer).order_by(models.Customer.created_at.desc()).limit(5).all()

    # ── 风险 1：逾期订单（未完成且交期已过） ──
    overdue = db.query(models.Order).filter(
        models.Order.status != "completed",
        models.Order.shipment_date != None,  # noqa: E711
        models.Order.shipment_date < today
    ).order_by(models.Order.shipment_date.asc()).all()
    overdue_items = [{
        "id": o.id, "order_no": o.order_no, "product_name": o.product_name,
        "shipment_date": str(o.shipment_date.date() if o.shipment_date else ""),
        "days": (today - o.shipment_date.date()).days,
    } for o in overdue[:8]]

    # ── 风险 2：交期临近（3 天内） ──
    due_soon = db.query(models.Order).filter(
        models.Order.status != "completed",
        models.Order.shipment_date != None,  # noqa: E711
        models.Order.shipment_date >= today,
        models.Order.shipment_date <= today + timedelta(days=DUE_SOON_DAYS)
    ).order_by(models.Order.shipment_date.asc()).all()
    due_soon_items = [{
        "id": o.id, "order_no": o.order_no, "product_name": o.product_name,
        "days": (o.shipment_date.date() - today).days,
    } for o in due_soon[:8]]

    # ── 风险 3：缺料（available <= min_stock） ──
    low_query = db.query(models.InventoryItem).filter(
        models.InventoryItem.is_archived == 0,
        (models.InventoryItem.total - models.InventoryItem.reserved) <= models.InventoryItem.min_stock
    )
    low_count = low_query.count()
    low = low_query.order_by((models.InventoryItem.total - models.InventoryItem.reserved).asc()).limit(8).all()
    low_stock_items = [{
        "id": i.id, "name": i.name, "unit": i.unit,
        "available": (i.total or 0) - (i.reserved or 0), "min_stock": i.min_stock,
    } for i in low]

    # ── 风险 4：停滞工序（in_progress 超过 3 天） ──
    stall_deadline = datetime.now() - timedelta(days=STALLED_DAYS)
    stalled_query = db.query(models.ProcessStep, models.Order).join(
        models.ProcessFlow, models.ProcessStep.flow_id == models.ProcessFlow.id
    ).join(models.Order, models.ProcessFlow.order_id == models.Order.id).filter(
        models.ProcessStep.status == "in_progress",
        models.ProcessStep.started_at != None,  # noqa: E711
        models.ProcessStep.started_at < stall_deadline,
        models.Order.status == "in_progress",
    )
    stalled_count = stalled_query.count()
    stalled = stalled_query.order_by(models.ProcessStep.started_at.asc()).limit(8).all()
    stalled_items = [{
        "order_id": o.id, "order_no": o.order_no, "step_id": s.id,
        "step_name": s.name,
        "days": (datetime.now() - s.started_at).days,
    } for s, o in stalled]

    # ── 风险 5：已完成但未领料（仍有预留挂在完成订单上，D16 退役自动扣减的兜底提醒） ──
    completed_unpicked_rows = (
        db.query(models.Order, func.count(models.InventoryReservation.id).label("mat_count"))
        .join(models.InventoryReservation, models.InventoryReservation.order_id == models.Order.id)
        .filter(models.Order.status == "completed")
        .group_by(models.Order.id)
        .limit(8)
        .all()
    )
    completed_unpicked_count = (
        db.query(func.count(func.distinct(models.InventoryReservation.order_id)))
        .join(models.Order, models.InventoryReservation.order_id == models.Order.id)
        .filter(models.Order.status == "completed")
        .scalar()
    ) or 0
    completed_unpicked_items = [{
        "order_id": o.id, "order_no": o.order_no, "product_name": o.product_name,
        "materials": c,
    } for o, c in completed_unpicked_rows]

    # ── 趋势：近 14 天完成订单数——单条 GROUP BY 查询（ENG-6：原为 14 次全表扫描） ──
    since = today - timedelta(days=TREND_DAYS - 1)
    rows = (
        db.query(cast(models.Order.updated_at, Date).label("d"), func.count().label("c"))
        .filter(
            models.Order.status == "completed",
            cast(models.Order.updated_at, Date) >= since,
        )
        .group_by(cast(models.Order.updated_at, Date))
        .all()
    )
    by_day = {r.d: r.c for r in rows}
    trend = [
        {"date": (today - timedelta(days=o)).strftime("%m-%d"),
         "completed": by_day.get(today - timedelta(days=o), 0)}
        for o in range(TREND_DAYS - 1, -1, -1)
    ]

    return {
        "today_pending": today_pending,
        "in_progress": in_progress,
        "inventory_alert": inventory_alert,
        "today_done": today_done,
        "recent_customers": recent_customers,
        "risks": {
            "overdue_orders": {"count": len(overdue), "items": overdue_items},
            "due_soon": {"count": len(due_soon), "items": due_soon_items},
            "low_stock": {"count": low_count, "items": low_stock_items},
            "stalled_steps": {"count": stalled_count, "items": stalled_items},
            "completed_unpicked": {"count": completed_unpicked_count, "items": completed_unpicked_items},
        },
        "trend": trend,
    }
