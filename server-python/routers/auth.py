from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from pydantic import BaseModel
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-super-secret-key-for-mes"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user or not bcrypt.checkpw(req.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被停用，请联系管理员")
        
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user.id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": encoded_jwt, 
        "refresh_token": encoded_jwt,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me")
def read_users_me(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    user_id = 1 # fallback
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload.get("sub"))
        except Exception:
            pass

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    perms = db.query(models.PagePermission).filter(models.PagePermission.user_id == user.id).all()
    user_dict = user.__dict__.copy()
    user_dict.pop("_sa_instance_state", None)
    
    perm_list = []
    for p in perms:
        p_dict = p.__dict__.copy()
        p_dict.pop("_sa_instance_state", None)
        perm_list.append(p_dict)
        
    user_dict["permissions"] = perm_list
    return user_dict
