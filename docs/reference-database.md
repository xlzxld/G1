# 数据库表结构

数据库引擎使用 **PostgreSQL 15**（由 Docker 中的 `db` 容器托管），由 SQLAlchemy ORM 进行实体映射与表结构自动同步。所有日期和时间字段采用 PostgreSQL 原生的 `TIMESTAMP WITHOUT TIME ZONE`（对应后端 `DateTime` 类型），并支持由数据库引擎在插入时自动填充默认时间戳。

## 实体关系图 (Entity Relationship Diagram)

```
users (用户) ──1:N── page_permissions (页面权限)
users (用户) ──1:N── orders (订单创建人)
users (用户) ──1:N── notifications (通知发送人/接收人)
users (用户) ──1:N── documents (图纸上传人)
users (用户) ──1:N── process_steps (工序完成人)
users (用户) ──1:N── audit_logs (审计日志操作人)

customers (客户) ──1:N── orders (订单)

orders (订单) ──1:1── process_flows (工序流程实例)
orders (订单) ──1:N── documents (图纸文件)
orders (订单) ──1:N── inventory_reservations (零配件预留)

process_flows (工艺流程) ──1:N── process_steps (工序步骤)

inventory_items (库存零配件) ──1:N── inventory_reservations (预留明细)
```

---

## 表详细定义

### 1. users — 用户账号表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 用户唯一主键 ID |
| `username` | `String` | Unique, Index, Not Null | — | 登录账号名称 |
| `display_name` | `String` | Not Null | — | 员工姓名，界面展示用 |
| `role_label` | `String` | — | `""` | 角色/工种标签（如“车间工人”、“设计师”） |
| `password_hash` | `String` | Not Null | — | bcrypt 对密码哈希加密后的字符串 |
| `is_admin` | `Integer` | — | `0` | 是否超级管理员 (1=是, 0=否) |
| `is_active` | `Integer` | — | `1` | 账号状态 (1=启用, 0=禁用停用) |
| `created_at` | `DateTime` | — | `func.now()` | 账号创建时间 |
| `updated_at` | `DateTime` | — | `func.now()` | 账号最近更新时间 |

---

### 2. page_permissions — 页面与操作权限表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 主键 ID |
| `user_id` | `Integer` | FK $\to$ `users.id` (CASCADE) | — | 关联的用户 ID |
| `page_key` | `String` | Not Null | — | 页面路由唯一标识键 (如 `orders`, `drawings` 等) |
| `can_view` | `Integer` | — | `0` | 该页面是否可见 (1=可见, 0=不可见) |
| `can_edit` | `Integer` | — | `0` | 该页面是否可增删改编辑 (1=可编辑, 0=只读) |

> 唯一性联合索引约束：`Unique(user_id, page_key)` 确保每个用户对于同一个模块仅拥有一条权限规则。

---

### 3. customers — 客户档案表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 客户唯一主键 ID |
| `name` | `String` | Not Null | — | 客户名称（如“捷温科技”） |
| `address` | `String` | — | `""` | 客户公司地址 |
| `notes` | `String` | — | `""` | 客户备注信息 |
| `contact_methods` | `JSON` | — | `[]` | 动态联系方式列表：`[{"type": "电话", "value": "138..."}, ...]` |
| `created_at` | `DateTime` | — | `func.now()` | 档案创建时间 |
| `updated_at` | `DateTime` | — | `func.now()` | 最近修改时间 |

* 注：`contact`、`phone`、`wechat`、`email` 等废弃字段在表结构中暂时保留为空字符，业务逻辑已全部迁移至 JSON 格式的 `contact_methods` 数组。

---

### 4. orders — 生产订单表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 订单唯一主键 ID |
| `order_no` | `String` | Unique, Index, Not Null | — | 生产订单编号（如 `ORD-2026-0001`） |
| `product_name` | `String` | Not Null | — | 对应热流道产品的规格或名称 |
| `customer_id` | `Integer` | FK $\to$ `customers.id` (SET NULL) | — | 关联的客户 ID（允许为空） |
| `customer_name` | `String` | — | `""` | 客户名称静态备份（用于兼容性过渡） |
| `priority` | `Integer` | — | `0` | 订单优先级数值（数值越大越紧急） |
| `status` | `String` | — | `"in_progress"` | 订单运行状态，由工序引擎实时修改 |
| `current_step_id` | `Integer` | — | — | 当前正在进行或刚结束的工序步骤 ID |
| `shipment_date` | `DateTime` | — | — | 预期发货日期时间 |
| `notes` | `String` | — | `""` | 订单的特殊要求备注 |
| `created_by` | `Integer` | FK $\to$ `users.id` (SET NULL) | — | 订单创建人 ID |
| `inventory_deducted`| `Integer` | — | `0` | 库存物理出库扣减标记 (0=未扣减, 1=已物理出库) |
| `created_at` | `DateTime` | — | `func.now()` | 订单录入时间 |
| `updated_at` | `DateTime` | — | `func.now()` | 订单最近变更时间 |

