# API 参考 (API Reference)

后端基于 FastAPI 重写后，提供了自动生成且符合 OpenAPI 标准的**交互式 API 文档 (Swagger UI)**。开发过程中推荐直接查阅 Swagger UI，以获取最精确、可即时调试的接口路径、请求体格式及返回 Schema。

## 交互式文档访问入口

在本地或局域网容器启动后，在浏览器直接打开以下链接：
* **Swagger UI (推荐)**: `http://localhost:8080/docs`  
  *提供完整的表单交互与接口一键“Try it out”测试。*
* **ReDoc (备用)**: `http://localhost:8080/redoc`  
  *提供排版规整、便于阅读的静态接口技术文档。*

> [!TIP]
> 如果是在局域网中的测试设备（例如手机），请将 `localhost` 替换为宿主机实际的局域网 IP（例如 `http://192.168.5.33:8080/docs`）。

---

## 统一认证规范

除了 **【登录接口】** `/auth/login` 之外，后端所有的 API 路由均受到安全守卫拦截。客户端在发送 HTTP 请求时，必须在 Header 中附加用户的 JWT Bearer Token：

* **请求头格式**:  
  `Authorization: Bearer <access_token>`
* **Token 有效期**:  
  默认为 7 天 (`ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7`)。
* **认证拦截**:  
  如果未带 Token、Token 篡改损坏或已过期，后端将直接拦截并返回 `401 Unauthorized` 状态码，前端 Axios 响应拦截器将捕获此状态并重定向回登录页。

---

## 路由模块（Router Groups）汇总

系统共有 11 个独立的路由组，各接口的基础请求路径如下：

### 1. 认证模块 (`/auth`)
* `POST /auth/login`：登录获取 JWT 令牌与用户信息。
* `GET /auth/me`：根据当前 Header 中的 Token，获取已登录用户的详细信息及对应的 `permissions` 页面权限矩阵。

### 2. 订单模块 (`/orders`)
* `GET /orders`：分页获取订单列表，支持关键字模糊匹配、状态过滤和排序。
* `POST /orders`：录入新生产订单，若关联工艺模板 ID 则自动实例化工序步骤。
* `GET /orders/{order_id}`：获取单笔订单的详情，包含其工艺流程步骤和当前进展状态。
* `POST /orders/{order_id}/steps/{step_id}/advance`：推进工序步骤完工（自动拦截工序拍照判定条件，所有步骤完成后自动触发物理库存扣减）。
* `POST /orders/{order_id}/steps/{step_id}/rollback`：回退工序至 pending 状态，并联动回退物理出库的零配件库存。
* `POST /orders/{order_id}/steps/{step_id}/skip`：跳过非必做工序步骤。
* `GET /orders/{order_id}/materials`：获取此订单预留的所有零配件明细及预留数量。
* `POST /orders/{order_id}/materials`：为订单预留绑定指定数量的零配件物料。
* `DELETE /orders/{order_id}/materials`：移除已绑定的用料并释放对应的预留锁定库存。

### 3. 工艺流程模块 (`/process-flows`)
* `GET /process-flows`：获取所有可用的工艺模板列表。
* `POST /process-flows`：新建工艺流程模板。
* `PUT /process-flows/{flow_id}/steps`：全量更新或保存工艺流程模板底下的全部工序步骤（采用“先删后插”的覆盖机制）。

### 4. 图纸文档模块 (`/documents`)
* `GET /documents`：获取系统图纸列表，支持按订单 ID 或图纸类别检索。
* `POST /documents/upload/{order_no}`：`multipart/form-data` 上传文件，自动根据同订单同分类将历史版本标为废弃，并将新文件写盘存储。
* `DELETE /documents/{id}`：从数据库删除图纸记录，并联动删除服务器磁盘上的物理文件。

### 5. 库存模块 (`/inventory`)
* `GET /inventory`：分页获取库房零配件物料名录，自动显示物理库存数、预留锁定数以及剩余可用数。
* `POST /inventory`：录入新物料。
* `PUT /inventory/{item_id}`：修改库存物料规格、总量或低水位预警阈值。

### 6. 客户模块 (`/customers`)
* `GET /customers`：获取客户列表（含 JSON 格式的联系方式列表）。
* `POST /customers`：录入新客户，强制要求至少录入一种联系方式（如微信或电话）。

### 7. 外协模块 (`/vendors`)
* `GET /vendors`：管理外委外协加工商信息。

### 8. 用户与权限控制 (`/users`) — 仅限管理员访问
* `GET /users`：系统用户账号列表。
* `PUT /users/{user_id}/permissions`：更新指定用户的页面可见与编辑权限矩阵。

### 9. 仪表台与统计 (`/dashboard`)
* `GET /dashboard/stats`：返回今日待处理订单、低水位库存报警数、我的待办等卡片汇总统计数值。

### 10. 系统设置 (`/settings`)
* `PUT /settings`：修改并保存主系统全局参数。

### 11. 通知消息 (`/notifications`)
* `GET /notifications`：分页获取个人消息列表。
* `POST /notifications/read-all`：将名下所有通知消息一键标记为已读。

---

## 统一响应状态码 (HTTP Status Codes)

| 状态码 | 中文释义 | 系统触发场景示例 |
|:---|:---|:---|
| **200 OK** | **请求成功** | 查询列表成功，或者修改成功。 |
| **201 Created** | **资源创建成功** | 新增客户、新建订单成功。 |
| **400 Bad Request** | **客户端请求参数错误** | 负责人姓名为空；工序是必做的却尝试跳过；“上传照片”工序在未拍图时尝试提交。 |
| **401 Unauthorized** | **未登录或凭证失效** | 请求 Header 未携带 Token 或 Token 签名不匹配。 |
| **403 Forbidden** | **权限不足** | 普通员工账号尝试更改其他人的页面权限，或者只读权限用户尝试发起 `DELETE` 请求。 |
| **404 Not Found** | **资源不存在** | 查询一笔已被物理删除的订单。 |
| **500 Internal Error**| **服务器内部错误** | 数据库连接超时，或者代码内部逻辑报错抛出异常。 |
