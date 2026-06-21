 # 权限模型

 ## 设计目标

 热流道车间通常有管理员（老板/主管）和普通工人两类角色。管理员需要看到所有数据，普通工人根据职责只看到相关页面（比如钳工只看订单和库存，不看图纸）。系统用一套简单但完整的权限矩阵实现这个需求。

 ## 三层权限结构

 ### 第 1 层: 管理员豁免

 `is_admin=1` 的用户**完全绕过**所有权限检查，无论是前端路由守卫还是后端中间件。代码中体现为:

- 前端路由守卫: `if (auth.isAdmin) return next()` — 直接放行
- 后端 `requirePermission`: `if (req.user.is_admin) return next()` — 第一个判断就是管理员豁免

 这意味着管理员不需要在 `page_permissions` 表中存在任何记录就能访问所有页面。

 ### 第 2 层: 页面权限矩阵

 每个非管理员用户对每个页面有一条 `page_permissions` 记录:

 | 字段 | 含义 | 效果 |
 |------|------|------|
 | can_view=0 | 不可见 | 菜单不显示，路由守卫拒绝访问并跳转到第一个可访问页面 |
 | can_view=1, can_edit=0 | 只读 | 可查看列表和详情，但创建/编辑/删除按钮禁用 |
 | can_view=1, can_edit=1 | 可编辑 | 完整的 CRUD 权限 |

 页面键 (page_key) 与路由和后端路由的对应关系:

 | page_key | 前端路由 | 后端路由前缀 | 菜单项 |
 |----------|---------|-------------|--------|
 | dashboard | / | /api/dashboard | 仪表台 |
 | customers | /customers | /api/customers | 客户管理 |
 | orders | /orders | /api/orders | 订单管理 |
 | process_flow | /process-flow | /api/process-flows | 工艺流程 |
 | drawings | /drawings | /api/documents | 图纸管理 |
 | inventory | /inventory | /api/inventory | 库存管理 |
 | users | /users | /api/users | 用户管理 |
 | notifications | /notifications | /api/notifications | 通知中心 |
 | settings | /settings | /api/settings | 系统设置 |
 | outsourcing | /outsourcing | /api/vendors | 外协管理 |

 ### 第 3 层: 双重保护

 权限检查同时存在于前端和后端，互为补充:

- **前端路由守卫 (`router/index.js` beforeEach):** 拦截页面访问，无权限时自动跳转。用户体验好——看不到无权访问的页面。
- **后端中间件 (`permissions.js` requirePermission):** 在每个请求发出前验证。安全性高——即使前端被绕过，API 仍然受保护。

 ## 管理员防锁死机制

 管理员在用户管理页面给自己配置权限时，"用户管理"对应的开关会被前端锁定为开启状态，防止管理员误将自己踢出用户管理页面。

 后端还有额外保护: 不允许删除最后一个管理员账户 (`Cannot delete the last admin`)。

 ## 路由守卫的无权限跳转逻辑

 ```
 用户访问 /settings
   → isAdmin? → 是 → 放行
   → 否 → 查找 settings 的 can_view
   → can_view=0 → 查找第一个 can_view=1 的页面
     → 找到 → 跳转到该页面
     → 找不到 → 跳转到 /login
 ```

 关键细节: 跳转到第一个可访问页面而非 `/`，避免了无权限→白屏或死循环。

 ## 后端中间件的编辑保护

 `requirePermission(pageKey, 'edit')` 会在 `can_edit=0` 时返回 403。  
 路由文件对 GET 请求使用 `requirePermission('orders', 'view')`，对 POST/PUT/DELETE 使用 `requirePermission('orders', 'edit')`。

 ## 通知和仪表台的权限

- **仪表台:** 路由级只要求认证 (authMiddleware)，不要求页面权限。所有登录用户都能看到仪表台。
- **通知中心:** 不检查页面权限（通知是跨模块的）。用户只能看到发给自己的通知，但发送通知不限制接收人。
- **通知规则:** 需要 admin 权限才能管理。

## 相关文档

- [API 参考](reference-api.md) — 各接口的权限要求（需 admin / requirePermission）
- [管理用户和权限](howto-manage-users.md) — 操作指南
- [数据库表结构](reference-database.md) — users 和 page_permissions 表定义
