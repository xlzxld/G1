"""认证与鉴权单一来源。

所有 Token 的签发、解析、校验只在本模块实现；其余模块（users/documents/
notifications/main 审计中间件）一律导入这里的函数，禁止自行 jwt.decode
（8/6 报告 P0-4：复制实现导致 is_active 校验漂移）。

Token 设计：
- access  JWT：type=access，7 天；
- refresh JWT：type=refresh，30 天，/auth/refresh 用它换新 access；
- 吊销：JWT 记录签发时的 user.token_version，登出时服务端递增该版本号，
  旧 Token 全部失效（无状态吊销，无需吊销表）。
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from pydantic import BaseModel
import bcrypt

from config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _create_token(user: models.User, token_type: str) -> str:
    if token_type == "refresh":
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "type": token_type,
        "ver": user.token_version or 1,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user or not bcrypt.checkpw(req.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被停用，请联系管理员")

    return {
        "access_token": _create_token(user, "access"),
        "refresh_token": _create_token(user, "refresh"),
        "token_type": "bearer",
        # UserResponse 排除 password_hash（8/6 报告 P0-2）
        "user": schemas.UserResponse.model_validate(user),
    }


def get_user_from_token(token: str, db: Session, expected_type: str = "access") -> models.User:
    """普通函数版鉴权：供 FastAPI 依赖与非请求上下文（SSE/中间件）共用。

    校验链：签名/过期 → type 匹配 → 用户存在 → is_active → token_version。
    任何一步失败抛 HTTPException（401/403）。
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效")

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Token 类型不正确，请重新登录")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token 无效")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="账户不存在或已被删除")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被停用，请联系管理员")
    if (user.token_version or 1) != payload.get("ver"):
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    return user


def try_decode_user_id(token: str) -> int | None:
    """宽容解析：仅用于审计日志归属，任何失败返回 None，不抛异常。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return int(payload.get("sub"))
    except Exception:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权访问，缺失Token")
    token = auth_header.split("Bearer ")[1]
    return get_user_from_token(token, db, expected_type="access")


def verify_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.is_admin != 1:
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以执行此操作")
    return current_user


@router.post("/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """用 refresh token 换新 access token。旧 refresh 沿用到自身过期（不轮换）。"""
    user = get_user_from_token(req.refresh_token, db, expected_type="refresh")
    return {
        "access_token": _create_token(user, "access"),
        "token_type": "bearer",
        "user": schemas.UserResponse.model_validate(user),
    }


@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """递增 token_version 使该用户全部已签发 Token 失效（包括其他设备）。"""
    current_user.token_version = (current_user.token_version or 1) + 1
    db.commit()
    return {"ok": True}


@router.get("/me")
def read_users_me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    perms = db.query(models.PagePermission).filter(models.PagePermission.user_id == user.id).all()
    data = schemas.UserResponse.model_validate(user).model_dump()
    data["permissions"] = [
        {"id": p.id, "user_id": p.user_id, "page_key": p.page_key,
         "can_view": p.can_view, "can_edit": p.can_edit}
        for p in perms
    ]
    return data
