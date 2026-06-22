 # API 参考

 所有接口均以 `/api` 为前缀。除 `/api/auth/login` 和 `/api/auth/refresh` 外，均需 `Authorization: Bearer <access_token>` 请求头。

 ## 认证 (`/api/auth`)

 ### POST /api/auth/login
 登录获取令牌。  
 **Body:** `{ username: string, password: string }`  
 **返回:** `{ access_token, refresh_token, user: { id, username, display_name, is_admin } }`  
 **错误:** 400 缺少字段 | 401 凭据无效或用户已停用

 ### POST /api/auth/refresh
 用 refresh token 换取新的 access token。  
 **Body:** `{ refresh_token: string }`  
 **返回:** `{ access_token }`  
 **错误:** 400 缺少字段 | 401 token 无效或已被撤销

 ### POST /api/auth/logout
 登出，将 refresh token 加入黑名单。  
 **需认证:** 是  
 **Body:** `{ refresh_token: string }` (可选)  
 **返回:** `{ message: "Logged out" }`

 ### GET /api/auth/me
 获取当前用户信息和权限。  
 **返回:** `{ id, username, display_name, role_label, is_admin, permissions: [{ page_key, can_view, can_edit }] }`

 ## 仪表台 (`/api/dashboard`)

 ### GET /api/dashboard/stats
 返回汇总统计数据。  
 **返回:** `{ today_pending, in_progress, customer_confirm, inventory_alert, today_done, recent_customers: [], my_todos }`

 ## 用户管理 (`/api/users`) — 需管理员权限

 ### GET /api/users
 **权限:** `users` 页面 view | **需:** admin  
 **返回:** 用户列表（不含密码哈希）

 ### POST /api/users
 **权限:** `users` 页面 edit | **需:** admin  
 **Body:** `{ username, display_name?, role_label?, password, is_admin?, is_active? }`  
 **返回:** `{ id, username }` (201)  
 **错误:** 400 缺少字段 | 409 用户名已存在

 ### PUT /api/users/:id
 **权限:** `users` 页面 edit | **需:** admin  
 **Body:** `{ username?, display_name?, role_label?, is_admin?, is_active?, password? }`  
 **返回:** `{ id, updated: true }`

 ### DELETE /api/users/:id
 **权限:** `users` 页面 edit | **需:** admin  
 **错误:** 400 不能删除最后一个管理员  
 **返回:** `{ deleted: true }`

 ### GET /api/users/:id/permissions
 **需:** admin  
 **返回:** `[{ page_key, can_view, can_edit }]`

 ### PUT /api/users/:id/permissions
 **权限:** `users` 页面 edit | **需:** admin  
 **Body:** `{ permissions: [{ page_key, can_view: 0|1, can_edit: 0|1 }] }`  
 **返回:** `{ updated: true }`

 ## 客户管理 (`/api/customers`)

 ### GET /api/customers
 **权限:** `customers` view  
 **Query:** `keyword` (可选，模糊匹配 name 和 contact_methods)  
 **返回:** 客户列表

 ### POST /api/customers
 **权限:** `customers` edit  
 **Body:** `{ name, address?, notes?, contact_methods: [{ type, value }] }`  
 **校验:** `contact_methods` 必须是非空数组，至少包含一个联系方式  
 **返回:** `{ id, name }` (201)

 ### GET /api/customers/:id
 **权限:** `customers` view  
 **返回:** 客户详情（含 contact_methods JSON）

 ### PUT /api/customers/:id
 **权限:** `customers` edit  
 **Body:** `{ name?, address?, notes?, contact_methods? }`  
 **返回:** `{ updated: true }`

 ### DELETE /api/customers/:id
 **权限:** `customers` edit  
 **行为:** 删除前将关联订单的 customer_id 置为 null  
 **返回:** `{ deleted: true }`

 ### GET /api/customers/:id/orders
 **权限:** `customers` view  
 **返回:** 该客户的订单列表

 ### GET /api/customers/:id/stats
 **权限:** `customers` view  
 **返回:** `{ total, completed, in_progress, paused, aborted }`

 ## 订单管理 (`/api/orders`)

 ### GET /api/orders
 **权限:** `orders` view  
 **Query:** `keyword`, `status`, `customer_name`, `priority`, `sort_by`, `sort_order`, `page`, `limit` (默认 20, 最大 100)  
 **返回:** `{ data: [], total, page, limit }`  
 **说明:** 结果中含 `current_step_name`（通过 LEFT JOIN process_steps）

 ### POST /api/orders
 **权限:** `orders` edit  
 **Body:** `{ order_no, product_name, template_flow_id?, customer_name?, priority?, shipment_date?, notes? }`  
 **校验:** order_no 和 product_name 必填；order_no 不可重复  
 **行为:** 若提供 template_flow_id，自动调用 copyFlowToOrder 复制工艺模板  
 **返回:** `{ id, order_no }` (201)

 ### GET /api/orders/:id
 **返回:** 订单详情 + `flow_id` + `steps`（含所有工序步骤）

 ### PUT /api/orders/:id
 **权限:** `orders` edit  
 **Body:** `{ product_name?, customer_name?, priority?, shipment_date?, notes? }`  
 **返回:** `{ updated: true }`

 ### DELETE /api/orders/:id
 **权限:** `orders` edit  
 **行为:** 级联删除关联的 process_flows 和 process_steps  
 **返回:** `{ deleted: true }`

 ### PUT /api/orders/:id/status
 **需:** admin  
 **Body:** `{ status: string }`  
 **返回:** `{ updated: true }`

 ### POST /api/orders/:id/steps/:stepId/advance
 **权限:** `orders` edit  
 **行为:** 推进当前步骤完成，自动更新订单状态和 current_step_id  
 **返回:** `{ step, nextSteps, orderStatus }`

 ### POST /api/orders/:id/steps/:stepId/rollback
 **权限:** `orders` edit  
 **行为:** 回退到上一步（自动处理并行组）  
 **返回:** `{ rolledBack, orderStatus }`

 ### POST /api/orders/:id/steps/:stepId/skip
 **权限:** `orders` edit  
 **行为:** 跳过非必做步骤  
 **返回:** `{ skipped, nextSteps, orderStatus }`  
 **错误:** 400 不允许跳过必做步骤 (required=1)

 ## 工艺流程 (`/api/process-flows`)

 ### GET /api/process-flows
 **权限:** `process_flow` view  
 **返回:** 所有工艺模板 (is_template=1)，按 updated_at 倒序

 ### POST /api/process-flows
 **权限:** `process_flow` edit  
 **Body:** `{ name, description? }`  
 **返回:** `{ id, name }` (201)

 ### GET /api/process-flows/:id
 **返回:** 模板详情 + `steps`（含所有步骤定义）

 ### PUT /api/process-flows/:id
 **权限:** `process_flow` edit  
 **Body:** `{ name?, description? }`  
 **返回:** `{ updated: true }`

 ### DELETE /api/process-flows/:id
 **权限:** `process_flow` edit  
 **行为:** 级联删除关联的 process_steps  
 **返回:** `{ deleted: true }`

 ### PUT /api/process-flows/:id/steps
 **权限:** `process_flow` edit  
 **Body:** `{ steps: [{ name, seq, required, can_parallel, depends_on_step_id?, assignee?, completion_condition?, outsourced? }] }`  
 **行为:** 在事务中先删后插，替换全部步骤  
 **返回:** `{ updated: true }`

 ### POST /api/process-flows/:id/steps
 **权限:** `process_flow` edit  
 **Body:** `{ name, seq?, required?, can_parallel?, assignee?, completion_condition? }`  
 **返回:** `{ id, name }` (201)

 ## 图纸管理 (`/api/documents`)

 ### GET /api/documents
 **权限:** `drawings` view  
 **Query:** `order_id`, `category` (可选过滤)  
 **返回:** 文档列表（LEFT JOIN orders 以获取 order_no）

 ### POST /api/documents/upload/:order_no
 **权限:** `drawings` edit  
 **Content-Type:** multipart/form-data  
 **字段:** `file` (图片文件), `category` (可选，默认"图纸"), `title`, `description`  
 **限制:** 仅允许图片格式 (png/jpg/gif/webp/bmp/svg)，最大 50MB  
 **行为:** 上传新版本时自动将同分类旧版本标为 deprecated  
 **返回:** `{ id, version, filename, category }` (201)

 ### PUT /api/documents/:id
 **权限:** `drawings` edit  
 **Body:** `{ title?, description?, status? }`  
 **返回:** `{ updated: true }`

 ### PUT /api/documents/:id/status
 **权限:** `drawings` edit  
 **Body:** `{ status: "active" | "pending" | "deprecated" }`  
 **行为:** 设为 active 时，同分类其他文件自动标为 deprecated  
 **返回:** `{ updated: true }`

 ### DELETE /api/documents/:id
 **权限:** `drawings` edit  
 **行为:** 删除数据库记录和磁盘文件  
 **返回:** `{ deleted: true }`

 ## 库存管理 (`/api/inventory`)

 ### GET /api/inventory
 **权限:** `inventory` view  
 **返回:** 物料列表（含 total、reserved 和 alert_threshold）

 ### POST /api/inventory
 **权限:** `inventory` edit  
 **Body:** `{ name, spec?, total?, unit?, alert_threshold? }`  
 **返回:** `{ id, name }` (201)

 ### PUT /api/inventory/:id
 **权限:** `inventory` edit  
 **Body:** `{ name?, spec?, total?, unit?, alert_threshold? }`  
 **返回:** `{ updated: true }`

 ### DELETE /api/inventory/:id
 **权限:** `inventory` edit  
 **行为:** 级联删除关联的预留记录  
 **返回:** `{ deleted: true }`

 ### GET /api/inventory/:id/reservations
 **返回:** 该物料的预留列表（LEFT JOIN orders 以获取 order_no）

 ### POST /api/inventory/reserve
 **权限:** `inventory` edit  
 **Body:** `{ item_id, order_id, quantity }`  
 **校验:** 预留量不能超过可用库存 (total - reserved)  
 **行为:** 事务中 increment reserved + 插入预留记录  
 **返回:** `{ reserved: true }` (201)

 ### DELETE /api/inventory/reserve/:id
 **权限:** `inventory` edit  
 **行为:** 事务中 decrement reserved + 删除预留记录  
 **返回:** `{ deleted: true }`

 ## 通知中心 (`/api/notifications`)

 ### GET /api/notifications
 **返回:** 当前用户的通知列表（最近 50 条）

 ### GET /api/notifications/unread-count
 **返回:** `{ count }` — 当前用户未读通知数

 ### POST /api/notifications
 **Body:** `{ to_user_id, title, body?, link? }`  
 **行为:** 来源自动标记为 `manual`  
 **返回:** `{ id }` (201)

 ### PUT /api/notifications/:id/read
 **校验:** 仅限通知接收者本人  
 **返回:** `{ updated: true }`

 ### PUT /api/notifications/read-all
 **行为:** 标记当前用户所有未读通知为已读  
 **返回:** `{ updated: true }`

 ### GET /api/notifications/rules (admin)
 ### POST /api/notifications/rules (admin)
 ### PUT /api/notifications/rules/:id (admin)
 ### DELETE /api/notifications/rules/:id (admin)

 ## 外协管理 (`/api/vendors`)

 ### GET /api/vendors
 **权限:** `outsourcing` view  
 **返回:** 外协厂商列表（按名称排序）

 ### POST /api/vendors
 **权限:** `outsourcing` edit  
 **Body:** `{ name, contact?, phone?, address?, notes? }`  
 **返回:** `{ id, name }` (201)

 ### PUT /api/vendors/:id
 **权限:** `outsourcing` edit  
 **Body:** `{ name?, contact?, phone?, address?, notes? }`  
 **返回:** `{ updated: true }`

 ### DELETE /api/vendors/:id
 **权限:** `outsourcing` edit  
 **返回:** `{ deleted: true }`

 ## 系统设置 (`/api/settings`)

 ### GET /api/settings
 **返回:** 所有系统参数（按 category 排序）

 ### PUT /api/settings
 **需:** admin  
 **Body:** `{ key: string, value: string }`  
 **行为:** 使用 INSERT ... ON CONFLICT upsert  
 **返回:** `{ updated: true }`

 ### PUT /api/settings/change-password
 **Body:** `{ current_password, new_password }`  
 **校验:** new_password 至少 6 位  
 **返回:** `{ updated: true }`

 ### GET /api/settings/audit-logs
 **需:** admin  
 **返回:** 最近 100 条操作日志（LEFT JOIN users 显示操作人）

 ## 文件下载

 ### GET /api/download/:order_no/:category/:filename
 下载上传的图纸文件。  
 **说明:** 所有路径片段支持 URL 编码（中文文件名）。

 ## 健康检查

 ### GET /api/health
 **返回:** `{ status: "ok" }`

 ## 错误格式

 所有错误返回格式统一为 `{ error: string }`，HTTP 状态码遵循语义：
- 400 — 请求参数错误
- 401 — 未认证或 token 过期
- 403 — 无权限（页面不可访问 或 不允许编辑）
- 404 — 资源不存在
- 409 — 冲突（如订单号重复）

## 相关文档

- [数据库表结构](reference-database.md) — API 操作的底层数据模型
- [系统架构](explanation-architecture.md) — 中间件链和认证流程
- [权限模型](explanation-permission-model.md) — `requirePermission` 中间件详解
- [配置文件](reference-configuration.md) — 环境变量和上传限制