---

### 5. process_flows — 工艺流程/模板表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 流程唯一主键 ID |
| `name` | `String` | Not Null | — | 流程/模板名称 |
| `description` | `String` | — | `""` | 流程描述 |
| `is_template` | `Integer` | — | `0` | 是否为模板 (1=工艺流模板, 0=被绑定给具体订单的流转实例) |
| `order_id` | `Integer` | — | — | 绑定的订单 ID（仅当 `is_template=0` 时生效） |
| `created_at` | `DateTime` | — | `func.now()` | 创建时间 |
| `updated_at` | `DateTime` | — | `func.now()` | 修改时间 |

---

### 6. process_steps — 工序步骤明细表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 步骤唯一主键 ID |
| `flow_id` | `Integer` | FK $\to$ `process_flows.id` (CASCADE)| — | 所属工艺流程的 ID |
| `name` | `String` | Not Null | — | 工序名称（如“热流道排板”、“发黑处理”） |
| `seq` | `Integer` | — | `0` | 工序排列顺序号，数值越小排越前 |
| `required` | `Integer` | — | `1` | 是否必做工序 (1=必做不能跳过, 0=选做可跳过) |
| `outsourced` | `Integer` | — | `0` | 是否外协外委工序 (1=外协, 0=车间内制) |
| `vendor_id` | `Integer` | — | — | 承接外协的厂商 ID (关联 `vendors.id`) |
| `sent_date` | `DateTime` | — | — | 发送外协的日期时间 |
| `return_date` | `DateTime` | — | — | 外协送回的日期时间 |
| `cost` | `Float` | — | — | 外协加工所花费的实际金额费用 |
| `assignee` | `String` | — | `""` | 工序负责人账号的用户名 (`username`) |
| `completion_condition`| `String` | — | `"manual"` | 完工判定逻辑条件 (`manual`=直接点确认, `photo`=必须拍照) |
| `status` | `String` | — | `"pending"` | 当前工序状态 (`pending`/`completed`/`skipped`) |
| `started_at` | `DateTime` | — | — | 工序开启时间 |
| `completed_at` | `DateTime` | — | — | 确认完工的时间（精确到秒） |
| `completed_by` | `Integer` | FK $\to$ `users.id` (SET NULL) | — | 完工点击人/确认人 ID |

* 注：已废弃 legacy 字段 `can_parallel`（并行步骤）与 `depends_on_step_id`（前置依赖）已被物理移除，系统改用纯线性 `seq` 序列引擎。

---

### 7. documents — 图纸文件与照片表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 图纸附件唯一主键 ID |
| `order_id` | `Integer` | FK $\to$ `orders.id` (CASCADE) | — | 所属订单 ID |
| `step_id` | `Integer` | FK $\to$ `process_steps.id` (CASCADE) | — | 上传关联的工序步骤 ID（如果为工序实操拍照） |
| `filename` | `String` | Not Null | — | 落盘在服务器的文件名（含时间戳前缀防止覆盖） |
| `original_name` | `String` | Not Null | — | 文件上传前的原始中文名称 |
| `category` | `String` | — | `"图纸"` | 分类（如“2D图”、“3D图”、“工艺文件”、“工序拍照”） |
| `version` | `Integer` | — | `1` | 该订单下同分类图纸的版本序列号 |
| `status` | `String` | — | `"active"` | 生命周期状态 (`active`=生效最新版, `deprecated`=历史废弃版本) |
| `file_path` | `String` | Not Null | — | 服务器保存的绝对路径路径 |
| `file_size` | `Integer` | — | `0` | 文件体积字节数 (bytes) |
| `mime_type` | `String` | — | `""` | 媒体文件类型 |
| `title` | `String` | — | `""` | 附件标题 |
| `description` | `String` | — | `""` | 附件详细描述 |
| `uploaded_by` | `Integer` | FK $\to$ `users.id` (SET NULL) | — | 上传操作人 ID |
| `created_at` | `DateTime` | — | `func.now()` | 文件上传时间 |

---

### 8. inventory_items — 库存物料明细表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 库存商品唯一主键 ID |
| `name` | `String` | Not Null | — | 零配件/物料名称（如“温控卡”） |
| `spec` | `String` | — | `""` | 规格尺寸或型号描述 |
| `total` | `Integer` | — | `0` | 物理库房的总实际在库数量 |
| `reserved` | `Integer` | — | `0` | 被各生产订单已锁定的预留锁定数量 |
| `unit` | `String` | — | `"件"` | 计量单位（个、件、米等） |
| `alert_threshold` | `Integer` | — | `5` | 库存低水位报警阈值 |
| `created_at` | `DateTime` | — | `func.now()` | 创建时间 |
| `updated_at` | `DateTime` | — | `func.now()` | 信息更新时间 |

