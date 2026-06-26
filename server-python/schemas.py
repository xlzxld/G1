from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    display_name: str
    role_label: Optional[str] = ""
    is_admin: int = 0
    is_active: int = 1

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    contact: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    wechat: Optional[str] = ""
    email: Optional[str] = ""
    notes: Optional[str] = ""
    contact_methods: Optional[List[dict]] = []

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Document Schemas ---
class DocumentBase(BaseModel):
    filename: str
    original_name: str
    category: str = "图纸"
    version: int = 1
    status: str = "active"
    file_path: str
    file_size: int = 0
    mime_type: str = ""
    title: str = ""
    description: str = ""

class DocumentCreate(DocumentBase):
    order_id: int
    uploaded_by: Optional[int] = None

class DocumentResponse(DocumentBase):
    id: int
    order_id: int
    uploaded_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Order Schemas ---
class OrderBase(BaseModel):
    order_no: str
    product_name: str
    priority: int = 0
    status: str = "in_progress"
    shipment_date: Optional[datetime] = None
    notes: Optional[str] = ""

class OrderCreate(OrderBase):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = ""
    template_flow_id: Optional[int] = None

class OrderResponse(OrderBase):
    id: int
    customer_id: Optional[int]
    customer_name: str
    current_step_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True

# --- Process Step & Flow Schemas ---
class ProcessStepBase(BaseModel):
    name: str
    seq: int = 0
    required: int = 1
    can_parallel: int = 0
    depends_on_step_id: Optional[int] = None
    outsourced: int = 0
    vendor_id: Optional[int] = None
    cost: Optional[float] = None
    assignee: str = ""
    completion_condition: str = "manual"

class ProcessStepCreate(ProcessStepBase):
    flow_id: int

class ProcessStepResponse(ProcessStepBase):
    id: int
    flow_id: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    completed_by: Optional[int]

    class Config:
        from_attributes = True

class ProcessFlowBase(BaseModel):
    name: str
    description: str = ""
    is_template: int = 0

class ProcessFlowCreate(ProcessFlowBase):
    order_id: Optional[int] = None

class ProcessFlowResponse(ProcessFlowBase):
    id: int
    order_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    steps: List[ProcessStepResponse] = []

    class Config:
        from_attributes = True

# --- Inventory Schemas ---
class InventoryItemBase(BaseModel):
    name: str
    spec: str = ""
    total: int = 0
    reserved: int = 0
    unit: str = "件"
    alert_threshold: int = 5

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Vendor Schemas ---
class VendorBase(BaseModel):
    name: str
    contact: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""
    contact_methods: Optional[List[dict]] = []

class VendorCreate(VendorBase):
    pass

class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Notification Schemas ---
class NotificationBase(BaseModel):
    title: str
    body: Optional[str] = ""
    source: str = "manual"
    link: Optional[str] = ""

class NotificationCreate(NotificationBase):
    to_user_id: int

class NotificationResponse(NotificationBase):
    id: int
    from_user_id: Optional[int]
    to_user_id: int
    is_read: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- NotificationRule Schemas ---
class NotificationRuleBase(BaseModel):
    name: str
    event: str
    condition_field: Optional[str] = ""
    condition_op: str = "lt"
    condition_value: Optional[str] = ""
    notify_role: Optional[str] = ""
    title_template: str
    body_template: Optional[str] = ""
    is_active: int = 1

class NotificationRuleCreate(NotificationRuleBase):
    pass

class NotificationRuleResponse(NotificationRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- AuditLog Schemas ---
class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    detail: Optional[str] = ""

class AuditLogResponse(AuditLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    display_name: Optional[str] = ""

    class Config:
        from_attributes = True
