"""V3 库存域集成测试——流水账本/预留闭环/删除守卫/预警穿越/迁移一致性。

对应测试计划：~/.gstack/projects/xlzxld-G1/xlzxld-V2-eng-review-test-plan-20260906.md
运行：见 tests/conftest.py 模块注释（后端容器内执行）。
"""
import pytest
from sqlalchemy import inspect, text
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

import models
from services import inventory_service as svc
from database import Base

pytestmark = pytest.mark.integration


# ────────────────────────── 鉴权边界 ──────────────────────────

def test_unauthenticated_blocked(client):
    resp = client.get("/inventory")
    assert resp.status_code == 401, "Router 级鉴权必须拦截匿名请求（P0-1）"


def test_non_admin_cannot_create_item(client, make_user):
    _, headers = make_user(username="worker1", is_admin=0)
    resp = client.post("/inventory", json={"name": "x"}, headers=headers)
    assert resp.status_code == 403, "物料主数据仅管理员（D13 两档权限）"


def test_view_only_user_cannot_write_movements(client, make_user, db):
    """回归：ISSUE-006（/qa 2026-09-06）——can_view 无 can_edit 的用户直接打 API
    曾可写库存（前端隐藏按钮=权限幻觉）。后端必须 403。"""
    user, headers = make_user(username="viewer1", is_admin=0)
    db.add(models.PagePermission(user_id=user.id, page_key="inventory", can_view=1, can_edit=0))
    db.flush()
    item = models.InventoryItem(name="权限测试料", total=10)
    db.add(item)
    db.flush()

    resp = client.post(f"/inventory/{item.id}/movements",
                       json={"type": "INBOUND", "quantity": 5}, headers=headers)
    assert resp.status_code == 403, "can_edit=0 的用户写流水必须 403（后端强制，非仅前端隐藏）"
    assert item.total == 10, "被拒操作不得留下任何库存变更"


# ────────────────────────── 流水账本基础 ──────────────────────────

