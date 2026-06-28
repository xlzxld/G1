from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas
import os
import time
from jose import jwt, JWTError
from routers.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# ---------------------------------------------------------------------------
# 允许的文件扩展名白名单
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {
    # 图片
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
    # 文档
    ".pdf",
    # 压缩包
    ".zip", ".rar", ".7z", ".tar", ".gz",
    # CAD 格式
    ".dwg", ".dxf", ".dwf", ".step", ".stp", ".iges", ".igs",
    # UG / NX (Parasolid)
    ".prt", ".x_t", ".x_b",
}

# 允许的 MIME 类型（CAD/UG 文件通常是 octet-stream，走扩展名判断）
ALLOWED_MIME_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "image/bmp", "image/svg+xml",
    "application/pdf",
    "application/zip", "application/x-zip-compressed",
    "application/x-rar-compressed", "application/x-7z-compressed",
    "application/x-tar", "application/gzip",
    "application/octet-stream",  # 兜底：CAD/UG 文件通常为此类型
}

ALLOWED_EXTENSIONS_DISPLAY = "图片(.png/.jpg/.gif/.webp/.bmp/.svg)、PDF、压缩包(.zip/.rar/.7z)、CAD(.dwg/.dxf/.step/.iges)、UG/NX(.prt/.x_t/.x_b)"


def _get_ext(filename: str) -> str:
    """返回小写扩展名，如 '.dwg'"""
    return os.path.splitext(filename.lower())[1]


