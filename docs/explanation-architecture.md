# 系统架构

## 分层架构

本系统采用现代化的前后端分离架构，配合 Docker Compose 进行容器化编排部署：

```
┌──────────────────────────────────────────────┐
│  浏览器 (Vue 3 客户端)                        │
│  Vue Router → 页面组件 → Pinia Store → Axios  │
└──────────────┬───────────────────────────────┘
               │ HTTP 请求 (带 Bearer JWT 令牌)
               │ (通过 Vite 代理或局域网宿主机 IP 进行分发)
┌──────────────▼───────────────────────────────┐
│  FastAPI 服务端 (Python 容器)                  │
│  ┌──────────┐ ┌────────────┐ ┌───────────┐   │
│  │  依赖注入 │ │  路由层    │ │ 业务函数  │   │
│  │  Depends │ │ /auth/     │ │   例如    │   │
│  │ (Auth/DB)│ │ /orders/   │ │  库存扣减 │   │
│  └──────────┘ └────────────┘ └───────────┘   │
│                      │                       │
│       ┌──────────────▼──────────────┐        │
│       │  SQLAlchemy ORM             │        │
│       ├─────────────────────────────┤        │
│       │  psycopg2 数据库驱动        │        │
│       │  PostgreSQL (db 容器)        │        │
│       └─────────────────────────────┘        │
└──────────────────────────────────────────────┘
               │ 文件写入
┌──────────────▼───────────────────────────────┐
│  uploads/{订单号}/{工序分类}/{文件名}          │
└──────────────────────────────────────────────┘
```

## 前端架构

**框架技术:** Vue 3 (Composition API + `<script setup>`)  
**状态管理:** Pinia (`useAuthStore`) — 仅用来管理用户登录状态、Token 缓存和个人权限矩阵。业务数据直接在各页面组件内通过 Axios 发起请求并进行局部状态存储，不设全局高密集业务 store。  
**路由导航:** Vue Router，拥有 10+ 核心业务路由，采用路由懒加载技术。路由守卫 `beforeEach` 在每次页面跳转时，会阻断式进行 JWT Token 的有效性判断及对应页面的 `page_permissions` 权限位判断。  
**UI 框架:** Element Plus，提供一套高度定制的深/浅色适配界面。  
**请求客户端:** Axios 实例 (`client/src/api/index.js`)。前端拦截器会在每个请求发出前，自动在 Header 中追加 `Authorization: Bearer <token>` 凭证。同时响应拦截器会对 401 认证异常进行全局拦截。

## 后端架构

**框架技术:** FastAPI (Python)  
FastAPI 提供了出色的运行性能和自动化的参数校验功能。系统依据业务领域进行了模块化拆分，各模块路由定义在 `server-python/routers/` 目录下，并在 `server-python/main.py` 中集中进行挂载与跨域配置。

**核心设计模式 — 依赖注入 (Dependency Injection):**
* **数据库会话管理**: 使用 `Depends(get_db)` 动态管理 SQLAlchemy `Session` 生命周期，确保每次 API 呼叫均能获得独立的连接，且在请求结束后自动关闭连接释放资源。
* **认证与防卫**: 敏感接口直接挂载 `Depends(get_current_user)` 或 `Depends(verify_admin)` 依赖函数。FastAPI 会自动拦截请求头、校验 JWT 并解析出对应用户行，非合法访问会直接返回 `401 Unauthorized` 状态码。

**全局操作审计中间件:**  
在 `main.py` 中挂载了 HTTP 中间件 `audit_log_middleware`，拦截所有 `POST`, `PUT`, `DELETE` 写入操作。中间件会自动解析 Authorization Header 以追踪操作人员姓名，并将操作对象及汉化后的操作事件详情记录写入 `audit_logs` 表，提供严密的生产追溯链路。

## 数据持久层

**数据库**: PostgreSQL (独立运行于 `db` 容器中)  
**数据库驱动**: psycopg2 (支持高性能数据库连接与事务并发控制)  
**ORM (对象关系映射)**: SQLAlchemy  
* **结构同步**: 后端启动时，通过 `Base.metadata.create_all(bind=engine)` 自动扫描映射模型，确保在 PostgreSQL 中自动建立所需的全部数据表与索引约束，无需手动运行迁移脚本。
* **并发防卫**: 涉及库存预留和物理扣减等并发操作时，SQLAlchemy 模型底层使用 `with_for_update()` 产生排他锁锁行，防止高并发下产生库存超卖或数据覆盖冲突。

## 静态文件与图纸存储

车间实操作业上传的图纸、照片等文件直接保存在后端服务器所在的本地磁盘空间中：
* **存储结构**: `uploads/{order_no}/{category}/v{timestamp}-{original_name}`。
* **接口服务**: 后端通过 FastAPI 静态文件服务模块直接对外挂载访问路径：
  ```python
  app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
  ```
  前端可直接通过 `VITE_API_BASE_URL/uploads/...` 路径下载或预览图片，支持带有中文文件名的 URL 编码解析。

## 局域网接入共享设计

为支持车间内的移动终端（平板、手机）共同协作，系统支持局域网接入：
* **Vite 监听**: 前端 `vite.config.js` 配置 `host: true`，使开发服务器监听全部局域网网卡。
* **容器网络桥接**: 在 Docker Compose 网络中，前端容器配置的 `VITE_API_BASE_URL` 会绑定宿主机的真实局域网 IP（例如 `http://192.168.5.33:8080`）。当移动设备接入局域网并访问前端时，浏览器渲染出的页面请求会被动态分发至该 IP 对应的后端容器，实现稳定的局域网协同。
