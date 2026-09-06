from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from routers.auth import get_current_user
from routers.inventory import require_inventory_edit
from services import inventory_service as svc
import models, schemas

# Router 级鉴权：订单全部端点要求登录（8/6 报告 P0-1）
router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)])

from sqlalchemy import or_, desc, asc

from sqlalchemy.orm import joinedload

@router.get("")
def get_orders(
    db: Session = Depends(get_db), 
    page: int = 1, 
    limit: int = 20,
    keyword: str = None,
    status: str = None,
    priority: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    customer_id: int = None
):
    query = db.query(models.Order).options(joinedload(models.Order.customer))
    
    if customer_id:
        query = query.filter(models.Order.customer_id == customer_id)
    if keyword:
        query = query.filter(
            or_(
                models.Order.order_no.ilike(f"%{keyword}%"),
                models.Order.product_name.ilike(f"%{keyword}%"),
                models.Order.customer_name.ilike(f"%{keyword}%")
            )
        )
    if status:
        query = query.filter(models.Order.status == status)
    if priority is not None and priority != "":
        try:
            query = query.filter(models.Order.priority == int(priority))
        except ValueError:
            pass
        
    total = query.count()
    
    if sort_by and hasattr(models.Order, sort_by):
        column = getattr(models.Order, sort_by)
        if sort_order == 'asc':
            query = query.order_by(asc(column))
        else:
            query = query.order_by(desc(column))
            
    skip = (page - 1) * limit
    orders = query.offset(skip).limit(limit).all()
    
    step_ids = [order.current_step_id for order in orders if order.current_step_id]
    step_map = {}
    if step_ids:
        steps = db.query(models.ProcessStep).filter(models.ProcessStep.id.in_(step_ids)).all()
        step_map = {s.id: s.name for s in steps}

    results = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "order_no": order.order_no,
            "product_name": order.product_name,
            "customer_id": order.customer_id,
            "customer_name": order.customer.name if order.customer else getattr(order, 'customer_name', ''),
            "priority": order.priority,
            "status": order.status,
            "current_step_id": order.current_step_id,
            "shipment_date": order.shipment_date,
            "notes": order.notes,
            "created_by": order.created_by,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "current_step_name": step_map.get(order.current_step_id, "") if order.current_step_id else ""
        }
        results.append(order_dict)
        
    return {"data": results, "total": total}

@router.post("", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    if not order.order_no or not str(order.order_no).strip():
        raise HTTPException(status_code=400, detail="订单编号不能为空")
    if not order.customer_id:
        raise HTTPException(status_code=400, detail="关联客户不能为空")
        
    order_data = order.model_dump(exclude={"template_flow_id"})
    order_data["status"] = "in_progress"
    
    # 同步客户名称，解决冗余字段搜索不一致问题
    db_customer = db.query(models.Customer).filter(models.Customer.id == order.customer_id).first()
    if db_customer:
        order_data["customer_name"] = db_customer.name
        
    db_order = models.Order(**order_data)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    if order.template_flow_id:
        template_flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == order.template_flow_id, models.ProcessFlow.is_template == 1).first()
        if template_flow:
            new_flow = models.ProcessFlow(
                name=f"Flow for {db_order.order_no}",
                description=template_flow.description,
                is_template=0,
                order_id=db_order.id
            )
            db.add(new_flow)
            db.commit()
            db.refresh(new_flow)
            
            template_steps = db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == template_flow.id).order_by(models.ProcessStep.seq).all()
            for ts in template_steps:
                new_step = models.ProcessStep(
                    flow_id=new_flow.id,
                    name=ts.name,
                    seq=ts.seq,
                    required=ts.required,
                    outsourced=ts.outsourced,
                    assignee=ts.assignee,
                    completion_condition=ts.completion_condition,
                    status="pending"
                )
                db.add(new_step)
            db.commit()
            
            # Set the first step as current step
            first_step = db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == new_flow.id).order_by(models.ProcessStep.seq).first()
            if first_step:
                db_order.current_step_id = first_step.id
                db.commit()

    # 触发通知规则引擎
    try:
        from routers.notifications import trigger_notification_rules
        order_dict = {
            "id": db_order.id,
            "order_no": db_order.order_no,
            "product_name": db_order.product_name,
            "status": db_order.status,
            "priority": db_order.priority,
            "notes": db_order.notes or ""
        }
        trigger_notification_rules("order_created", order_dict, db)
    except Exception as e:
        print(f"Order created notify failed: {e}")

    return db_order

