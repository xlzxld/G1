 # 系统架构

 ## 分层架构

 ```
 ┌──────────────────────────────────────────────┐
 │  浏览器 (Vue 3)                               │
 │  Vue Router → 页面组件 → Pinia Store → Axios  │
 └──────────────┬───────────────────────────────┘
                │ HTTP (JSON + JWT)
 ┌──────────────▼───────────────────────────────┐
 │  Express 服务端                                │
 │  ┌──────────┐ ┌────────────┐ ┌───────────┐  │
 │  │ 中间件层  │ │  路由层     │ │  服务层   │  │
 │  │ auth     │ │ /api/auth/  │ │ process-  │  │
 │  │ perm     │ │ /api/orders │ │ Engine    │  │
 │  │ audit    │ │ /api/users  │ │           │  │
 │  └──────────┘ └────────────┘ └───────────┘  │
 │                      │                       │
 │       ┌──────────────▼──────────────┐        │
 │       │  Knex 查询构建器            │        │
 │       ├─────────────────────────────┤        │
 │       │  better-sqlite3             │        │
 │       │  SQLite (data/mes.db)       │        │
 │       └─────────────────────────────┘        │
 └──────────────────────────────────────────────┘
                │ 文件系统
 ┌──────────────▼───────────────────────────────┐
 │  uploads/{订单号}/{分类}/{文件名}             │
 └──────────────────────────────────────────────┘
 ```

 ## 前端架构

 **框架:** Vue 3 (Composition API + `<script setup>`)

 **状态管理:** Pinia (`useAuthStore`) — 只用于认证状态。业务数据在各页面组件内通过 Axios 直接请求，无集中式业务 store。

 **路由:** Vue Router，14 个路由，懒加载页面组件。路由守卫 `beforeEach` 执行认证检查和权限检查。

 **UI 框架:** Element Plus，全局注册，所有图标全局注册供模板使用。

 **请求:** Axios 实例 (`/client/src/api/index.js`)，baseURL=`/api`，请求拦截器自动添加 Bearer token，响应拦截器自动处理 401 → refresh token → 重试。

 ## 后端架构

 **框架:** Express (纯路由，无控制器层抽象)

 每个业务模块一个路由文件，直接操作 Knex 查询。服务层仅在复杂逻辑处抽取（`processEngine.js`）。

 **中间件执行顺序:**
 1. `cors()` — 跨域
 2. `express.json({ limit: "50mb" })` — body 解析
 3. 路由级: `authMiddleware` → `requirePermission(pageKey, action)` → 业务 handler

 **认证流程:**
- 登录返回 access token (15min) + refresh token (7d)
- 每个 API 请求携带 access token
- 前端拦截器: 401 → 用 refresh token 换取新的 access token → 重试原请求
- 登出时 refresh token 加入内存黑名单 (`refreshBlacklist` Set)

 ## 数据层

 **数据库:** SQLite 单文件 (`data/mes.db`)  
 **迁移:** Knex，启动时自动运行 `db.migrate.latest()`  
 **种子:** 如果 `users` 表为空，自动运行 `db.seed.run()`（创建演示数据）

 **外键:** 所有表间引用使用 SQL 外键约束，级联行为由 ON DELETE 子句定义（CASCADE / SET NULL）。SQLite 中通过 `PRAGMA foreign_keys = ON` 启用（better-sqlite3 默认开启）。

 ## 文件存储

 图纸文件直接存储在服务器本地文件系统，目录结构:

 ```
 uploads/
   2026001/
     图纸/
       v1737000000-drawing.png
       v1737100000-drawing-v2.png
 ```

 下载通过自定义 Express 路由 `/api/download/:order_no/:category/:filename` 处理，支持 URL 编码中文文件名。

 ## 技术选型理由

- **Vue 3 + Element Plus:** 中文生态成熟，适合内部管理系统
- **Express:** 轻量，路由即文档，无需 ORM 的黑盒抽象
- **better-sqlite3:** 同步 API，零配置，单文件部署，适合车间场景
- **Knex:** 迁移管理 + 查询构建，比原始 SQL 安全（参数化），比 ORM 透明
- **JWT 双 token:** 短 access token 限制泄露窗口，长 refresh token 减少重复登录

## 相关文档

- [API 参考](reference-api.md) — 路由层完整接口文档
- [数据库表结构](reference-database.md) — 数据模型定义
- [权限模型](explanation-permission-model.md) — 中间件层的权限设计
- [工序引擎](explanation-process-engine.md) — 服务层的核心业务逻辑
