from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from sqlalchemy.dialects.postgresql import JSONB
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("", response_model=List[schemas.CustomerResponse])
def get_customers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, keyword: str = None):
    query = db.query(models.Customer)
    if keyword:
        kw_like = f"%{keyword}%"
        query = query.filter(
            or_(
                models.Customer.name.ilike(kw_like),
                models.Customer.contact.ilike(kw_like),
                models.Customer.phone.ilike(kw_like),
                models.Customer.wechat.ilike(kw_like),
                models.Customer.email.ilike(kw_like),
                cast(cast(models.Customer.contacts, JSONB), String).ilike(kw_like)
            )
        )
    customers = query.order_by(models.Customer.name).offset(skip).limit(limit).all()
    return customers

@router.post("", response_model=schemas.CustomerResponse)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    if not customer.name or not customer.name.strip():
        raise HTTPException(status_code=400, detail="Customer name cannot be empty")
        
    for m in (customer.contact_methods or []):
        if not m.get('type') or not str(m.get('type')).strip():
            raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
        if not m.get('value') or not str(m.get('value')).strip():
            raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    for c in (customer.contacts or []):
        if not c.name or not c.name.strip():
            raise HTTPException(status_code=400, detail="联系人姓名不能为空")
        for m in (c.contact_methods or []):
            if not m.type or not m.type.strip():
                raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
            if not m.value or not m.value.strip():
                raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    db_customer = models.Customer(**customer.model_dump())
    if db_customer.contacts:
        db_customer.contact = db_customer.contacts[0].get('name', '')
        # Find the first phone value
        methods = db_customer.contacts[0].get('contact_methods', [])
        phone_val = ""
        for m in methods:
            if not phone_val:
                phone_val = m.get('value', '')
            if m.get('type') == '电话':
                phone_val = m.get('value', '')
                break
        db_customer.phone = phone_val
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(customer_id: int, customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.name or not customer.name.strip():
        raise HTTPException(status_code=400, detail="Customer name cannot be empty")

    for m in (customer.contact_methods or []):
        if not m.get('type') or not str(m.get('type')).strip():
            raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
        if not m.get('value') or not str(m.get('value')).strip():
            raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    for c in (customer.contacts or []):
        if not c.name or not c.name.strip():
            raise HTTPException(status_code=400, detail="联系人姓名不能为空")
        for m in (c.contact_methods or []):
            if not m.type or not m.type.strip():
                raise HTTPException(status_code=400, detail="联系方式的类型不能为空")
            if not m.value or not m.value.strip():
                raise HTTPException(status_code=400, detail="联系方式的值不能为空")

    update_data = customer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    
    if db_customer.contacts:
        db_customer.contact = db_customer.contacts[0].get('name', '')
        # Find the first phone value
        methods = db_customer.contacts[0].get('contact_methods', [])
        phone_val = ""
        for m in methods:
            if not phone_val:
                phone_val = m.get('value', '')
            if m.get('type') == '电话':
                phone_val = m.get('value', '')
                break
        db_customer.phone = phone_val
    
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(db_customer)
    db.commit()
    return {"ok": True}

@router.get("/{customer_id}/orders", response_model=List[schemas.OrderResponse])
def get_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.customer_id == customer_id).all()
    return orders

@router.get("/{customer_id}/stats")
def get_customer_stats(customer_id: int, db: Session = Depends(get_db)):
    total = db.query(models.Order).filter(models.Order.customer_id == customer_id).count()
    completed = db.query(models.Order).filter(models.Order.customer_id == customer_id, models.Order.status == "completed").count()
    in_progress = db.query(models.Order).filter(models.Order.customer_id == customer_id, models.Order.status == "in_progress").count()
    paused = db.query(models.Order).filter(models.Order.customer_id == customer_id, models.Order.status == "paused").count()
    
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "paused": paused
    }
