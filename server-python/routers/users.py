from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
import bcrypt
from jose import jwt
from routers.auth import SECRET_KEY, ALGORITHM

def verify_admin(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="未登录，无法访问此接口"
        )
    token = auth_header.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="登录已失效，请重新登录"
        )
        
    current_user = db.query(models.User).filter(models.User.id == current_user_id).first()
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="用户不存在"
        )
        
    if current_user.is_admin != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="权限不足，只有管理员可以访问用户管理接口"
        )
    return current_user

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(verify_admin)])

@router.get("", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

def grant_admin_permissions(user_id: int, db: Session):
    db.query(models.PagePermission).filter(models.PagePermission.user_id == user_id).delete()
    pages = ['dashboard', 'customers', 'orders', 'process_flow', 'inventory', 'notifications', 'settings', 'outsourcing']
    for page_key in pages:
        perm = models.PagePermission(
            user_id=user_id,
            page_key=page_key,
            can_view=1,
            can_edit=1
        )
        db.add(perm)
    db.commit()

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
    
    if db_user.is_admin == 1:
        grant_admin_permissions(db_user.id, db)
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
    
    if db_user.is_admin == 1:
        grant_admin_permissions(db_user.id, db)
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
def update_permissions(user_id: int, payload: PermissionsUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(verify_admin)):
    # Check if target user is an administrator
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    is_target_admin = (target_user.is_admin == 1)
    is_editing_self_admin = (current_user.id == user_id) and is_target_admin

    db.query(models.PagePermission).filter(models.PagePermission.user_id == user_id).delete()
    for p in payload.permissions:
        can_view_val = 1 if p.can_view else 0
        can_edit_val = 1 if p.can_edit else 0
        
        # Enforce that admin's permissions are ALWAYS fully open (cannot be closed)
        if is_target_admin:
            can_view_val = 1
            can_edit_val = 1

        new_perm = models.PagePermission(
            user_id=user_id,
            page_key=p.page_key,
            can_view=can_view_val,
            can_edit=can_edit_val
        )
        db.add(new_perm)
    db.commit()
    return {"ok": True}