def _is_allowed(filename: str, content_type: str) -> bool:
    ext = _get_ext(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if content_type in ALLOWED_MIME_TYPES:
        return True
    # 部分浏览器对 rar/7z/CAD/UG 文件上报不标准 MIME，只要扩展名合法就放行
    return True


# ---------------------------------------------------------------------------
# Auth & Permission 依赖
# ---------------------------------------------------------------------------

def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    token = auth_header.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def _get_drawings_perm(user: models.User, db: Session) -> models.PagePermission:
    """获取 drawings 权限行（管理员直接返回 None，调用方需先判断 is_admin）"""
    return db.query(models.PagePermission).filter(
        models.PagePermission.user_id == user.id,
        models.PagePermission.page_key == "drawings"
    ).first()


def require_drawings_view(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    if current_user.is_admin:
        return current_user
    perm = _get_drawings_perm(current_user, db)
    if not perm or not perm.can_view:
        raise HTTPException(status_code=403, detail="权限不足：无图纸查看权限")
    return current_user


def require_drawings_edit(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    if current_user.is_admin:
        return current_user
    perm = _get_drawings_perm(current_user, db)
    if not perm or not perm.can_view:
        raise HTTPException(status_code=403, detail="权限不足：无图纸查看权限")
    if not perm.can_edit:
        raise HTTPException(status_code=403, detail="权限不足：无图纸编辑权限")
    return current_user


# ---------------------------------------------------------------------------
# GET /documents  — 查询图纸列表
# ---------------------------------------------------------------------------

@router.get("", response_model=List[schemas.DocumentResponse])
def list_documents(
    order_id: Optional[int] = Query(None, description="按订单 ID 过滤"),
    category: Optional[str] = Query(None, description="按分类过滤，如 '图纸'"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_drawings_view),
):
    q = db.query(models.Document)
    if order_id is not None:
        q = q.filter(models.Document.order_id == order_id)
    if category:
        q = q.filter(models.Document.category == category)
    return q.order_by(models.Document.created_at.desc()).all()


# ---------------------------------------------------------------------------
# POST /documents  — 上传图纸（含版本控制）
# ---------------------------------------------------------------------------

@router.post("", response_model=schemas.DocumentResponse)
async def upload_document(
    order_id: int = Form(..., description="所属订单 ID"),
    title: str = Form("", description="图纸标题（可选）"),
    description: str = Form("", description="说明（可选）"),
    category: str = Form("图纸", description="分类，默认为'图纸'"),
    step_id: Optional[int] = Form(None, description="所属工序 ID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_drawings_edit),
):
    original_name = file.filename or "unnamed"

    # 1. 文件类型校验
    if not _is_allowed(original_name, file.content_type or ""):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 ({_get_ext(original_name)})。支持格式：{ALLOWED_EXTENSIONS_DISPLAY}"
        )

    # 2. 读取内容 & 大小校验
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 50 MB 上限")

    # 3. 查找订单（用于目录命名）
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 4. 构建存储路径：uploads/{order_no}/{category}/v{timestamp}-{filename}
    ts = int(time.time() * 1000)
    stored_filename = f"v{ts}-{original_name}"
    dir_path = os.path.join(UPLOAD_DIR, order.order_no, category)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, stored_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 5. 版本号自动递增（同订单 + 同分类维度）
    last = (
        db.query(models.Document)
        .filter(
            models.Document.order_id == order_id,
            models.Document.category == category,
        )
        .order_by(models.Document.version.desc())
        .first()
    )
    next_version = (last.version if last else 0) + 1

    # 6. 将同分类下所有 active 版本标记为 deprecated
    db.query(models.Document).filter(
        models.Document.order_id == order_id,
        models.Document.category == category,
        models.Document.status == "active",
    ).update({"status": "deprecated"}, synchronize_session=False)

    # 7. 写入新版本记录
    db_doc = models.Document(
        order_id=order_id,
        step_id=step_id,
        filename=stored_filename,
        original_name=original_name,
        category=category,
        version=next_version,
        status="active",
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "",
        title=title if title else original_name.rsplit(".", 1)[0],
        description=description,
        uploaded_by=current_user.id,
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 触发“订单设计完成”通知规则
    if db_doc.category == "图纸" and db_doc.status == "active":
        try:
            from routers.notifications import trigger_notification_rules
            context = {
                "id": order.id,
                "order_no": order.order_no,
                "product_name": order.product_name,
                "drawing_title": db_doc.title,
                "version": db_doc.version
            }
            trigger_notification_rules("design_completed", context, db)
        except Exception as e:
            print(f"Trigger design_completed error: {e}")

    return db_doc


# ---------------------------------------------------------------------------
# PUT /documents/{doc_id}  — 修改元信息
# ---------------------------------------------------------------------------

@router.put("/{doc_id}", response_model=schemas.DocumentResponse)
def update_document(
    doc_id: int,
    payload: schemas.DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_drawings_edit),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="图纸记录不存在")

    if payload.title is not None:
        doc.title = payload.title
    if payload.description is not None:
        doc.description = payload.description
    if payload.status is not None:
        if payload.status not in ("active", "pending", "deprecated"):
            raise HTTPException(status_code=400, detail="无效状态值，允许：active / pending / deprecated")
        doc.status = payload.status

    db.commit()
    db.refresh(doc)
    return doc


# ---------------------------------------------------------------------------
# PUT /documents/{doc_id}/status  — 单独变更状态（含互斥 active 逻辑）
# ---------------------------------------------------------------------------

@router.put("/{doc_id}/status", response_model=schemas.DocumentResponse)
def update_document_status(
    doc_id: int,
    payload: schemas.DocumentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_drawings_edit),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="图纸记录不存在")

    if payload.status not in ("active", "pending", "deprecated"):
        raise HTTPException(status_code=400, detail="无效状态值，允许：active / pending / deprecated")

    # 激活某版本时，将同订单+同分类下其他 active 版本降级为 deprecated
    if payload.status == "active":
        db.query(models.Document).filter(
            models.Document.order_id == doc.order_id,
            models.Document.category == doc.category,
            models.Document.status == "active",
            models.Document.id != doc_id,
        ).update({"status": "deprecated"}, synchronize_session=False)

    doc.status = payload.status
    db.commit()
    db.refresh(doc)

    # 触发“订单设计完成”通知规则
    if doc.category == "图纸" and payload.status == "active":
        try:
            order = db.query(models.Order).filter(models.Order.id == doc.order_id).first()
            if order:
                from routers.notifications import trigger_notification_rules
                context = {
                    "id": order.id,
                    "order_no": order.order_no,
                    "product_name": order.product_name,
                    "drawing_title": doc.title,
                    "version": doc.version
                }
                trigger_notification_rules("design_completed", context, db)
        except Exception as e:
            print(f"Trigger design_completed on status update error: {e}")

    return doc


# ---------------------------------------------------------------------------
# DELETE /documents/{doc_id}  — 删除记录 + 磁盘文件
# ---------------------------------------------------------------------------

@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_drawings_edit),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="图纸记录不存在")

    # 删除磁盘文件，文件不存在时静默忽略
    try:
        if os.path.isfile(doc.file_path):
            os.remove(doc.file_path)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return {"deleted": True}
