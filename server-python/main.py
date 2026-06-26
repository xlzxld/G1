from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

# Create all tables (in production, use Alembic)
Base.metadata.create_all(bind=engine)

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

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    method = request.method
    # only audit mutations
    if method in ["POST", "PUT", "DELETE"]:
        path = request.url.path
        if path.startswith("/auth"):
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization", "")
        user_id = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                from jose import jwt
                from routers.auth import SECRET_KEY, ALGORITHM
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = int(payload.get("sub"))
            except Exception as e:
                pass
                
        if not user_id:
            user_id = 1
            
        action = "create" if method == "POST" else "update" if method == "PUT" else "delete"
        entity_type = path.split("/")[1] if len(path.split("/")) > 1 else "unknown"
        
        db = SessionLocal()
        try:
            audit = models.AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                detail=urllib.parse.unquote(path)
            )
            db.add(audit)
            db.commit()
        except:
            pass
        finally:
            db.close()
            
    response = await call_next(request)
    return response
