from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
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
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String, default="") # Kept for legacy/fallback
    priority = Column(Integer, default=0)
    status = Column(String, default="in_progress")
    current_step_id = Column(Integer, nullable=True)
    shipment_date = Column(DateTime, nullable=True)
    notes = Column(String, default="")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    inventory_deducted = Column(Integer, default=0) # 0=未扣减，1=已扣减
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="orders")
    documents = relationship("Document", back_populates="order", cascade="all, delete-orphan")


class ProcessFlow(Base):
    __tablename__ = "process_flows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    is_template = Column(Integer, default=0)
    order_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    steps = relationship("ProcessStep", back_populates="flow", cascade="all, delete-orphan")


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("process_flows.id", ondelete="CASCADE"), nullable=False)
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
    status = Column(String, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    flow = relationship("ProcessFlow", back_populates="steps")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(Integer, ForeignKey("process_steps.id", ondelete="CASCADE"), nullable=True)
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
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="documents")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    spec = Column(String, default="")
    total = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    unit = Column(String, default="件")
    alert_threshold = Column(Integer, default=5)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


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
