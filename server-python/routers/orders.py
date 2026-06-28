from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/orders", tags=["orders"])

from sqlalchemy import or_, desc, asc

@router.get("")
def get_orders(
    db: Session = Depends(get_db), 
    page: int = 1, 
    limit: int = 20,
    keyword: str = None,
    status: str = None,
    priority: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    query = db.query(models.Order)
    
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
            "current_step_name": ""
        }
        if order.current_step_id:
            step = db.query(models.ProcessStep).filter(models.ProcessStep.id == order.current_step_id).first()
            if step:
                order_dict["current_step_name"] = step.name
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
        
    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
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

def check_inventory_alert(item_id: int, db: Session):
    try:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
        if item:
            available = item.total - item.reserved
            if available <= item.alert_threshold:
                from routers.notifications import trigger_notification_rules
                context = {
                    "id": item.id,
                    "name": item.name,
                    "spec": item.spec or "",
                    "total": item.total,
                    "reserved": item.reserved,
                    "available": available,
                    "alert_threshold": item.alert_threshold
                }
                trigger_notification_rules("inventory_alert", context, db)
    except Exception as e:
        print(f"Check inventory alert failed: {e}")

def deduct_order_inventory(order: models.Order, db: Session):
    # 如果已经扣减过，或者非已完成状态，不做重复扣减
    if order.status != "completed" or order.inventory_deducted == 1:
        return
    
    # 查找该订单的所有用料预留并联动核销
    reservations = db.query(models.InventoryReservation).filter(models.InventoryReservation.order_id == order.id).all()
    if not reservations:
        # 如果当前订单没有分配用料，不写入扣减完成标记，留待后续有物料时结转
        return
        
    for res in reservations:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == res.item_id).with_for_update().first()
        if item:
            # 扣减总量与已预留量
            item.total = max(0, item.total - res.quantity)
            item.reserved = max(0, item.reserved - res.quantity)
            db.commit() # 提前提交以便 check_inventory_alert 获取最新值
            check_inventory_alert(res.item_id, db)
            
    order.inventory_deducted = 1
    
    # 触发订单完成通知
    try:
        from routers.notifications import trigger_notification_rules
        order_dict = {
            "id": order.id,
            "order_no": order.order_no,
            "product_name": order.product_name,
            "status": order.status,
            "priority": order.priority,
            "notes": order.notes or ""
        }
        trigger_notification_rules("order_completed", order_dict, db)
    except Exception as e:
        print(f"Order completed notify failed: {e}")

def rollback_order_inventory(order: models.Order, db: Session):
    # 如果未做扣减，或者仍处于已完成状态，不做回滚
    if order.inventory_deducted != 1:
        return
        
    # 查找该订单的所有用料预留并联动还原
    reservations = db.query(models.InventoryReservation).filter(models.InventoryReservation.order_id == order.id).all()
    for res in reservations:
        item = db.query(models.InventoryItem).filter(models.InventoryItem.id == res.item_id).with_for_update().first()
        if item:
            # 还原总量与已预留量
            item.total = item.total + res.quantity
            item.reserved = item.reserved + res.quantity
            
    order.inventory_deducted = 0

from pydantic import BaseModel
class StatusUpdate(BaseModel):
    status: str

@router.put("/{order_id}/status")
def update_order_status(order_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # 如果订单从已完成退回到其他非完成状态，执行库存联动还原
    if order.status == "completed" and payload.status != "completed":
        rollback_order_inventory(order, db)
        
    order.status = payload.status
    if payload.status == "completed":
        deduct_order_inventory(order, db)
        
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
        order.status = 'completed'
        deduct_order_inventory(order, db)

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
    
    # 联动还原已经扣除的库存，并恢复其预留锁定状态
    rollback_order_inventory(order, db)
    
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
        order.status = 'completed'
        deduct_order_inventory(order, db)

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
def add_order_material(order_id: int, req: MaterialAdd, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status == "completed":
        raise HTTPException(status_code=400, detail="订单已完成，不能修改或添加用料")

    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="用料数量必须大于0")

    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == req.item_id).with_for_update().first()
    if not db_item:
        raise HTTPException(status_code=404, detail="所选零配件不存在")

    available = db_item.total - db_item.reserved
    if req.quantity > available:
        raise HTTPException(status_code=400, detail=f"「{db_item.name}」可用库存不足！当前可用库存为 {available} {db_item.unit}")

    # 如果对该订单下同一零配件重复添加，则合并数量
    existing = db.query(models.InventoryReservation).filter(
        models.InventoryReservation.order_id == order_id,
        models.InventoryReservation.item_id == req.item_id
    ).first()

    if existing:
        existing.quantity += req.quantity
    else:
        new_res = models.InventoryReservation(
            order_id=order_id,
            item_id=req.item_id,
            quantity=req.quantity
        )
        db.add(new_res)

    db_item.reserved += req.quantity
    db.commit()
    check_inventory_alert(req.item_id, db)
    return {"ok": True}

@router.delete("/{order_id}/materials/{reservation_id}")
def delete_order_material(order_id: int, reservation_id: int, db: Session = Depends(get_db)):
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

    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == res.item_id).with_for_update().first()
    if db_item:
        db_item.reserved = max(0, db_item.reserved - res.quantity)

    db.delete(res)
    db.commit()
    check_inventory_alert(res.item_id, db)
    return {"ok": True}
