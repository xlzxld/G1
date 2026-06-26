from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from pydantic import BaseModel
import bcrypt
from routers.auth import read_users_me

router = APIRouter(prefix="/settings", tags=["settings"])

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.put("/change-password")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not bcrypt.checkpw(req.current_password.encode('utf-8'), current_user["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    new_hash = bcrypt.hashpw(req.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.query(models.User).filter(models.User.id == current_user["id"]).update({"password_hash": new_hash})
    db.commit()
    return {"ok": True}

@router.get("/audit-logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    logs = db.query(models.AuditLog, models.User.display_name)\
             .outerjoin(models.User, models.AuditLog.user_id == models.User.id)\
             .order_by(models.AuditLog.created_at.desc())\
             .limit(200)\
             .all()
             
    result = []
    for log, display_name in logs:
        log_dict = log.__dict__.copy()
        log_dict["display_name"] = display_name or "系统"
        result.append(log_dict)
    return result