@router.put("/{order_id}", response_model=schemas.OrderResponse)
def update_order(order_id: int, order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if not order.order_no or not str(order.order_no).strip():
        raise HTTPException(status_code=400, detail="订单编号不能为空")
    if not order.customer_id:
        raise HTTPException(status_code=400, detail="关联客户不能为空")

    update_data = order.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
        
    # 同步客户名称，解决重新关联客户后搜索依然搜到老客户的问题
    if "customer_id" in update_data:
        db_customer = db.query(models.Customer).filter(models.Customer.id == update_data["customer_id"]).first()
        if db_customer:
            db_order.customer_name = db_customer.name
        
    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(require_inventory_edit)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 删除守卫（D19）：已有领料/退料流水的订单禁止删除，否则流水失去业务上下文
    has_movements = db.query(models.StockMovement).filter(
        models.StockMovement.source_type == "order",
        models.StockMovement.source_id == order.id
    ).count() > 0
    if has_movements:
        raise HTTPException(status_code=400, detail="该订单已有领料/退料流水，禁止删除（库存审计链需要保留业务上下文）")

    # 释放全部预留并回退 reserved 缓存列（8/6 报告数据完整性 #1 修复）
    svc.release_order_reservations(db, order)

    flows = db.query(models.ProcessFlow).filter(models.ProcessFlow.order_id == order.id).all()
    for flow in flows:
        db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == flow.id).delete()
    db.query(models.ProcessFlow).filter(models.ProcessFlow.order_id == order.id).delete()
    db.query(models.Document).filter(models.Document.order_id == order.id).delete()

    db.delete(order)
    db.commit()
    return {"ok": True}

@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order_dict = {
        "id": order.id,
        "order_no": order.order_no,
        "product_name": order.product_name,
        "customer_id": order.customer_id,
        "customer_name": order.customer.name if order.customer else order.customer_name,
        "customer": {
            "name": order.customer.name,
            "contact": order.customer.contact,
            "phone": order.customer.phone,
            "address": order.customer.address,
            "wechat": order.customer.wechat,
            "email": order.customer.email
        } if order.customer else None,
        "priority": order.priority,
        "status": order.status,
        "current_step_id": order.current_step_id,
        "shipment_date": order.shipment_date,
        "notes": order.notes,
        "created_by": order.created_by,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "documents": [
            {
                "id": d.id, "filename": d.filename, "original_name": d.original_name,
                "category": d.category, "version": d.version, "status": d.status,
                "file_path": d.file_path, "file_size": d.file_size, "mime_type": d.mime_type,
                "title": d.title, "description": d.description, "created_at": d.created_at,
                "step_id": d.step_id
            } for d in order.documents
        ],
        "steps": []
    }
    
    # Attach steps if a process flow is linked
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.order_id == order.id).first()
    if flow:
        steps = db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == flow.id).order_by(models.ProcessStep.seq).all()
        order_dict["steps"] = [
            {
                "id": s.id, "name": s.name, "seq": s.seq, "required": s.required,
                "outsourced": s.outsourced,
                "assignee": s.assignee, "status": s.status, "completion_condition": s.completion_condition,
                "started_at": s.started_at, "completed_at": s.completed_at
            } for s in steps
        ]
        
    return order_dict

