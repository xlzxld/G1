from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from routers.auth import read_users_me
from pydantic import BaseModel

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=List[schemas.NotificationResponse])
def get_notifications(db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    return db.query(models.Notification).filter(models.Notification.to_user_id == current_user["id"]).order_by(models.Notification.created_at.desc()).limit(100).all()

@router.put("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    notif = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.to_user_id == current_user["id"]).first()
    if notif:
        notif.is_read = 1
        db.commit()
    return {"ok": True}

@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    db.query(models.Notification).filter(models.Notification.to_user_id == current_user["id"]).update({"is_read": 1})
    db.commit()
    return {"ok": True}

@router.post("", response_model=schemas.NotificationResponse)
def create_notification(notif: schemas.NotificationCreate, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not notif.title or not notif.title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")
    if not notif.to_user_id:
        raise HTTPException(status_code=400, detail="接收人不能为空")
        
    db_notif = models.Notification(
        from_user_id=current_user["id"],
        to_user_id=notif.to_user_id,
        title=notif.title,
        body=notif.body,
        source=notif.source,
        link=notif.link,
        is_read=0
    )
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif

@router.get("/rules", response_model=List[schemas.NotificationRuleResponse])
def get_rules(db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return db.query(models.NotificationRule).all()

class RuleUpdate(BaseModel):
    is_active: int

@router.put("/rules/{rule_id}", response_model=schemas.NotificationRuleResponse)
def toggle_rule(rule_id: int, update: RuleUpdate, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    rule = db.query(models.NotificationRule).filter(models.NotificationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    rule.is_active = update.is_active
    db.commit()
    db.refresh(rule)
    return rule
