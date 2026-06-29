from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

# Create all tables (in production, use Alembic)
Base.metadata.create_all(bind=engine)

from sqlalchemy import text
with engine.connect() as connection:
    try:
        connection.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS inventory_deducted INTEGER DEFAULT 0;"))
        connection.execute(text("ALTER TABLE process_steps DROP COLUMN IF EXISTS can_parallel;"))
        connection.execute(text("ALTER TABLE process_steps DROP COLUMN IF EXISTS depends_on_step_id;"))
        connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS step_id INTEGER REFERENCES process_steps(id) ON DELETE CASCADE;"))
        connection.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS contacts JSON DEFAULT '[]';"))
        connection.execute(text("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS contacts JSON DEFAULT '[]';"))
        connection.commit()
    except Exception as e:
        print(f"Error modifying database: {e}")

app = FastAPI(
    title="Hot Runner MES API",
    description="MES System API rewritten in Python/FastAPI",
    version="2.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173", # Vue Dev server
    "http://127.0.0.1:5173",
    "*" # Can be restricted later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "Welcome to Hot Runner MES API (FastAPI)"}

from routers import customers, orders, inventory, process, documents, auth, users, dashboard, settings, vendors, notifications

app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(process.router)
app.include_router(documents.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(vendors.router)
app.include_router(notifications.router)

import urllib.parse
from fastapi import Request
from database import SessionLocal
import models

def get_friendly_detail(method: str, path: str, db) -> str:
    path = path.strip("/")
    parts = path.split("/")
    if not parts or parts[0] == "":
        return f"{method} {path}"
        
    base = parts[0]
    
    # 1. 订单路由
    if base == "orders":
        if len(parts) == 1:
            if method == "POST": return "创建了新生产订单"
            return "批量操作订单"
        
        order_id = parts[1]
        try:
            order_obj = db.query(models.Order).filter(models.Order.id == int(order_id)).first()
            order_no = f"「{order_obj.order_no}」" if order_obj else f"#{order_id}"
        except Exception:
            order_no = f"#{order_id}"
            
        if len(parts) == 2:
            if method == "PUT": return f"修改了订单 {order_no} 的基本信息"
            if method == "DELETE": return f"删除了订单 {order_no}"
            return f"操作了订单 {order_no}"
            
        sub = parts[2]
        if sub == "status":
            return f"更新了订单 {order_no} 的生产状态"
        elif sub == "materials":
            if method == "POST": return f"为订单 {order_no} 分配了零配件用料"
            if method == "DELETE": return f"移除了订单 {order_no} 的某项用料"
            return f"修改了订单 {order_no} 的用料明细"
        elif sub == "steps" and len(parts) >= 5:
            step_id = parts[3]
            action = parts[4]
            try:
                step_obj = db.query(models.ProcessStep).filter(models.ProcessStep.id == int(step_id)).first()
                step_name = f"「{step_obj.name}」" if step_obj else f"步骤ID:{step_id}"
            except Exception:
                step_name = f"步骤ID:{step_id}"
                
            if action == "advance": return f"确认完成了订单 {order_no} 的 {step_name} 工序"
            if action == "rollback": return f"撤回了订单 {order_no} 的 {step_name} 工序"
            if action == "skip": return f"跳过了订单 {order_no} 的 {step_name} 工序"
            return f"操作了订单 {order_no} 的工序"
            
    # 2. 库存路由
    elif base == "inventory":
        if len(parts) == 1:
            if method == "POST": return "录入了新的库存物料"
            return "管理了库存列表"
        if parts[1] == "reserve":
            return "为订单预留了库存零配件"
        
        item_id = parts[1]
        try:
            item_obj = db.query(models.InventoryItem).filter(models.InventoryItem.id == int(item_id)).first()
            item_name = f"「{item_obj.name}」" if item_obj else f"ID:{item_id}"
        except Exception:
            item_name = f"ID:{item_id}"
            
        if method == "PUT": return f"修改了库存零配件 {item_name} 的规格或预警阈值"
        if method == "DELETE": return f"删除了库存零配件 {item_name}"
        
    # 3. 图纸附件路由
    elif base == "documents":
        if len(parts) == 1:
            if method == "POST": return "上传了新工程图纸/附件"
            return "管理了图纸文档"
        doc_id = parts[1]
        try:
            doc_obj = db.query(models.Document).filter(models.Document.id == int(doc_id)).first()
            doc_name = f"「{doc_obj.filename}」" if doc_obj else f"ID:{doc_id}"
        except Exception:
            doc_name = f"ID:{doc_id}"
            
        if method == "DELETE": return f"删除了工程文档 {doc_name}"
        if method == "PUT": return f"修改了工程文档 {doc_name} 的分类或备注信息"
        
    # 4. 客户路由
    elif base == "customers":
        if len(parts) == 1:
            if method == "POST": return "新建录入了新客户档案"
            return "管理了客户名录"
        cust_id = parts[1]
        try:
            cust_obj = db.query(models.Customer).filter(models.Customer.id == int(cust_id)).first()
            cust_name = f"「{cust_obj.name}」" if cust_obj else f"ID:{cust_id}"
        except Exception:
            cust_name = f"ID:{cust_id}"
            
        if method == "PUT": return f"修改了客户 {cust_name} 的地址或联系方式"
        if method == "DELETE": return f"删除了客户 {cust_name} 的全部档案信息"
        
    # 5. 用户与权限路由
    elif base == "users":
        if len(parts) == 1:
            if method == "POST": return "新建注册了系统操作账号"
            return "管理了系统账号列表"
        u_id = parts[1]
        try:
            u_obj = db.query(models.User).filter(models.User.id == int(u_id)).first()
            u_name = f"「{u_obj.username}」" if u_obj else f"ID:{u_id}"
        except Exception:
            u_name = f"ID:{u_id}"
            
        if method == "PUT": return f"更新了账号 {u_name} 的资料或权限配置"
        if method == "DELETE": return f"销户删除了系统账号 {u_name}"
        
    # 6. 外协加工商
    elif base == "vendors":
        if len(parts) == 1:
            if method == "POST": return "添加了新外协委外加工商"
            return "管理了外协厂商列表"
        v_id = parts[1]
        if method == "PUT": return f"修改了外协加工商 ID:{v_id} 的联系信息"
        if method == "DELETE": return f"删除了外协加工商 ID:{v_id}"
        
    # 7. 工艺模板
    elif base == "process-flows":
        if len(parts) == 1:
            if method == "POST": return "创建了新工艺模板"
        elif len(parts) == 2:
            if method == "PUT": return f"修改了工艺模板 ID:{parts[1]} 的基本信息"
            if method == "DELETE": return f"删除了工艺模板 ID:{parts[1]}"
        elif len(parts) >= 3 and parts[2] == "steps":
            return f"更新了工艺模板 ID:{parts[1]} 的工序步骤配置"

    # 8. 通知中心
    elif base == "notifications":
        if len(parts) == 1:
            if method == "POST": return "派发了新通知"
        elif len(parts) == 2 and parts[1] == "read-all":
            return "标记了全部通知为已读"
        elif len(parts) == 3 and parts[2] == "read":
            return f"将通知 ID:{parts[1]} 标记为已读"

    # 9. 其他设定
    elif base == "settings":
        return "修改了主系统配置参数"
        
    # 汉化映射表：为所有非特化处理的 API 路径兜底，确保详情里绝不漏英文
    entity_map = {
        "customers": "客户档案",
        "orders": "订单",
        "inventory": "库存零配件",
        "process-flows": "工艺模板",
        "users": "用户账号",
        "vendors": "外协厂商",
        "notifications": "通知中心",
        "settings": "系统设置",
        "auth": "登录认证",
        "documents": "图纸管理",
        "process": "工艺流程",
    }
    translated_base = entity_map.get(base, base)
    action_word = "添加" if method == "POST" else "更新" if method == "PUT" else "删除" if method == "DELETE" else method
    return f"{action_word}了 {translated_base} 数据"

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    method = request.method
    if method in ["POST", "PUT", "DELETE"]:
        path = request.url.path
        if path.startswith("/auth"):
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization", "")
        user_id = None
        # 支持 Bearer / bearer 大小写不敏感的解析方式
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                from jose import jwt
                from routers.auth import SECRET_KEY, ALGORITHM
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = int(payload.get("sub"))
            except Exception:
                pass
                
        db = SessionLocal()
        try:
            # 如果没拿到 user_id (没有 Token 或 Token 错误)，尝试寻找第一个管理员 ID，以避免关联不存在的 ID 1
            if not user_id:
                try:
                    first_admin = db.query(models.User).filter(models.User.is_admin == 1).order_by(models.User.id).first()
                    if first_admin:
                        user_id = first_admin.id
                    else:
                        first_user = db.query(models.User).order_by(models.User.id).first()
                        if first_user:
                            user_id = first_user.id
                except Exception:
                    pass
                # 仍为空时，如果表里没有任何用户，保留 None，外键设为 NULL 表明“系统/游客”触发
                
            action = "create" if method == "POST" else "update" if method == "PUT" else "delete"
            detail_text = get_friendly_detail(method, path, db)
            audit = models.AuditLog(
                user_id=user_id,
                action=action,
                entity_type=path.split("/")[1] if len(path.split("/")) > 1 else "unknown",
                detail=detail_text
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            print(f"Audit log failed: {e}")
        finally:
            db.close()
            
    response = await call_next(request)
    return response
