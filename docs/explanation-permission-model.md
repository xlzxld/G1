# 权限模型

## 设计目标

热流道车间通常由管理员（如厂长/系统管理员）、工程设计师、车间操作工和库房管理员等多个角色共同使用。为确保系统数据安全与权责分明，系统采用了一套完整的双轨（前端 + 后端）三层权限防御矩阵，实现了基于页面路由与操作等级的访问控制（Role-Based Access Control - RBAC）。

## 三层权限架构

### 第 1 层: 系统管理员豁免 (Admin Bypass)

如果用户表中的字段 `is_admin` 为 `1`（即超级管理员），系统直接判定其**完全豁免并绕过**所有的页面权限矩阵检查。此判定在前端与后端的第一优先级处生效：
* **后端**：在权限判定依赖项中，只要检测到 `current_user.is_admin` 为真，则直接通过，不再查询 `page_permissions` 权限矩阵表。
* **前端**：在路由守卫中，如果 `authStore.isAdmin` 为 `true`，路由守卫会直接放行。

这保证了管理员账户即便在数据库权限表中没有任何记录，也拥有全站的绝对控制权。

---

### 第 2 层: 页面级与操作级权限矩阵 (Matrix-Based Page Gating)

非管理员用户的权限数据记录在 `page_permissions` 表中，每个用户对每个系统页面对应有一条权限数据（具有唯一联合索引约束 `(user_id, page_key)`）。

权限细分为三个级别：

| 权限表现 | can_view 值 | can_edit 值 | 前后端综合表现效果 |
|:---|:---:|:---:|:---|
| **完全无权 (不可见)** | `0` | `0` | 前端菜单隐藏，直接通过 URL 访问跳转失败；后端 API 报错 `403` 禁止访问。 |
| **只读权限 (Read-Only)** | `1` | `0` | 前端菜单可见，能读取数据列表和详情；但所有新增、编辑、删除、导入、导出按钮全部置灰禁用；后端 POST/PUT/DELETE 接口报错 `403`。 |
| **读写权限 (CRUD)** | `1` | `1` | 允许完整的读写及业务流转操作。 |

系统各模块的 `page_key` 与前后端路径对应关系如下：

| page_key (权限键) | 前端路由路径 | 后端挂载路由前缀 | 前端菜单名称 |
|:---|:---|:---|:---|
| `dashboard` | `/` | `/dashboard` | 仪表台 |
| `customers` | `/customers` | `/customers` | 客户管理 |
| `orders` | `/orders` | `/orders` | 订单管理 |
| `process_flow` | `/process-flow` | `/process-flows` | 工艺流程 |
| `drawings` | `/drawings` | `/documents` | 图纸管理 |
| `inventory` | `/inventory` | `/inventory` | 库存管理 |
| `users` | `/users` | `/users` | 用户管理 (仅 Admin) |
| `notifications` | `/notifications`| `/notifications` | 通知中心 |
| `settings` | `/settings` | `/settings` | 系统设置 |
| `outsourcing` | `/outsourcing` | `/vendors` | 外协管理 |

---

### 第 3 层: 前后端双重防御机制

系统的安全性建立在“前端友好提示、后端强力防守”的双重保护原则之上：

#### 前端路由防御 (`client/src/router/index.js`)
前端利用 Vue Router 的 `beforeEach` 全局前置守卫：
* 用户每次跳转前，检查 `authStore` 中的 `permissions` 矩阵。
* 如果目标页面的 `can_view` 为 `0`，守卫会自动计算该用户当前拥有的**第一个** `can_view=1` 的页面进行跳转重定向，防止页面陷入无限循环或白屏；如果没有任何可访问页面，则重定向至登录页。

#### 后端依赖注入防守 (FastAPI `Depends`)
即使恶意用户通过修改前端源码绕过了按钮的禁用状态，后端每个有安全需要的路由都在 FastAPI 依赖项层面设置了强校验。例如在 `/documents` 图纸模块中：
```python
def require_drawings_view(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    if current_user.is_admin:
        return current_user
    perm = _get_drawings_perm(current_user, db)
    if not perm or not perm.can_view:
        raise HTTPException(status_code=403, detail="权限不足：无图纸查看权限")
    return current_user
```
在路由 Handler 中，只需挂载 `Depends(require_drawings_view)` 或 `Depends(require_drawings_edit)`，FastAPI 就会在执行业务前自动拦截并完成鉴权。

## 管理员防锁死机制

1. **前端锁定**：在“用户管理”页面编辑用户本身时，若被修改用户为当前登录的管理员，其“用户管理”可见与编辑开关会被锁定为开启且置灰不可更改，防止管理员手抖将自己踢出权限管理系统。
2. **后端唯一管理员守卫**：在后端删除用户或更改其管理员属性时，系统会优先查询库中 `is_admin=1` 且正处于激活状态的用户数量，确保系统内最少保留一个超级管理员账号，拒绝将最后一个管理员删除或降级为普通用户的请求。