# ────────────────────────── 库存联动（D16 退役） ──────────────────────────
# 原 check_inventory_alert / deduct_order_inventory / rollback_order_inventory 已删除：
# 领料 OUTBOUND 是唯一减 total 的业务路径（services/inventory_service.py），
# 订单状态流转不再触碰库存；预警由服务层在提交后按阈值穿越评估。

def _notify_order_completed(order: models.Order, db: Session):
    try:
        from routers.notifications import trigger_notification_rules
        trigger_notification_rules("order_completed", {
            "id": order.id,
            "order_no": order.order_no,
            "product_name": order.product_name,
            "status": order.status,
            "priority": order.priority,
            "notes": order.notes or ""
        }, db)
    except Exception as e:
        print(f"Order completed notify failed: {e}")

from pydantic import BaseModel
class StatusUpdate(BaseModel):
    status: str

VALID_ORDER_STATUSES = {"in_progress", "completed", "paused"}

@router.put("/{order_id}/status")
def update_order_status(order_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in VALID_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效的订单状态，允许：{' / '.join(sorted(VALID_ORDER_STATUSES))}")

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    prev_status = order.status
    order.status = payload.status
    # 订单完成不再触碰库存（D16）；只保留业务通知
    if payload.status == "completed" and prev_status != "completed":
        _notify_order_completed(order, db)

    db.commit()
    return {"ok": True}

@router.post("/{order_id}/steps/{step_id}/advance")
def advance_step(order_id: int, step_id: int, db: Session = Depends(get_db)):
    step = db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id, models.ProcessStep.flow_id == db.query(models.ProcessFlow.id).filter(models.ProcessFlow.order_id == order_id).scalar_subquery()).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
        
    if step.completion_condition == 'photo':
        doc_count = db.query(models.Document).filter(models.Document.step_id == step_id).count()
        if doc_count == 0:
            raise HTTPException(status_code=400, detail="必须为本工序上传实操/检验照片才能确认完成")
            
    from datetime import datetime
    step.status = 'completed'
    step.completed_at = datetime.utcnow()
    
    # Also update order current_step_id if we want to track it
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    order.current_step_id = step.id
    
    # If all steps (including non-required ones) are completed or skipped, we auto-complete the order
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.order_id == order_id).first()
    all_steps = db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == flow.id).order_by(models.ProcessStep.seq).all()
    all_completed = True
    for s in all_steps:
        if s.status not in ('completed', 'skipped'):
            all_completed = False
            break
    if all_completed:
        prev_status = order.status
        order.status = 'completed'
        if prev_status != 'completed':
            _notify_order_completed(order, db)

    db.commit()
    return {"ok": True}

@router.post("/{order_id}/steps/{step_id}/rollback")
def rollback_step(order_id: int, step_id: int, db: Session = Depends(get_db)):
    step = db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id, models.ProcessStep.flow_id == db.query(models.ProcessFlow.id).filter(models.ProcessFlow.order_id == order_id).scalar_subquery()).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    step.status = 'pending'
    step.completed_at = None

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    order.status = 'in_progress'

    db.commit()
    return {"ok": True}

@router.post("/{order_id}/steps/{step_id}/skip")
def skip_step(order_id: int, step_id: int, db: Session = Depends(get_db)):
    step = db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id, models.ProcessStep.flow_id == db.query(models.ProcessFlow.id).filter(models.ProcessFlow.order_id == order_id).scalar_subquery()).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    if step.required:
        raise HTTPException(status_code=400, detail="必做工序不能跳过")
    step.status = 'skipped'
    
    # Check if this triggers order auto-completion
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.order_id == order_id).first()
    all_steps = db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == flow.id).order_by(models.ProcessStep.seq).all()
    all_completed = True
    for s in all_steps:
        if s.status not in ('completed', 'skipped'):
            all_completed = False
            break
    if all_completed:
        prev_status = order.status
        order.status = 'completed'
        if prev_status != 'completed':
            _notify_order_completed(order, db)

    db.commit()
    return {"ok": True}

