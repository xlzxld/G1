 # 数据库表结构

 数据库引擎: SQLite (better-sqlite3)，迁移管理: Knex。  
 所有时间字段使用 ISO 8601 文本格式 (`text`)，由 JavaScript 生成，非数据库原生时间戳。

 ## 实体关系图

 ```
 users ──1:N── page_permissions
 users ──1:N── orders (created_by)
 users ──1:N── notifications (from/to)
 users ──1:N── documents (uploaded_by)
 users ──1:N── process_steps (completed_by)
 users ──1:N── audit_logs
 customers ──1:N── orders
 orders ──1:N── process_flows (is_template=0)
 orders ──1:N── documents
 orders ──1:N── inventory_reservations
 process_flows ──1:N── process_steps
 inventory_items ──1:N── inventory_reservations
 ```

 ## 表详细定义

 ### users — 用户

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | username | TEXT | NOT NULL, UNIQUE | 登录名 |
 | display_name | TEXT | NOT NULL | 显示名称 |
 | role_label | TEXT | NOT NULL, DEFAULT '' | 角色标签（如"车间工人"） |
 | password_hash | TEXT | NOT NULL | bcrypt 哈希，10 rounds |
 | is_admin | INTEGER | NOT NULL, DEFAULT 0 | 管理员标志 (0/1) |
 | is_active | INTEGER | NOT NULL, DEFAULT 1 | 激活状态 (0/1) |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 ### page_permissions — 页面权限矩阵

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | user_id | INTEGER | FK→users(id) ON DELETE CASCADE | 用户 |
 | page_key | TEXT | NOT NULL | 页面标识符 (dashboard, orders, ...) |
 | can_view | INTEGER | NOT NULL, DEFAULT 0 | 可见 (0/1) |
 | can_edit | INTEGER | NOT NULL, DEFAULT 0 | 可编辑 (0/1) |

 唯一约束: `(user_id, page_key)` — 每个用户对每个页面只有一条权限记录。

 ### customers — 客户

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | name | TEXT | NOT NULL | 客户名称 |
 | contact | TEXT | DEFAULT '' | 旧版字段（已废弃，见下方 contact_methods） |
 | phone | TEXT | DEFAULT '' | 旧版字段 |
 | address | TEXT | DEFAULT '' | 地址 |
 | wechat | TEXT | DEFAULT '' | 旧版字段 |
 | email | TEXT | DEFAULT '' | 旧版字段 |
 | notes | TEXT | DEFAULT '' | 备注 |
 | contact_methods | TEXT | DEFAULT '[]' | JSON 数组: `[{"type":"电话","value":"138..."}]` |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 `contact_methods` 替代了旧的 contact/phone/wechat/email 固定字段。支持的 type 包括: 联系人、电话、微信、QQ、邮箱、传真（可扩展）。

 ### orders — 订单

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | order_no | TEXT | NOT NULL, UNIQUE | 订单编号 |
 | product_name | TEXT | NOT NULL | 产品名称 |
 | customer_name | TEXT | DEFAULT '' | 客户名称（旧字段，现在通过 customer_id 关联） |
 | priority | INTEGER | NOT NULL, DEFAULT 0 | 优先级 |
 | status | TEXT | NOT NULL, DEFAULT 'draft' | 状态，由工序引擎驱动 |
 | current_step_id | INTEGER | NULLABLE | 当前正在进行的步骤 ID |
 | shipment_date | TEXT | NULLABLE | 发货日期 |
 | notes | TEXT | DEFAULT '' | 备注 |
 | customer_id | INTEGER | FK→customers(id) ON DELETE SET NULL | 关联客户 |
 | created_by | INTEGER | FK→users(id) ON DELETE SET NULL | 创建人 |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 状态值: `draft` → `{步骤名}进行中` → ... → `completed` / `paused` / `aborted`

 ### process_flows — 工艺流程

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | name | TEXT | NOT NULL | 流程名称 |
 | description | TEXT | DEFAULT '' | 描述 |
 | is_template | INTEGER | NOT NULL, DEFAULT 0 | 1=工艺模板, 0=订单实例 |
 | order_id | INTEGER | NULLABLE | 关联的订单 ID（实例专用） |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 模板 (is_template=1) 在创建订单时通过 `copyFlowToOrder` 复制为实例 (is_template=0)。

 ### process_steps — 工序步骤

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | flow_id | INTEGER | FK→process_flows(id) ON DELETE CASCADE | 所属流程 |
 | name | TEXT | NOT NULL | 步骤名称 |
 | seq | INTEGER | NOT NULL, DEFAULT 0 | 顺序号 |
 | required | INTEGER | NOT NULL, DEFAULT 1 | 是否必做 (0/1) |
 | can_parallel | INTEGER | NOT NULL, DEFAULT 0 | 是否可并行 (0/1) |
 | depends_on_step_id | INTEGER | NULLABLE | 依赖的前置步骤 ID |
 | outsourced | INTEGER | NOT NULL, DEFAULT 0 | 是否外协 (0/1) |
 | vendor_id | INTEGER | NULLABLE | 外协厂商 ID |
 | sent_date | TEXT | NULLABLE | 外协发送日期 |
 | return_date | TEXT | NULLABLE | 外协返回日期 |
 | cost | REAL | NULLABLE | 外协费用 |
 | assignee | TEXT | DEFAULT '' | 指定执行人 (username) |
 | completion_condition | TEXT | NOT NULL, DEFAULT 'manual' | 完成条件 (当前仅 'manual') |
 | status | TEXT | NOT NULL, DEFAULT 'pending' | pending/in_progress/completed/skipped |
 | started_at | TEXT | NULLABLE | 开始时间 |
 | completed_at | TEXT | NULLABLE | 完成时间 |
 | completed_by | INTEGER | FK→users(id) ON DELETE SET NULL | 完成人 |

 ### documents — 图纸文件

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | order_id | INTEGER | FK→orders(id) ON DELETE CASCADE | 所属订单 |
 | filename | TEXT | NOT NULL | 存储文件名 (如 `v1737000000-drawing.png`) |
 | original_name | TEXT | NOT NULL | 原始文件名 |
 | category | TEXT | NOT NULL, DEFAULT '图纸' | 分类 |
 | version | INTEGER | NOT NULL, DEFAULT 1 | 版本号（自增） |
 | status | TEXT | NOT NULL, DEFAULT 'active' | active/pending/deprecated |
 | file_path | TEXT | NOT NULL | 磁盘完整路径 |
 | file_size | INTEGER | DEFAULT 0 | 文件大小 (bytes) |
 | mime_type | TEXT | DEFAULT '' | MIME 类型 |
 | title | TEXT | DEFAULT '' | 可编辑标题 |
 | description | TEXT | DEFAULT '' | 可编辑描述 |
 | uploaded_by | INTEGER | FK→users(id) ON DELETE SET NULL | 上传人 |
 | created_at | TEXT | NOT NULL, DEFAULT now | 上传时间 |

 版本管理：上传同分类文件时旧版本自动标为 deprecated。

 ### inventory_items — 库存物料

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | name | TEXT | NOT NULL | 物料名称 |
 | spec | TEXT | DEFAULT '' | 规格型号 |
 | total | INTEGER | NOT NULL, DEFAULT 0 | 总库存量 |
 | reserved | INTEGER | NOT NULL, DEFAULT 0 | 已预留量 |
 | unit | TEXT | DEFAULT '件' | 单位 |
 | alert_threshold | INTEGER | DEFAULT 5 | 预警阈值 |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 可用库存 = total - reserved。预留通过 inventory_reservations 表管理。

 ### inventory_reservations — 库存预留

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | item_id | INTEGER | FK→inventory_items(id) ON DELETE CASCADE | 物料 |
 | order_id | INTEGER | FK→orders(id) ON DELETE CASCADE | 订单 |
 | quantity | INTEGER | NOT NULL, DEFAULT 0 | 预留数量 |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |

 ### notifications — 通知

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | from_user_id | INTEGER | FK→users(id) ON DELETE SET NULL | 发送人 |
 | to_user_id | INTEGER | FK→users(id) ON DELETE CASCADE | 接收人 |
 | title | TEXT | NOT NULL | 标题 |
 | body | TEXT | DEFAULT '' | 正文 |
 | source | TEXT | NOT NULL, DEFAULT 'manual' | 来源 (manual/auto) |
 | link | TEXT | DEFAULT '' | 跳转链接 |
 | is_read | INTEGER | NOT NULL, DEFAULT 0 | 已读 (0/1) |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |

 ### notification_rules — 自动通知规则

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | name | TEXT | NOT NULL | 规则名称 |
 | event | TEXT | NOT NULL | 触发事件 |
 | condition_field | TEXT | DEFAULT '' | 条件字段 |
 | condition_op | TEXT | DEFAULT 'lt' | 条件运算符 (lt/gt/eq) |
 | condition_value | TEXT | DEFAULT '' | 条件值 |
 | notify_role | TEXT | DEFAULT '' | 通知角色 |
 | title_template | TEXT | NOT NULL | 标题模板 |
 | body_template | TEXT | DEFAULT '' | 正文模板 |
 | is_active | INTEGER | NOT NULL, DEFAULT 1 | 启用 (0/1) |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |

 **注意:** 自动规则引擎的定时检查尚未实现，目前规则只能通过 API 管理。

 ### vendors — 外协厂商

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | name | TEXT | NOT NULL | 厂商名称 |
 | contact | TEXT | DEFAULT '' | 联系人 |
 | phone | TEXT | DEFAULT '' | 电话 |
 | address | TEXT | DEFAULT '' | 地址 |
 | notes | TEXT | DEFAULT '' | 备注 |
 | created_at | TEXT | NOT NULL, DEFAULT now | 创建时间 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 ### system_settings — 系统参数

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | key | TEXT | NOT NULL, UNIQUE | 参数键 |
 | value | TEXT | NOT NULL | 参数值 |
 | category | TEXT | DEFAULT 'general' | 分类 |
 | updated_at | TEXT | NOT NULL, DEFAULT now | 更新时间 |

 ### audit_logs — 操作日志

 | 列名 | 类型 | 约束 | 说明 |
 |------|------|------|------|
 | id | INTEGER | PK, AUTOINCREMENT | 主键 |
 | user_id | INTEGER | FK→users(id) ON DELETE SET NULL | 操作人 |
 | action | TEXT | NOT NULL | 操作类型 |
 | entity_type | TEXT | NOT NULL | 实体类型 |
 | entity_id | INTEGER | NULLABLE | 实体 ID |
 | detail | TEXT | DEFAULT '' | 详情 (HTTP method + URL) |
 | created_at | TEXT | NOT NULL, DEFAULT now | 操作时间 |

 **注意:** audit_logs 中间件 (`audit.js`) 已编写但尚未集成到路由中。

## 相关文档

- [API 参考](reference-api.md) — 对应每个表的 CRUD 接口
- [系统架构](explanation-architecture.md) — 数据层在整体架构中的位置
- [配置文件](reference-configuration.md) — Knex 和数据库路径配置
