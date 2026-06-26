from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
import models
from database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()
    
    # 待处理订单 (paused)
    today_pending = db.query(models.Order).filter(models.Order.status == "paused").count()
    
    # 生产中 (in_progress)
    in_progress = db.query(models.Order).filter(models.Order.status == "in_progress").count()
    
    # 库存预警 (total - reserved <= alert_threshold or something similar)
    # Let's just use total <= alert_threshold for simplicity
    inventory_alert = db.query(models.InventoryItem).filter(models.InventoryItem.total <= models.InventoryItem.alert_threshold).count()
    
    # 今日完成 (completed today)
    # Using cast to Date is safer across dialects
    from sqlalchemy import cast, Date
    today_done = db.query(models.Order).filter(
        models.Order.status == "completed",
        cast(models.Order.updated_at, Date) == today
    ).count()
    
    # 我的待办 (mocked)
    my_todos = 0
    
    # 最近新增客户
    recent_customers = db.query(models.Customer).order_by(models.Customer.created_at.desc()).limit(5).all()
    
    return {
        "today_pending": today_pending,
        "in_progress": in_progress,
        "inventory_alert": inventory_alert,
        "today_done": today_done,
        "recent_customers": recent_customers
    }
