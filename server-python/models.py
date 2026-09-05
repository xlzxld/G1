from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    # 登出/封禁时递增：JWT 内记录签发时的版本号，不匹配即视为已吊销
    token_version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    page_permissions = relationship("PagePermission", back_populates="user", cascade="all, delete-orphan")


class PagePermission(Base):
    __tablename__ = "page_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    page_key = Column(String, nullable=False)
    can_view = Column(Integer, default=0)
    can_edit = Column(Integer, default=0)

    user = relationship("User", back_populates="page_permissions")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, default="")
    phone = Column(String, default="")
    address = Column(String, default="")
    wechat = Column(String, default="")
    email = Column(String, default="")
    notes = Column(String, default="")
    contact_methods = Column(JSON, default=list) # Replaces individual contact fields
    contacts = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, nullable=False)
    # 产品类型（受控枚举，与 BOM.product_type 匹配；存量订单留空不回填，仅新单匹配）
    product_type = Column(String, default="", index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), index=True, nullable=True)
    customer_name = Column(String, default="") # Kept for legacy/fallback
    priority = Column(Integer, index=True, default=0)
    status = Column(String, index=True, default="in_progress")
    current_step_id = Column(Integer, nullable=True)
    shipment_date = Column(DateTime, nullable=True)
    notes = Column(String, default="")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # 已退役（D16）：订单状态流转不再触碰库存，领料 OUTBOUND 是唯一减 total 路径。
    # 列仅为存量库兼容保留，新代码禁止读写。
    inventory_deducted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="orders")
    documents = relationship("Document", back_populates="order", cascade="all, delete-orphan")


class ProcessFlow(Base):
    __tablename__ = "process_flows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    is_template = Column(Integer, default=0)
    order_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    steps = relationship("ProcessStep", back_populates="flow", cascade="all, delete-orphan")


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("process_flows.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String, nullable=False)
    seq = Column(Integer, default=0)
    required = Column(Integer, default=1)
    outsourced = Column(Integer, default=0)
    vendor_id = Column(Integer, nullable=True)
    sent_date = Column(DateTime, nullable=True)
    return_date = Column(DateTime, nullable=True)
    cost = Column(Float, nullable=True)
    assignee = Column(String, default="")
    completion_condition = Column(String, default="manual")
    status = Column(String, index=True, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    flow = relationship("ProcessFlow", back_populates="steps")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    step_id = Column(Integer, ForeignKey("process_steps.id", ondelete="CASCADE"), index=True, nullable=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    category = Column(String, default="图纸")
    version = Column(Integer, default=1)
    status = Column(String, default="active")
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String, default="")
    title = Column(String, default="")
    description = Column(String, default="")
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    order = relationship("Order", back_populates="documents")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    spec = Column(String, default="")
    # category/location：物料主数据（V3 库存域）
    category = Column(String, default="")
    location = Column(String, default="")
    total = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    unit = Column(String, default="件")
    # min_stock：安全库存水位，接替旧 alert_threshold（口径统一为 available = total - reserved）
    min_stock = Column(Integer, default=5)
    # 归档替代删除：存在流水的物料禁止 DELETE，只能归档（保护审计链）
    is_archived = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    movements = relationship("StockMovement", back_populates="item")


class StockMovement(Base):
    """库存流水——库存量的单一事实来源。

    item.total = SUM(quantity)（缓存列，仅由 services/inventory_service.py 刷新）。
    领料=OUTBOUND(source_type=order)；退料=RETURN；入库=INBOUND；
    采购到货=INBOUND(source_type=purchase)；期初=OPENING；盘点差额=ADJUSTMENT。
    quantity 带符号：入库为正、出库为负。
    """
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    # 存在流水的物料禁止删除（应用层守卫），RESTRICT 作为 DB 级兜底
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), index=True, nullable=False)
    type = Column(String, index=True, nullable=False)
    source_type = Column(String, default="manual", index=True)
    source_id = Column(Integer, index=True, nullable=True)
    batch_no = Column(String, default="")
    unit_cost = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now(), index=True)

    item = relationship("InventoryItem", back_populates="movements")


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"
    # 同一订单对同一物料只允许一条预留记录（并发重复预留修复，8/6 报告数据完整性 #6）
    __table_args__ = (
        UniqueConstraint("order_id", "item_id", name="uq_reservation_order_item"),
    )

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class BOM(Base):
    """用料模板：与 ProcessFlow(is_template) 同构。建单时按 product_type 自动带出用料。"""
    __tablename__ = "boms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # 受控枚举：两端（Order.product_type / BOM.product_type）只允许从已有类型中选择，
    # 禁止自由文本（外部声音 #9：静默失配防护）
    product_type = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    note = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")


class BOMItem(Base):
    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("boms.id", ondelete="CASCADE"), index=True, nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    quantity_per_set = Column(Integer, default=1, nullable=False)
    note = Column(String, default="")

    bom = relationship("BOM", back_populates="items")
    item = relationship("InventoryItem")


class PurchaseOrder(Base):
    """采购单雏形：补货清单 → 采购 → 到货生成 INBOUND 流水。

    雏形阶段一张采购单仅含一个物料；received_quantity 支持分批到货，
    全部到齐后状态置 closed。
    """
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_no = Column(String, unique=True, index=True, nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, default=0)
    status = Column(String, index=True, default="draft")  # draft | ordered | received | closed
    expected_date = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    received_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    item = relationship("InventoryItem")
    vendor = relationship("Vendor")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    to_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, default="")
    source = Column(String, default="manual")
    link = Column(String, default="")
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event = Column(String, nullable=False)
    condition_field = Column(String, default="")
    condition_op = Column(String, default="lt")
    condition_value = Column(String, default="")
    notify_role = Column(String, default="")
    title_template = Column(String, nullable=False)
    body_template = Column(String, default="")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, default="")
    phone = Column(String, default="")
    address = Column(String, default="")
    notes = Column(String, default="")
    contact_methods = Column(JSON, default=list)
    contacts = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    category = Column(String, default="general")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    detail = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())
