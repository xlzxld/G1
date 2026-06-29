# 汇易通热流道管理系统 V2 开发指南 (AGENTS.md)

本文件定义了本项目的常用控制指令、数据播种方法、前后端开发规范以及 AI 辅助技能路由规则。

---

## 🛠️ 常用开发与运行命令

项目完全基于 Docker 容器化运行，命令在 Windows 和 macOS 下表现一致（旧版 Docker 环境可使用 `docker-compose` 代替 `docker compose`）。

### 1. 启停与容器生命周期
*   **启动开发环境 (后台)**：
    ```bash
    docker compose up -d
    ```
*   **启动开发环境 (前台，查看实时日志)**：
    ```bash
    docker compose up
    ```
*   **关闭并释放容器**：
    ```bash
    docker compose down
    ```
*   **重启所有服务**：
    ```bash
    docker compose restart
    ```
*   **重启特定服务**：
    ```bash
    docker compose restart backend
    docker compose restart frontend
    ```
*   **更新依赖并强制重新构建镜像**：
    ```bash
    docker compose up -d --build
    ```

### 2. 查看日志与状态
*   **查看运行状态**：
    ```bash
    docker compose ps
    ```
*   **查看所有服务的滚动日志**：
    ```bash
    docker compose logs -f
    ```
*   **查看特定服务的滚动日志**：
    ```bash
    docker compose logs -f backend
    docker compose logs -f frontend
    ```

### 3. 数据播种与初始化
*   **初始化基础用户与系统权限 (必须)**：
    ```bash
    docker compose exec backend python seed.py
    ```
*   **注入演示模拟业务数据 (可选)**：
    ```bash
    docker compose exec backend python seed_mock.py
    ```

### 4. 深度重置环境
*   **清除所有容器及数据库卷 (清除全部数据)**：
    ```bash
    docker compose down -v
    ```

---

## 🎨 编码规范与指导

### 🐍 Python 后端 (server-python)
- **技术选型**：`FastAPI` + `SQLAlchemy 2.0` + `Pydantic v2` + `PostgreSQL`
- **代码结构**：
  - [models.py](file:///c:/Users/5600/Documents/G1/server-python/models.py)：数据库表结构定义。
  - [schemas.py](file:///c:/Users/5600/Documents/G1/server-python/schemas.py)：Pydantic 输入输出校验模型。
  - [routers/](file:///c:/Users/5600/Documents/G1/server-python/routers)：存放各业务模块 API 路由。
- **书写规范**：
  - 强制编写类型注解 (Type Hints)。
  - SQLAlchemy 查询强制使用 2.0 的 `select()` 语法，弃用 legacy query 语法。
  - 异常处理统一返回 `HTTPException`，并携带明确的错误详情信息。

### 📦 Vue 前端 (client)
- **技术选型**：`Vue 3` (Composition API) + `Vite` + `Pinia` + `Element Plus` + `Tailwind CSS`
- **书写规范**：
  - 采用 `<script setup>` 语法糖书写组件逻辑。
  - 组件样式以 Tailwind CSS 实用类为主，结合 Element Plus 实现 Bento 风格现代化 UI。
  - 组件及页面拆分明确：通用状态放置在 `src/stores/` 中，API 请求封装在 `src/api/` 下。
  - 所有 API 请求使用全局封装好的 Axios 实例，统一捕获并利用 Element Plus 的通知组件展示错误。

---

## 🧭 技能路由规则 (Skill Routing)

当开发助手处理特定类型的任务时，建议根据下表规则自动路由并调用对应技能（Skill）：

- **产品构想/头脑风暴/新功能构思** ➔ 调用 `/office-hours`
- **产品策略/大纲设计/范围评审** ➔ 调用 `/plan-ceo-review`
- **系统架构/底层技术架构设计** ➔ 调用 `/plan-eng-review`
- **设计系统/视觉评审/原型反馈** ➔ 调用 `/design-consultation` 或 `/plan-design-review`
- **全流程自动代码/方案评审管道** ➔ 调用 `/autoplan`
- **系统错误定位与 Bug 调试** ➔ 调用 `/investigate`
- **浏览器端自动化 QA 功能测试** ➔ 调用 `/qa` 或 `/qa-only`
- **代码变更评审/Diff 检查** ➔ 调用 `/review`
- **页面布局调整与视觉优化 (设计细节)** ➔ 调用 `/design-review`
- **部署、发布、推送 PR/合并分支** ➔ 调用 `/ship` 或 `/land-and-deploy`
- **保存当前会话/断点上下文** ➔ 调用 `/context-save`
- **还原先前保存的开发会话上下文** ➔ 调用 `/context-restore`
- **编写符合积压标准的规格说明书/问题单** ➔ 调用 `/spec`