def test_create_item_writes_opening_ledger(client, make_user, db):
    _, headers = make_user(username="admin1", is_admin=1)
    resp = client.post("/inventory", json={
        "name": "热嘴A", "spec": "10mm", "category": "热嘴",
        "location": "A-01", "unit": "件", "min_stock": 5, "total": 100,
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    item_id = resp.json()["id"]

    mv = client.get(f"/inventory/{item_id}/movements", headers=headers).json()
    assert len(mv) == 1
    assert mv[0]["type"] == "OPENING"
    assert mv[0]["quantity"] == 100 and mv[0]["balance_after"] == 100


def test_update_master_data_does_not_touch_total(client, make_user):
    _, headers = make_user(username="admin2", is_admin=1)
    item_id = client.post("/inventory", json={"name": "垫圈", "total": 50}, headers=headers).json()["id"]

    # 尝试通过编辑接口改总量（旧路径）——必须被忽略，total 不变
    resp = client.put(f"/inventory/{item_id}", json={"name": "垫圈", "total": 999}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 50, "PUT 不得直改 total（D10/D16）"


def test_inbound_outbound_roundtrip(client, make_user):
    _, headers = make_user(username="admin3", is_admin=1)
    item_id = client.post("/inventory", json={"name": "导线", "total": 0}, headers=headers).json()["id"]

    client.post(f"/inventory/{item_id}/movements",
                json={"type": "INBOUND", "quantity": 500, "batch_no": "B2026-01"}, headers=headers)
    resp = client.post(f"/inventory/{item_id}/movements",
                       json={"type": "OUTBOUND", "quantity": 120}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 380 and body["available"] == 380


def test_outbound_insufficient_stock_400(client, make_user):
    _, headers = make_user(username="admin4", is_admin=1)
    item_id = client.post("/inventory", json={"name": "垫块", "total": 10}, headers=headers).json()["id"]
    resp = client.post(f"/inventory/{item_id}/movements",
                       json={"type": "OUTBOUND", "quantity": 11}, headers=headers)
    assert resp.status_code == 400
    assert client.get(f"/inventory/{item_id}", headers=headers).json()["total"] == 10


def test_stocktake_adjustment(client, make_user):
    _, headers = make_user(username="admin5", is_admin=1)
    item_id = client.post("/inventory", json={"name": "弹簧", "total": 100}, headers=headers).json()["id"]
    resp = client.post(f"/inventory/{item_id}/movements",
                       json={"type": "ADJUSTMENT", "quantity": 77, "note": "月度盘点"}, headers=headers)
    assert resp.json()["total"] == 77
    mv = client.get(f"/inventory/{item_id}/movements", headers=headers).json()
    assert mv[0]["type"] == "ADJUSTMENT" and mv[0]["quantity"] == -23


# ────────────────────────── 预留与领退料闭环 ──────────────────────────

def _make_order(client, headers, db, order_no="ORD-T1"):
    cust = models.Customer(name="测试客户")
    db.add(cust)
    db.commit()
    resp = client.post("/orders", json={
        "order_no": order_no, "product_name": "测试热流道", "priority": 1,
        "customer_id": cust.id,
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def test_pick_consumes_reservation(client, make_user, db):
    _, headers = make_user(username="admin6", is_admin=1)
    item_id = client.post("/inventory", json={"name": "阀针", "total": 50}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db)
    client.post("/inventory/reserve",
                json={"item_id": item_id, "order_id": order_id, "quantity": 10}, headers=headers)

    resp = client.post(f"/inventory/{item_id}/movements",
                       json={"type": "OUTBOUND", "quantity": 6, "order_id": order_id}, headers=headers)
    body = resp.json()
    # 预留 10 消耗 6：reserved=4，total=44，available=40
    assert body["reserved"] == 4 and body["total"] == 44 and body["available"] == 40
    rows = db.query(models.InventoryReservation).filter_by(order_id=order_id, item_id=item_id).all()
    assert len(rows) == 1 and rows[0].quantity == 4


def test_overpick_allowed_and_reserved_cleared(client, make_user, db):
    _, headers = make_user(username="admin7", is_admin=1)
    item_id = client.post("/inventory", json={"name": "加热圈", "total": 30}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T2")
    client.post("/inventory/reserve",
                json={"item_id": item_id, "order_id": order_id, "quantity": 5}, headers=headers)

    resp = client.post(f"/inventory/{item_id}/movements",
                       json={"type": "OUTBOUND", "quantity": 8, "order_id": order_id}, headers=headers)
    body = resp.json()
    # 超领：预留 5 全部消耗，reserved=0，total=22
    assert body["reserved"] == 0 and body["total"] == 22
    assert db.query(models.InventoryReservation).filter_by(order_id=order_id).count() == 0


def test_return_restores_reservation_for_active_order(client, make_user, db):
    _, headers = make_user(username="admin8", is_admin=1)
    item_id = client.post("/inventory", json={"name": "感温线", "total": 20}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T3")
    client.post(f"/inventory/{item_id}/movements",
                json={"type": "OUTBOUND", "quantity": 5, "order_id": order_id}, headers=headers)

    resp = client.post(f"/inventory/{item_id}/movements",
                       json={"type": "RETURN", "quantity": 2, "order_id": order_id}, headers=headers)
    body = resp.json()
    # 退料 2 入账并恢复在制订单预留：total=17，reserved=2，available=15
    assert body["total"] == 17 and body["reserved"] == 2 and body["available"] == 15


def test_reserve_nonexistent_order_404(client, make_user):
    _, headers = make_user(username="admin9", is_admin=1)
    item_id = client.post("/inventory", json={"name": "垫片", "total": 10}, headers=headers).json()["id"]
    resp = client.post("/inventory/reserve",
                       json={"item_id": item_id, "order_id": 999999, "quantity": 1}, headers=headers)
    assert resp.status_code == 404, "预留必须校验订单存在（数据完整性 #7）"


def test_reserve_insufficient_400(client, make_user, db):
    _, headers = make_user(username="admin10", is_admin=1)
    item_id = client.post("/inventory", json={"name": "瓷介", "total": 5}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T4")
    resp = client.post("/inventory/reserve",
                       json={"item_id": item_id, "order_id": order_id, "quantity": 6}, headers=headers)
    assert resp.status_code == 400


def test_reserve_merge_respects_unique_constraint(client, make_user, db):
    _, headers = make_user(username="admin11", is_admin=1)
    item_id = client.post("/inventory", json={"name": "定位销", "total": 100}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T5")
    client.post("/orders/{oid}/materials".replace("{oid}", str(order_id)),
                json={"item_id": item_id, "quantity": 3}, headers=headers)
    client.post("/orders/{oid}/materials".replace("{oid}", str(order_id)),
                json={"item_id": item_id, "quantity": 4}, headers=headers)

    rows = db.query(models.InventoryReservation).filter_by(order_id=order_id, item_id=item_id).all()
    assert len(rows) == 1, "(order_id,item_id) 唯一约束：重复预留必须合并（数据完整性 #6）"
    assert rows[0].quantity == 7


# ────────────────────────── 删除守卫与回归 ──────────────────────────

def test_delete_order_releases_reservations(client, make_user, db):
    """回归测试（8/6 报告数据完整性 #1）：修复前 reserved 永久虚增。"""
    _, headers = make_user(username="admin12", is_admin=1)
    item_id = client.post("/inventory", json={"name": "密封圈", "total": 40}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T6")
    client.post("/inventory/reserve",
                json={"item_id": item_id, "order_id": order_id, "quantity": 10}, headers=headers)
    assert client.get(f"/inventory/{item_id}", headers=headers).json()["reserved"] == 10

    resp = client.delete(f"/orders/{order_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    item = client.get(f"/inventory/{item_id}", headers=headers).json()
    assert item["reserved"] == 0, "删除订单必须释放预留并回退 reserved"
    assert item["total"] == 40


def test_delete_order_with_movements_blocked(client, make_user, db):
    _, headers = make_user(username="admin13", is_admin=1)
    item_id = client.post("/inventory", json={"name": "阀针2", "total": 30}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T7")
    client.post(f"/inventory/{item_id}/movements",
                json={"type": "OUTBOUND", "quantity": 2, "order_id": order_id}, headers=headers)

    resp = client.delete(f"/orders/{order_id}", headers=headers)
    assert resp.status_code == 400, "有领料流水的订单禁止删除（D19）"


def test_delete_item_with_movements_blocked(client, make_user):
    _, headers = make_user(username="admin14", is_admin=1)
    item_id = client.post("/inventory", json={"name": " archival", "total": 5}, headers=headers).json()["id"]
    client.post(f"/inventory/{item_id}/movements",
                json={"type": "INBOUND", "quantity": 1}, headers=headers)
    resp = client.delete(f"/inventory/{item_id}", headers=headers)
    assert resp.status_code == 400, "有流水的物料禁止删除，应归档"
    # 归档路径可用
    resp = client.post(f"/inventory/{item_id}/archive", headers=headers)
    assert resp.status_code == 200 and resp.json()["is_archived"] == 1


def test_order_completion_does_not_touch_stock(client, make_user, db):
    """回归测试（D16）：订单完成不再自动扣减库存，领料 OUTBOUND 是唯一减 total 路径。"""
    _, headers = make_user(username="admin15", is_admin=1)
    item_id = client.post("/inventory", json={"name": "温控卡", "total": 35}, headers=headers).json()["id"]
    order_id = _make_order(client, headers, db, "ORD-T8")
    client.post("/inventory/reserve",
                json={"item_id": item_id, "order_id": order_id, "quantity": 8}, headers=headers)

    resp = client.put(f"/orders/{order_id}/status", json={"status": "completed"}, headers=headers)
    assert resp.status_code == 200
    item = client.get(f"/inventory/{item_id}", headers=headers).json()
    assert item["total"] == 35, "完成订单不得改 total（修复前 deduct_order_inventory 会直减）"
    assert item["reserved"] == 8, "完成订单不得改 reserved"


# ────────────────────────── 预警穿越 ──────────────────────────

def test_threshold_crossing_alerts_once(client, make_user, db):
    """D19：仅在向下穿越 min_stock 时告警一次，低水位内的连续变动不重复。"""
    user, headers = make_user(username="admin16", is_admin=1)
    db.add(models.NotificationRule(
        name="低库存预警", event="inventory_alert",
        condition_field="available", condition_op="lt", condition_value="6",
        notify_role=f"user_ids:{user.id}", title_template="库存告急 {name}", body_template="可用 {available}",
        is_active=1,
    ))
    item_id = client.post("/inventory", json={"name": "电磁阀", "total": 20, "min_stock": 5}, headers=headers).json()["id"]

    # 第一次领料：available 20 -> 4，向下穿越 → 1 条通知
    client.post(f"/inventory/{item_id}/movements",
                json={"type": "OUTBOUND", "quantity": 16}, headers=headers)
    first = db.query(models.Notification).filter_by(title="库存告急 电磁阀").count()
    assert first == 1, "穿越阈值应触发一次预警"

    # 低水位继续领料：4 -> 2，无穿越 → 不再新增
    client.post(f"/inventory/{item_id}/movements",
                json={"type": "OUTBOUND", "quantity": 2}, headers=headers)
    second = db.query(models.Notification).filter_by(title="库存告急 电磁阀").count()
    assert second == 1, "低水位内的变动不得重复告警（D19 防轰炸）"


# ────────────────────────── 采购（服务级） ──────────────────────────

def test_po_partial_receive_then_close(db, make_user):
    user, _ = make_user(username="admin17", is_admin=1)
    item = svc.create_item_with_opening(db, name="加热棒", opening_qty=0, operator_id=user.id)
    po = models.PurchaseOrder(po_no="PO-T1", item_id=item.id, quantity=10, status="ordered")
    db.add(po)
    db.commit()

    svc.receive_purchase(db, po=po, received_qty=4, operator_id=user.id)
    assert po.received_quantity == 4 and po.status == "ordered"
    assert item.total == 4, "到货必须生成 INBOUND 流水"

    svc.receive_purchase(db, po=po, received_qty=6, operator_id=user.id)
    assert po.received_quantity == 10 and po.status == "closed"
    assert item.total == 10


def test_po_receive_exceeds_remaining_400(db, make_user):
    user, _ = make_user(username="admin18", is_admin=1)
    item = svc.create_item_with_opening(db, name="加热棒2", opening_qty=0, operator_id=user.id)
    po = models.PurchaseOrder(po_no="PO-T2", item_id=item.id, quantity=5, status="ordered")
    db.add(po)
    db.commit()
    with pytest.raises(Exception):
        svc.receive_purchase(db, po=po, received_qty=6, operator_id=user.id)


def test_po_receival_blocked_after_closed(db, make_user):
    """幂等守卫：已完结采购单重复到货必须拒绝（双击/重试防护）。"""
    user, _ = make_user(username="admin19", is_admin=1)
    item = svc.create_item_with_opening(db, name="加热棒3", opening_qty=0, operator_id=user.id)
    po = models.PurchaseOrder(po_no="PO-T3", item_id=item.id, quantity=3, status="ordered")
    db.add(po)
    db.commit()
    svc.receive_purchase(db, po=po, received_qty=3, operator_id=user.id)
    with pytest.raises(Exception):
        svc.receive_purchase(db, po=po, received_qty=1, operator_id=user.id)
    assert item.total == 3, "重复到货不得重复入账"


# ────────────────────────── 账本一致性 ──────────────────────────

def test_ledger_consistency_after_operations(client, make_user, db):
    _, headers = make_user(username="admin20", is_admin=1)
    item_id = client.post("/inventory", json={"name": "三联件", "total": 14, "min_stock": 5}, headers=headers).json()["id"]
    client.post(f"/inventory/{item_id}/movements", json={"type": "INBOUND", "quantity": 20}, headers=headers)
    client.post(f"/inventory/{item_id}/movements", json={"type": "OUTBOUND", "quantity": 9}, headers=headers)
    client.post(f"/inventory/{item_id}/movements", json={"type": "ADJUSTMENT", "quantity": 30}, headers=headers)

    result = svc.verify_ledger_consistency(db, item_id)
    assert result["drift"] == 0, "缓存列必须等于 SUM(流水)"


# ────────────────────────── 迁移一致性（cutover 保险） ──────────────────────────

def test_alembic_head_schema_matches_models(tmp_path):
    """在全新临时库上跑 alembic upgrade head，断言结构与 Base.metadata 逐列一致。"""
    import os
    from alembic import command
    from alembic.config import Config

    # 注意：str(URL) 会掩码密码（SQLAlchemy 2.0），必须传 URL 对象或显式 render_as_string
    base_url = make_url(os.environ["DATABASE_URL"])
    mig_url = base_url.set(database="mes_mig_check")
    admin = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "mes_mig_check"'))
        conn.execute(text(f'CREATE DATABASE "mes_mig_check"'))
    admin.dispose()

    cfg = Config("alembic.ini")
    prev_url = os.environ["DATABASE_URL"]
    # alembic/env.py 以 DATABASE_URL 环境变量为准，必须临时改写
    os.environ["DATABASE_URL"] = mig_url.render_as_string(hide_password=False)
    try:
        command.upgrade(cfg, "head")
    finally:
        os.environ["DATABASE_URL"] = prev_url

    eng = create_engine(mig_url)
    insp = inspect(eng)
    missing = []
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            missing.append(f"表 {table.name} 不存在")
            continue
        db_cols = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name not in db_cols:
                missing.append(f"{table.name}.{col.name} 缺失")
    eng.dispose()

    assert not missing, "alembic head 与 models 不一致：" + "; ".join(missing[:10])
    # 预留唯一约束必须在
    eng = create_engine(mig_url)
    insp = inspect(eng)
    uqs = [set(u["column_names"]) for u in insp.get_unique_constraints("inventory_reservations")]
    assert {"order_id", "item_id"} in uqs, "uq_reservation_order_item 缺失"
    eng.dispose()
