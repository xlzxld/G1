from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas
from routers.auth import read_users_me
from pydantic import BaseModel
import asyncio
from fastapi.responses import StreamingResponse
from jose import jwt
from routers.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/notifications", tags=["notifications"])

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    def connect(self, user_id: int, queue: asyncio.Queue):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(queue)

    def disconnect(self, user_id: int, queue: asyncio.Queue):
        if queue in self.active_connections.get(user_id, []):
            self.active_connections[user_id].remove(queue)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    def notify_user(self, user_id: int):
        if user_id in self.active_connections:
            for queue in self.active_connections[user_id]:
                try:
                    queue.put_nowait("refresh")
                except Exception:
                    pass

manager = ConnectionManager()

def get_user_id_from_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except Exception:
        return None

@router.get("/stream")
async def message_stream(token: str = None):
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    queue = asyncio.Queue()
    manager.connect(user_id, queue)
    
    async def event_generator():
        try:
            while True:
                try:
                    # 45秒心跳检测检测间隔时间（最大程度降低由唤醒引起的性能损耗）
                    message = await asyncio.wait_for(queue.get(), timeout=45.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield "data: ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            manager.disconnect(user_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("", response_model=List[schemas.NotificationResponse])
def get_notifications(db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    return db.query(models.Notification).filter(models.Notification.to_user_id == current_user["id"]).order_by(models.Notification.created_at.desc()).limit(200).all()

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
    manager.notify_user(notif.to_user_id)
    return db_notif

# ────────────────────────── 通知规则管理 ──────────────────────────

@router.get("/rules", response_model=List[schemas.NotificationRuleResponse])
def get_rules(db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return db.query(models.NotificationRule).all()

@router.post("/rules", response_model=schemas.NotificationRuleResponse)
def create_rule(req: schemas.NotificationRuleCreate, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    rule = models.NotificationRule(**req.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.put("/rules/{rule_id}", response_model=schemas.NotificationRuleResponse)
def update_rule(rule_id: int, req: schemas.NotificationRuleCreate, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    rule = db.query(models.NotificationRule).filter(models.NotificationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    for k, v in req.model_dump().items():
        setattr(rule, k, v)
        
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db), current_user: dict = Depends(read_users_me)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    rule = db.query(models.NotificationRule).filter(models.NotificationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    db.delete(rule)
    db.commit()
    return {"ok": True}

# ────────────────────────── 通知规则联动引擎 ──────────────────────────

def trigger_notification_rules(event: str, context: dict, db: Session):
    try:
        # 1. 找出所有匹配的、活跃的通知规则
        rules = db.query(models.NotificationRule).filter(
            models.NotificationRule.event == event,
            models.NotificationRule.is_active == 1
        ).all()
        
        for rule in rules:
            # 2. 条件判定
            condition_matched = True
            if rule.condition_field:
                field_name = rule.condition_field.strip()
                if field_name in context:
                    field_val = context[field_name]
                    op = rule.condition_op
                    cond_val = rule.condition_value
                    
                    try:
                        # 转换比较
                        if op in ("gt", "lt"):
                            f_val = float(field_val)
                            f_cond = float(cond_val)
                            if op == "gt" and not (f_val > f_cond): condition_matched = False
                            if op == "lt" and not (f_val < f_cond): condition_matched = False
                        elif op == "eq":
                            if str(field_val).strip() != str(cond_val).strip(): condition_matched = False
                        elif op == "contains":
                            if str(cond_val) not in str(field_val): condition_matched = False
                    except Exception:
                        condition_matched = False
                else:
                    condition_matched = False
                    
            if not condition_matched:
                continue
                
            # 3. 模板格式化
            title = rule.title_template
            body = rule.body_template or ""
            for k, v in context.items():
                placeholder = f"{{{k}}}"
                title = title.replace(placeholder, str(v))
                body = body.replace(placeholder, str(v))
                
            # 4. 解析接收人列表
            to_user_ids = []
            role_config = (rule.notify_role or "").strip()
            
            if not role_config or role_config.lower() == "all":
                # 发给所有人
                to_user_ids = [u.id for u in db.query(models.User).all()]
            elif role_config.startswith("user_ids:"):
                # 指定用户 ids，格式："user_ids:1,2,5"
                try:
                    ids_str = role_config.split("user_ids:")[1]
                    to_user_ids = [int(x.strip()) for x in ids_str.split(",") if x.strip()]
                except Exception:
                    pass
            elif role_config.startswith("role:"):
                # 角色分类发送
                role_name = role_config.split("role:")[1].strip()
                if role_name == "admin":
                    to_user_ids = [u.id for u in db.query(models.User).filter(models.User.is_admin == 1).all()]
                else:
                    to_user_ids = [u.id for u in db.query(models.User).filter(models.User.is_admin != 1).all()]
            else:
                # 兜底直接解析逗号分隔的普通用户 ID 列表
                try:
                    to_user_ids = [int(x.strip()) for x in role_config.split(",") if x.strip()]
                except Exception:
                    pass
                    
            # 5. 创建通知
            for uid in to_user_ids:
                new_notif = models.Notification(
                    from_user_id=1,  # 系统账号
                    to_user_id=uid,
                    title=title,
                    body=body,
                    source="system",
                    link=(
                        f"/orders?highlight={context.get('id')}" if "id" in context and (event.startswith("order_") or event == "design_completed")
                        else f"/inventory?highlight={context.get('item_id')}" if "item_id" in context and event == "inventory_alert"
                        else ""
                    ),
                    is_read=0
                )
                db.add(new_notif)
                
        db.commit()
        # 触发实时推送更新
        for uid in to_user_ids:
            manager.notify_user(uid)
    except Exception as e:
        print(f"Trigger notification rules error: {e}")
