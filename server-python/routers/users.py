from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
import bcrypt

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@router.post("", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if not user.username or not user.username.strip():
        raise HTTPException(status_code=400, detail="用户名不能为空")
        
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_user = models.User(
        username=user.username,
        password_hash=hashed,
        display_name=user.display_name,
        role_label=user.role_label,
        is_admin=user.is_admin,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.username or not user.username.strip():
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    db_user.username = user.username
    db_user.display_name = user.display_name
    db_user.role_label = user.role_label
    db_user.is_admin = user.is_admin
    db_user.is_active = user.is_active
    
    if user.password:
        hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db_user.password_hash = hashed
        
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"ok": True}

@router.get("/{user_id}/permissions")
def get_permissions(user_id: int, db: Session = Depends(get_db)):
    perms = db.query(models.PagePermission).filter(models.PagePermission.user_id == user_id).all()
    return [{"page_key": p.page_key, "can_view": p.can_view == 1, "can_edit": p.can_edit == 1} for p in perms]

from pydantic import BaseModel
class PermissionItem(BaseModel):
    page_key: str
    can_view: bool
    can_edit: bool

class PermissionsUpdate(BaseModel):
    permissions: List[PermissionItem]

@router.put("/{user_id}/permissions")
def update_permissions(user_id: int, payload: PermissionsUpdate, db: Session = Depends(get_db)):
    db.query(models.PagePermission).filter(models.PagePermission.user_id == user_id).delete()
    for p in payload.permissions:
        new_perm = models.PagePermission(
            user_id=user_id,
            page_key=p.page_key,
            can_view=1 if p.can_view else 0,
            can_edit=1 if p.can_edit else 0
        )
        db.add(new_perm)
    db.commit()
    return {"ok": True}
