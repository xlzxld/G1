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
            
        # 3. Create 25 Inventory Items in Chinese (25 items)
        print("Creating 25 Chinese inventory items...")
        inventory_data = [
            {"name": "标准热咀 A1", "spec": "10mm / 开放式", "total": 120, "reserved": 20, "unit": "件", "alert_threshold": 50},
            {"name": "加热圈 B2", "spec": "220V / 500W / 直径30mm", "total": 12, "reserved": 8, "unit": "件", "alert_threshold": 15}, # Trigger alert
            {"name": "温控箱 C3", "spec": "8点式智能温控 / 双组PID", "total": 4, "reserved": 1, "unit": "台", "alert_threshold": 5},   # Trigger alert
            {"name": "热电偶 K型", "spec": "M12螺纹 / 长度100mm", "total": 200, "reserved": 15, "unit": "支", "alert_threshold": 30},
            {"name": "流道板密封圈", "spec": "15mm / 高温紫铜", "total": 300, "reserved": 50, "unit": "个", "alert_threshold": 100},
            {"name": "针阀嘴针阀针", "spec": "直径2.0mm / 长度250mm", "total": 50, "reserved": 10, "unit": "支", "alert_threshold": 15},
            {"name": "热流道分流板 A型", "spec": "双腔 / 标准开放式", "total": 15, "reserved": 5, "unit": "块", "alert_threshold": 6},
            {"name": "单点热咀 H1", "spec": "针阀式 / 150mm", "total": 30, "reserved": 12, "unit": "件", "alert_threshold": 10},
            {"name": "重载接插件", "spec": "16针 / 16A / 侧出", "total": 80, "reserved": 25, "unit": "套", "alert_threshold": 20},
            {"name": "高温补偿导线", "spec": "K型双芯 / 玻纤屏蔽", "total": 1000, "reserved": 150, "unit": "米", "alert_threshold": 200},
            {"name": "陶瓷加热圈", "spec": "220V / 1000W / 直径50mm", "total": 25, "reserved": 5, "unit": "件", "alert_threshold": 10},
            {"name": "感温线 J型", "spec": "弹簧压紧式 / 2米", "total": 150, "reserved": 30, "unit": "支", "alert_threshold": 40},
            {"name": "针阀气缸 C1", "spec": "单组气动 / 高温密封", "total": 18, "reserved": 4, "unit": "套", "alert_threshold": 8},
            {"name": "分流板垫块", "spec": "直径25mm / 钛合金", "total": 200, "reserved": 60, "unit": "个", "alert_threshold": 50},
            {"name": "中心定位销", "spec": "直径16mm / 高精度", "total": 120, "reserved": 30, "unit": "件", "alert_threshold": 30},
            {"name": "防漏金属垫圈", "spec": "直径12mm / 纯铜", "total": 500, "reserved": 100, "unit": "个", "alert_threshold": 150},
            {"name": "电热管加热棒", "spec": "单头 / 10mm * 150mm / 400W", "total": 70, "reserved": 15, "unit": "支", "alert_threshold": 25},
            {"name": "温控箱控制卡", "spec": "单段PID微电脑控制板", "total": 35, "reserved": 8, "unit": "块", "alert_threshold": 10},
            {"name": "重载连接器防护罩", "spec": "双扣金属上壳 / PG21", "total": 45, "reserved": 10, "unit": "个", "alert_threshold": 12},
            {"name": "感温针保护套管", "spec": "304不锈钢 / 8mm * 100mm", "total": 90, "reserved": 20, "unit": "支", "alert_threshold": 20},
            {"name": "分流板加热管", "spec": "柔性加热管 / 长度800mm", "total": 40, "reserved": 15, "unit": "根", "alert_threshold": 15},
            {"name": "气动针阀控制电磁阀", "spec": "五通二位 / 24VDC", "total": 22, "reserved": 6, "unit": "只", "alert_threshold": 8},
            {"name": "高温接线瓷介", "spec": "两极 / 螺钉紧固", "total": 400, "reserved": 80, "unit": "只", "alert_threshold": 100},
            {"name": "高强度模具弹簧", "spec": "重载棕色 / 25mm * 80mm", "total": 110, "reserved": 40, "unit": "件", "alert_threshold": 30},
            {"name": "气源三联件", "spec": "过滤减压油雾 / PT1/4", "total": 14, "reserved": 3, "unit": "套", "alert_threshold": 5}
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
        
        # 7. Generate 30 unread notifications referencing real order/inventory IDs
        print("Creating 30 random unread notifications...")

        db_orders = db.query(models.Order).all()
        db_inventory = db.query(models.InventoryItem).all()
        db_users = db.query(models.User).all()
        all_user_ids = [u.id for u in db_users] or [1]

        now_n = datetime.now()
        month_start_n = now_n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        notif_templates = [
            ("订单交付期预警", "订单 {order_no}（{product_name}）交付期仅剩 {days} 天，请合理安排工期！", "auto", "order"),
            ("工序进度滞后提醒", "订单 {order_no} 当前工序『{step}』已超期，请跟进处理。", "auto", "order"),
            ("优先级变更通知", "订单 {order_no} 优先级已调整为【特急】，请优先安排生产资源。", "manual", "order"),
            ("物料库存告急", "库存物料『{item_name}』当前库存 {total} {unit}，已低于预警水位 {threshold} {unit}，请尽快补货！", "auto", "inventory"),
            ("物料预留成功", "已为订单 {order_no} 成功预留物料『{item_name}』× {qty} {unit}。", "auto", "inventory"),
            ("新工序派工", "您已被指派为订单 {order_no}『{step}』工序执行人，请及时确认。", "manual", "order"),
            ("外协返件提醒", "订单 {order_no} 外协工序『{step}』预计今日返件，请安排接收检验。", "auto", "order"),
            ("订单状态变更", "订单 {order_no} 状态已由【进行中】更新为【{status}】。", "auto", "order"),
            ("图纸版本更新", "订单 {order_no} 的技术图纸已更新至新版本，请下载最新版本核对。", "manual", "order"),
            ("库存盘点提醒", "本月库存盘点即将开始，请核对物料『{item_name}』的实物数量。", "auto", "inventory"),
        ]
        step_names_n = ["设计与三维建模", "原材料采购", "CNC粗加工", "热处理", "精密磨削",
                        "模具装配", "试模与品质检验", "深孔钻孔加工", "流道内部抛光",
                        "通电加热平衡测试", "高温高压绝缘测试"]
        status_labels_n = {"in_progress": "进行中", "completed": "已完成", "paused": "已暂停"}

        generated = 0
        for _ in range(30):
            tpl_title, tpl_body, source, link_type = random.choice(notif_templates)
            to_user_id = 1  # 全部发给 admin 用户，确保登录后30条全部可见

            seconds_in_month = int((now_n - month_start_n).total_seconds())
            rand_seconds = random.randint(0, max(seconds_in_month, 1))
            created_time = month_start_n + timedelta(seconds=rand_seconds)

            order = random.choice(db_orders) if db_orders else None
            item = random.choice(db_inventory) if db_inventory else None
            step = random.choice(step_names_n)
            days = random.randint(1, 10)
            qty = random.randint(1, 20)

            ctx = {
                "order_no": order.order_no if order else "ORD-N/A",
                "product_name": order.product_name if order else "未知产品",
                "step": step,
                "days": days,
                "item_name": item.name if item else "未知物料",
                "total": item.total if item else 0,
                "unit": item.unit if item else "件",
                "threshold": item.alert_threshold if item else 5,
                "qty": qty,
                "status": random.choice(list(status_labels_n.values())),
            }

            body = tpl_body.format(**ctx)

            if link_type == "order" and order:
                link = f"/orders?highlight={order.id}"
            elif link_type == "inventory" and item:
                link = f"/inventory?highlight={item.id}"
            else:
                link = ""

            notif = models.Notification(
                from_user_id=1,
                to_user_id=to_user_id,
                title=tpl_title,
                body=body,
                source=source,
                link=link,
                is_read=0,
                created_at=created_time,
            )
            db.add(notif)
            generated += 1

        db.commit()
        print(f"  → {generated} unread notifications created.")

        print("Mock data generated successfully!")
        print(f"Stats: 5 Customers, 3 Templates, 25 Inventory Items, 3 Vendors, 30 Notifications, 25 Orders.")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_mock()
