import os
import random
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
import models
from datetime import datetime, timedelta

def seed_mock():
    db = SessionLocal()
    try:
        print("Clearing old mock data...")
        # Clear existing data in correct dependency order
        db.query(models.Notification).delete()
        db.query(models.Vendor).delete()
        db.query(models.Document).delete()
        db.query(models.ProcessStep).delete()
        db.query(models.ProcessFlow).delete()
        db.query(models.Order).delete()
        db.query(models.InventoryItem).delete()
        db.query(models.Customer).delete()
        db.commit()
        
        # 1. Create Customers (5 items)
        print("Creating 5 customers...")
        customers_data = [
            {"name": "比亚迪汽车有限公司", "contact": "王总", "phone": "13800000001", "address": "深圳市坪山区", "notes": "VIP核心客户，注重交期", "contact_methods": [{"type": "电话", "value": "13800000001"}, {"type": "微信", "value": "byd_procure"}]},
            {"name": "特斯拉超级工厂(上海)", "contact": "马经理", "phone": "13900000002", "address": "上海市浦东新区", "notes": "外资大厂，流程严谨，图纸需版本受控", "contact_methods": [{"type": "邮箱", "value": "tesla_sh@tesla.com"}]},
            {"name": "富士康精密组件(深圳)", "contact": "郭课长", "phone": "13700000003", "address": "深圳市龙华区", "notes": "起量迅速，主要针对电子类模具", "contact_methods": [{"type": "电话", "value": "13700000003"}]},
            {"name": "格力电器股份有限公司", "contact": "董工", "phone": "13600000004", "address": "珠海市前山", "notes": "大尺寸面板热流道需求多", "contact_methods": [{"type": "微信", "value": "gree_dong"}]},
            {"name": "华为终端有限公司", "contact": "余总", "phone": "13500000005", "address": "东莞市松山湖", "notes": "高精度热流道定制需求", "contact_methods": [{"type": "电话", "value": "13500000005"}]}
        ]
        db_customers = []
        for c in customers_data:
            customer = models.Customer(**c)
            db.add(customer)
            db_customers.append(customer)
        db.commit()
        
        c_ids = [c.id for c in db_customers]
        
        # 2. Create 3 Process Flow Templates in Chinese (3 items)
        print("Creating 3 Chinese process flow templates...")
        template_flows = [
            {
                "name": "标准注塑模具工艺流程",
                "description": "适用于标准热流道注塑模具的制造和检验流程",
                "steps": [
                    {"name": "设计与三维建模", "assignee": "xiaoli", "required": 1},
                    {"name": "原材料采购", "assignee": "laowang", "required": 1},
                    {"name": "CNC粗加工", "assignee": "laowang", "required": 1},
                    {"name": "热处理", "assignee": "laowang", "required": 1, "outsourced": 1},
                    {"name": "精密磨削", "assignee": "laowang", "required": 1},
                    {"name": "模具装配", "assignee": "laowang", "required": 1},
                    {"name": "试模与品质检验", "assignee": "admin", "required": 1}
                ]
            },
            {
                "name": "热流道分流板加工工艺流程",
                "description": "适用于非标定制热流道板的精密深孔加工和通电测试",
                "steps": [
                    {"name": "流道板图纸审核", "assignee": "xiaoli", "required": 1},
                    {"name": "毛坯下料与打磨", "assignee": "laowang", "required": 1},
                    {"name": "深孔钻孔加工", "assignee": "laowang", "required": 1, "outsourced": 1},
                    {"name": "流道内部抛光", "assignee": "laowang", "required": 1},
                    {"name": "加热元件与热电偶安装", "assignee": "laowang", "required": 1},
                    {"name": "通电加热平衡测试", "assignee": "admin", "required": 1}
                ]
            },
            {
                "name": "非标定制加热器流程",
                "description": "适用于非标定制电加热圈、加热棒的生产和绝缘检测",
                "steps": [
                    {"name": "电气方案设计", "assignee": "xiaoli", "required": 1},
                    {"name": "管材弯曲成型", "assignee": "laowang", "required": 1},
                    {"name": "绝缘氧化镁填充", "assignee": "laowang", "required": 1},
                    {"name": "高温高压绝缘测试", "assignee": "admin", "required": 1},
                    {"name": "激光表面打标", "assignee": "laowang", "required": 0}
                ]
            }
        ]
        
        db_templates = []
        for tf_data in template_flows:
            flow = models.ProcessFlow(
                name=tf_data["name"],
                description=tf_data["description"],
                is_template=1
            )
            db.add(flow)
            db.commit()
            db.refresh(flow)
            
            for seq, s in enumerate(tf_data["steps"], 1):
                step = models.ProcessStep(
                    flow_id=flow.id,
                    name=s["name"],
                    seq=seq,
                    required=s["required"],
                    outsourced=s.get("outsourced", 0),
                    assignee=s["assignee"],
                    status="pending"
                )
                db.add(step)
            db.commit()
            db_templates.append(flow)
            
        # 3. Create 5 Inventory Items in Chinese (5 items)
        print("Creating 5 Chinese inventory items...")
        inventory_data = [
            {"name": "标准热咀 A1", "spec": "10mm / 开放式", "total": 120, "reserved": 20, "unit": "件", "alert_threshold": 50},
            {"name": "加热圈 B2", "spec": "220V / 500W / 直径30mm", "total": 12, "reserved": 8, "unit": "件", "alert_threshold": 15}, # Trigger alert
            {"name": "温控箱 C3", "spec": "8点式智能温控 / 双组PID", "total": 4, "reserved": 1, "unit": "台", "alert_threshold": 5},   # Trigger alert
            {"name": "热电偶 K型", "spec": "M12螺纹 / 长度100mm", "total": 200, "reserved": 15, "unit": "支", "alert_threshold": 30},
            {"name": "流道板密封圈", "spec": "15mm / 高温紫铜", "total": 300, "reserved": 50, "unit": "个", "alert_threshold": 100}
        ]
        for item_data in inventory_data:
            item = models.InventoryItem(**item_data)
            db.add(item)
        db.commit()
        
        # 4. Create 3 Vendors (3 items)
        print("Creating 3 vendors...")
        vendors_data = [
            {"name": "东莞市精雕机械外协厂", "contact": "张厂长", "phone": "13111112222", "address": "东莞市大岭山镇精雕工业园", "notes": "专注于深孔钻、CNC精密雕刻加工", "contact_methods": [{"type": "电话", "value": "13111112222"}]},
            {"name": "深圳市博森热处理有限公司", "contact": "李工", "phone": "13222223333", "address": "深圳市宝安区沙井街道", "notes": "提供淬火、回火、真空热处理服务", "contact_methods": [{"type": "微信", "value": "bosen_heat"}]},
            {"name": "惠州市恒泰表面处理厂", "contact": "陈经理", "phone": "13333334444", "address": "惠州市仲恺高新区", "notes": "电镀、防锈阳极氧化等表面工程", "contact_methods": [{"type": "电话", "value": "13333334444"}]}
        ]
        for vendor_data in vendors_data:
            vendor = models.Vendor(**vendor_data)
            db.add(vendor)
        db.commit()
        
        # 5. Create 3 Notifications (3 items)
        print("Creating 3 notifications...")
        notifications_data = [
            {"from_user_id": 1, "to_user_id": 1, "title": "系统提醒: 订单交付期预警", "body": "订单 ORD-2026-0002 交付期仅剩 5 天，请合理安排工期。", "source": "auto", "link": "/orders"},
            {"from_user_id": 1, "to_user_id": 1, "title": "物料库存告急通知", "body": "库存商品『温控箱 C3』库存数(4台)已低于预警水位(5台)，请尽快采购补充！", "source": "auto", "link": "/inventory"},
            {"from_user_id": 1, "to_user_id": 1, "title": "新工序派工通知", "body": "您已被指派为订单 ORD-2026-0005『试模与品质检验』工序的执行人。", "source": "manual", "link": "/orders"}
        ]
        for notif_data in notifications_data:
            notif = models.Notification(**notif_data)
            db.add(notif)
        db.commit()

        # 6. Create 25 Orders with random template assignment (25 items)
        print("Creating 25 orders & assigning process flows...")
        product_names = [
            "Model Y仪表盘热流道系统", "卡罗拉前保险杠热流道板", "iPhone 18 Pro金属中框模具", 
            "大疆无人机机身模具", "格力空调面板针阀式热嘴", "华为Mate 80后壳热流道", 
            "迈腾车门内衬板热流道", "四腔针阀式热流道系统", "八腔开放式侧浇口系统", 
            "精密医疗移液嘴热流道", "比亚迪秦Plus保险杠热嘴", "宁德时代电池外壳注塑模",
            "奔驰E级中网热流道板", "飞利浦剃须刀外壳模具", "小米智能手环腕带模具",
            "联想笔记本A壳热流道", "美的电饭煲顶盖热嘴", "奥迪Q5前大灯灯罩模具",
            "海信电视机后盖热流道", "高精密多腔注射针筒热嘴", "丰田RAV4中控台分流板",
            "小鹏P7尾灯双色注塑模", "理想L9进气格栅热流道", "双回路高功率加热元件组",
            "标准十孔针阀分流板"
        ]
        
        today = datetime.now()
        
        # We want to distribute status: e.g. 15 in_progress, 6 completed, 4 paused
        statuses = ["in_progress"] * 15 + ["completed"] * 6 + ["paused"] * 4
        random.shuffle(statuses)
        
        for idx in range(1, 26):
            order_no = f"ORD-2026-{idx:04d}"
            prod_name = product_names[idx - 1]
            cust_id = random.choice(c_ids)
            priority = random.choice([0, 1, 2]) # 0=普通, 1=紧急, 2=特急
            status = statuses[idx - 1]
            ship_days = random.choice([5, 10, 15, 20, 25, -2, -5]) # some past, some future
            
            # Find customer name
            cust_name = next(c.name for c in db_customers if c.id == cust_id)
            
            order = models.Order(
                order_no=order_no,
                product_name=prod_name,
                customer_id=cust_id,
                customer_name=cust_name,
                priority=priority,
                status=status,
                shipment_date=today + timedelta(days=ship_days),
                notes=f"第 {idx} 号自动生成的测试订单，由种子脚本提供。",
                created_by=1
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            
            # Select random template
            tpl = random.choice(db_templates)
            
            # Copy template flow to order
            order_flow = models.ProcessFlow(
                name=f"Flow for {order.order_no}",
                description=tpl.description,
                is_template=0,
                order_id=order.id
            )
            db.add(order_flow)
            db.commit()
            db.refresh(order_flow)
            
            # Retrieve template steps
            tpl_steps = db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == tpl.id).order_by(models.ProcessStep.seq).all()
            
            # Determine active step index if not completed
            num_steps = len(tpl_steps)
            active_step_idx = random.randint(0, num_steps - 1) if status in ["in_progress", "paused"] else num_steps
            
            order_steps = []
            for s_idx, t_step in enumerate(tpl_steps):
                # Set step status based on order status and step index
                if status == "completed":
                    step_status = "completed"
                else: # in_progress or paused
                    if s_idx < active_step_idx:
                        step_status = "completed"
                    elif s_idx == active_step_idx:
                        step_status = "in_progress"
                    else:
                        step_status = "pending"
                
                new_step = models.ProcessStep(
                    flow_id=order_flow.id,
                    name=t_step.name,
                    seq=t_step.seq,
                    required=t_step.required,
                    outsourced=t_step.outsourced,
                    assignee=t_step.assignee,
                    status=step_status,
                    started_at=today - timedelta(days=s_idx + 1) if step_status in ["completed", "in_progress"] else None,
                    completed_at=today - timedelta(days=s_idx) if step_status == "completed" else None
                )
                db.add(new_step)
                order_steps.append(new_step)
            db.commit()
            
            # Assign current_step_id
            active_step = next((s for s in order_steps if s.status == "in_progress"), None)
            if not active_step:
                active_step = next((s for s in order_steps if s.status == "pending"), None)
            if not active_step:
                active_step = order_steps[-1] if order_steps else None
                
            if active_step:
                order.current_step_id = active_step.id
                db.commit()
                
        # Hack to trigger today_done because updated_at is auto-set by DB trigger or SQLAlchemy
        completed_orders = db.query(models.Order).filter(models.Order.status=="completed").all()
        for co in completed_orders:
            co.updated_at = today
        db.commit()
        
        print("Mock data generated successfully!")
        print(f"Stats: 5 Customers, 3 Templates, 5 Inventory Items, 3 Vendors, 3 Notifications, 25 Orders.")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_mock()