# ────────────────────────── 订单用料（零配件）管理 ──────────────────────────

@router.get("/{order_id}/materials")
def get_order_materials(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    reservations = (
        db.query(models.InventoryReservation)
        .filter(models.InventoryReservation.order_id == order_id)
        .all()
    )
    
    result = []
    for res in reservations:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == res.item_id).first()
        result.append({
            "id": res.id,
            "item_id": res.item_id,
            "quantity": res.quantity,
            "item_name": item.name if item else "未知配件",
            "spec": item.spec if item else "",
            "unit": item.unit if item else "件",
            "total": item.total if item else 0,
            "reserved": item.reserved if item else 0
        })
    return result

class MaterialAdd(BaseModel):
    item_id: int
    quantity: int

@router.post("/{order_id}/materials")
def add_order_material(order_id: int, req: MaterialAdd, db: Session = Depends(get_db),
                       current_user: models.User = Depends(require_inventory_edit)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "completed":
        raise HTTPException(status_code=400, detail="订单已完成，不能修改或添加用料")

    # 预留经服务层：订单存在校验 + 行锁 + 唯一约束合并 + 预警穿越评估（数据完整性 #6/#7 修复）
    svc.reserve_for_order(db, item_id=req.item_id, order_id=order_id, quantity=req.quantity)
    return {"ok": True}

@router.delete("/{order_id}/materials/{reservation_id}")
def delete_order_material(order_id: int, reservation_id: int, db: Session = Depends(get_db),
                          current_user: models.User = Depends(require_inventory_edit)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "completed":
        raise HTTPException(status_code=400, detail="订单已完成，不能删除已用用料")

    res = db.query(models.InventoryReservation).filter(
        models.InventoryReservation.id == reservation_id,
        models.InventoryReservation.order_id == order_id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="用料记录不存在")

    # 释放预留并回退 reserved 缓存列（经服务层，行锁保护）
    svc.release_reservation(db, res)
    db.commit()
    return {"ok": True}

@router.post("/{order_id}/release-reservations")
def release_order_reservations_ep(order_id: int, db: Session = Depends(get_db),
                                  current_user: models.User = Depends(require_inventory_edit)):
    """已完成订单释放剩余预留（驾驶舱"已完成未领料"风险的解决动作，PROD-2）。"""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    released = svc.release_completed_order_reservations(db, order)
    return {"ok": True, "released": released}


@router.get("/{order_id}/locate")
def locate_order_page(
    order_id: int, 
    db: Session = Depends(get_db),
    limit: int = 20,
    status: str = None,
    priority: str = None,
    keyword: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    customer_id: int = None
):
    query = db.query(models.Order)
    if customer_id:
        query = query.filter(models.Order.customer_id == customer_id)
    if keyword:
        query = query.filter(
            or_(
                models.Order.order_no.ilike(f"%{keyword}%"),
                models.Order.product_name.ilike(f"%{keyword}%"),
                models.Order.customer_name.ilike(f"%{keyword}%")
            )
        )
    if status:
        query = query.filter(models.Order.status == status)
    if priority is not None and priority != "":
        try:
            query = query.filter(models.Order.priority == int(priority))
        except ValueError:
            pass

    target_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not target_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if sort_by and hasattr(models.Order, sort_by):
        column = getattr(models.Order, sort_by)
        if sort_order == 'asc':
            query = query.order_by(asc(column))
        else:
            query = query.order_by(desc(column))
    else:
        query = query.order_by(desc(models.Order.created_at))

    all_ids = [r[0] for r in query.with_entities(models.Order.id).all()]
    try:
        idx = all_ids.index(order_id)
        page = (idx // limit) + 1
        return {"page": page}
    except ValueError:
        return {"page": 1}