---

### 9. inventory_reservations — 订单物料预留映射表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 主键 ID |
| `item_id` | `Integer` | FK $\to$ `inventory_items.id` (CASCADE) | — | 锁定的物料 ID |
| `order_id` | `Integer` | FK $\to$ `orders.id` (CASCADE) | — | 分配至哪笔生产订单 ID |
| `quantity` | `Integer` | — | `0` | 锁定预留的物理数量 |
| `created_at` | `DateTime` | — | `func.now()` | 预留事务生成时间 |

---

### 10. notifications — 站内消息通知表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 主键 ID |
| `from_user_id` | `Integer` | FK $\to$ `users.id` (SET NULL) | — | 触发或发送通知的用户 ID（为空表明系统自动派发） |
| `to_user_id` | `Integer` | FK $\to$ `users.id` (CASCADE)| — | 消息接收人 ID |
| `title` | `String` | Not Null | — | 通知的标题 |
| `body` | `String` | — | `""` | 通知的详细文字内容 |
| `source` | `String` | — | `"manual"` | 来源类别 (`manual`=用户手动发, `auto`=警报引擎触发) |
| `link` | `String` | — | `""` | 点击通知可跳转的前端具体页面路径 |
| `is_read` | `Integer` | — | `0` | 已读标记 (0=未读, 1=已读) |
| `created_at` | `DateTime` | — | `func.now()` | 消息派发时间 |

---

### 11. notification_rules — 自动警报配置表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 规则唯一主键 ID |
| `name` | `String` | Not Null | — | 警报规则名称 |
| `event` | `String` | Not Null | — | 判定事件触发源（如 `inventory_alert`） |
| `condition_field`| `String` | — | `""` | 比较字段名（如 `available` 字段） |
| `condition_op` | `String` | — | `"lt"` | 逻辑操作符 (`eq`/`lt`/`gt`/`contains` 等) |
| `condition_value`| `String` | — | `""` | 判定水位阈值界限 |
| `notify_role` | `String` | — | `""` | 接收消息的对应系统角色 |
| `title_template` | `String` | Not Null | — | 自动派发消息标题模板 |
| `body_template` | `String` | — | `""` | 自动派发消息正文模板（可支持花括号插值） |
| `is_active` | `Integer` | — | `1` | 规则是否开启生效中 (1=启用, 0=挂起禁用) |
| `created_at` | `DateTime` | — | `func.now()` | 规则创建时间 |

---

### 12. vendors — 外协加工商表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 加工商唯一主键 ID |
| `name` | `String` | Not Null | — | 外协单位名称（如“大昌精机厂”） |
| `contact` | `String` | — | `""` | 联系人姓名备份 |
| `phone` | `String` | — | `""` | 联系人电话备份 |
| `address` | `String` | — | `""` | 物理厂房寄送地址 |
| `notes` | `String` | — | `""` | 备注资质信息 |
| `contact_methods` | `JSON` | — | `[]` | 动态多联系方式数组，结构与客户相同 |
| `created_at` | `DateTime` | — | `func.now()` | 厂商录入时间 |
| `updated_at` | `DateTime` | — | `func.now()` | 资料修改时间 |

---

### 13. system_settings — 系统设置配置表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 主键 ID |
| `key` | `String` | Unique, Not Null| — | 系统配置属性键 (如 `system_theme` 等) |
| `value` | `String` | Not Null | — | 配置项的具体存储属性值 |
| `category` | `String` | — | `"general"` | 设置分类 |
| `updated_at` | `DateTime` | — | `func.now()` | 最近保存修改时间 |

---

### 14. audit_logs — 全局操作审计日志表

| 列名 | 数据类型 | 约束 | 默认值 | 详细说明 |
|:---|:---|:---|:---|:---|
| `id` | `Integer` | PK, Index | 自增 | 审计记录唯一主键 ID |
| `user_id` | `Integer` | FK $\to$ `users.id` (SET NULL) | — | 进行该敏感写入操作的系统账号 ID |
| `action` | `String` | Not Null | — | 动作类别 (`create`/`update`/`delete`) |
| `entity_type` | `String` | Not Null | — | 操作更改的数据类型（如 `orders`, `inventory`） |
| `entity_id` | `Integer` | — | — | 被更改数据的实体 ID |
| `detail` | `String` | — | `""` | 汉化后的友好操作细节陈述（如：*确认完成了订单「ORD-XX」的「设计」工序*） |
| `created_at` | `DateTime` | — | `func.now()` | 操作发生时服务器记录的精确时刻（精确到秒） |
