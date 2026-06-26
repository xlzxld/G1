import os
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
import models
from datetime import datetime, timedelta

def seed_mock():
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(models.Document).delete()
        db.query(models.ProcessStep).delete()
        db.query(models.ProcessFlow).delete()
        db.query(models.Order).delete()
        db.query(models.InventoryItem).delete()
        db.query(models.Customer).delete()
        db.commit()
        
        # 1. Create Customers
        customers = [
            models.Customer(
                name="Tesla Gigafactory Shanghai",
                contact="Elon M.",
                phone="13800000001",
                address="Shanghai",
                notes="VIP Client",
                contact_methods=[{"type": "电话", "value": "13800000001"}]
            ),
            models.Customer(
                name="Foxconn Technology",
                contact="Terry G.",
                phone="13900000002",
                address="Shenzhen",
                notes="Urgent orders mostly",
                contact_methods=[{"type": "邮箱", "value": "contact@foxconn.com"}]
            ),
            models.Customer(
                name="BYD Auto",
                contact="Wang C.",
                phone="13700000003",
                address="Shenzhen",
                notes="High volume",
                contact_methods=[{"type": "微信", "value": "byd_procurement"}]
            )
        ]
        db.add_all(customers)
        db.commit()
        
        db_customers = db.query(models.Customer).all()
        c_ids = [c.id for c in db_customers]
        
        # 2. Create Inventory Items
        items = [
            models.InventoryItem(name="Standard Hot Nozzle A1", spec="10mm", total=100, reserved=20, unit="pcs", alert_threshold=50),
            models.InventoryItem(name="Heating Coil B2", spec="220V", total=10, reserved=5, unit="pcs", alert_threshold=15), # Trigger alert
            models.InventoryItem(name="Temperature Controller C3", spec="Digital", total=5, reserved=0, unit="sets", alert_threshold=10) # Trigger alert
        ]
        db.add_all(items)
        db.commit()
        
        # 3. Create Process Flow Template
        flow = models.ProcessFlow(
            name="Standard Injection Mold Flow",
            description="Default steps for standard hot runner systems",
            is_template=1
        )
        db.add(flow)
        db.commit()
        
        steps_data = [
            {"name": "Design & CAD", "seq": 1, "assignee": "xiaoli", "status": "completed"},
            {"name": "Material Procurement", "seq": 2, "assignee": "laowang", "status": "completed"},
            {"name": "CNC Machining", "seq": 3, "assignee": "laowang", "status": "in_progress"},
            {"name": "Assembly", "seq": 4, "assignee": "laowang", "status": "pending"},
            {"name": "Quality Inspection", "seq": 5, "assignee": "admin", "status": "pending"}
        ]
        
        for s in steps_data:
            step = models.ProcessStep(flow_id=flow.id, **s)
            db.add(step)
        db.commit()
        
        # 4. Create Orders
        today = datetime.now()
        orders = [
            models.Order(
                order_no="ORD-2026-0001",
                product_name="Model 3 Dashboard Hot Runner",
                customer_id=c_ids[0],
                priority=2, # 特急
                status="in_progress",
                shipment_date=today + timedelta(days=10),
                notes="Need to rush this order"
            ),
            models.Order(
                order_no="ORD-2026-0002",
                product_name="iPhone 18 Casing Mold",
                customer_id=c_ids[1],
                priority=1, # 紧急
                status="draft",
                shipment_date=today + timedelta(days=5)
            ),
            models.Order(
                order_no="ORD-2026-0003",
                product_name="Seal Ring Component",
                customer_id=c_ids[2],
                priority=0, # 普通
                status="completed",
                shipment_date=today - timedelta(days=1)
            )
        ]
        db.add_all(orders)
        db.commit()
        
        # 5. Assign Flow to Orders
        for order in orders:
            order_flow = models.ProcessFlow(
                name=f"Flow for {order.order_no}",
                is_template=0,
                order_id=order.id
            )
            db.add(order_flow)
            db.commit()
            
            for i, s in enumerate(steps_data):
                step_status = "pending"
                if order.status == "completed":
                    step_status = "completed"
                elif order.status == "in_progress":
                    if i < 2:
                        step_status = "completed"
                    elif i == 2:
                        step_status = "in_progress"
                        
                order_step = models.ProcessStep(
                    flow_id=order_flow.id,
                    name=s["name"],
                    seq=s["seq"],
                    assignee=s["assignee"],
                    status=step_status
                )
                db.add(order_step)
            db.commit()
        
        # Hack to trigger today_done because updated_at is auto-set by DB trigger or SQLAlchemy
        db.query(models.Order).filter(models.Order.order_no=="ORD-2026-0003").update({"updated_at": today})
        db.commit()
        
        print("Mock data generated successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_mock()
