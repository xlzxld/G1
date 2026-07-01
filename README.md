# 汇易通热流道管理系统 V2 (Hot Runner MES V2)

一套轻量级、现代化的制造执行系统（MES），专为热流道及相关模具加工行业设计。本系统采用前后端分离架构，集成了客户管理、外协管理、工艺引擎、库存状态以及完整的订单调度闭环功能。

---

## 🌟 核心特性

- **一键极速部署**：深度容器化设计，彻底分离了开发与正式生产环境。无需在宿主机配置复杂的 Python/Node.js 开发环境。
- **现代化技术栈**：
  - **前端**：`Vue 3` + `Vite` + `Element Plus` + `Tailwind CSS` (采用 Bento 风格面板，支持暗色模式，极致视觉体验)
  - **后端**：`Python` + `FastAPI` (原生高并发与强类型数据校验) + `SQLAlchemy` ORM
  - **数据库**：`PostgreSQL 15`
- **核心业务模块**：
  - **订单与流程调度 (Orders & Process Flow)**：追踪生产进度，优化派工管理。
  - **外协与客户管理 (CRM & Vendors)**：动态外协进度跟踪及客户关系维护。
  - **实时仪表盘 (Dashboard)**：关键生产指标与库存状态图表化展示。
  - **图纸与文档版本控制 (Documents)**：加工图纸、工艺文档版本可追溯，减少人为差错。

---

## 🏗️ 架构与环境隔离

系统现在支持两套彻底隔离的架构：

### 开发环境 (`docker-compose.dev.yml`)
适合本地开发、代码热更新。暴露测试端口：
- **前端 (frontend)**：`http://localhost:9956` (带 Vite 热更新)
- **后端 (backend)**：`http://localhost:8080/docs` (带 Uvicorn reload)
- **数据库 (db)**：`5432` 映射到宿主机。

### 生产环境 (`docker-compose.prod.yml`)
适合公网/正式服务器部署。封闭敏感端口，统一由 Caddy 反向代理网关接管：
- **入口 (frontend / Caddy)**：暴露出标准的 `80` 和 `443` 端口。静态文件极速分发，`/api` 无缝代理至后端。
- **后端 (backend)**：纯内网运行（`8000` 不暴露），采用多 workers 进程提供高并发承载。
- **数据库 (db)**：纯内网运行（`5432` 不暴露）。

---

## 🚀 极速启动指南 (Docker 部署)

无论是在 **Windows** (PowerShell / CMD) 还是 **macOS** (Terminal) 上，部署步骤均完全一致。

### 1. 环境准备
确保您的计算机上已安装并启动了以下软件：
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (已内置 `docker compose` 命令行工具)
- [Git](https://git-scm.com/)

### 2. 克隆并进入项目目录
```bash
git clone <repository_url> -b V2
cd G1
```

### 3. 一键启动所有服务 (以开发环境为例)
由于采用了环境解耦，所有的命令均需指定使用的编排文件 `-f docker-compose.dev.yml`：
```bash
docker compose -f docker-compose.dev.yml up -d
```
> **💡 提示**：
> 1. 如果您的 Docker 环境较旧，可能需要将命令改为 `docker-compose -f docker-compose.dev.yml up -d`。
> 2. 首次运行会自动拉取基础镜像，后续再次启动即可秒开。

### 4. 访问系统
服务启动完毕后即可打开浏览器访问：
- **前端系统界面**：[http://localhost:9956](http://localhost:9956)
- **后端 API 文档**：[http://localhost:8080/docs](http://localhost:8080/docs)

---

## 💾 数据库种子数据注入

当服务首次拉起，或者您重置了数据库后，需要手动注入初始数据以进行使用或演示：

### 1. 导入基础系统权限与用户（必须）
```bash
docker compose -f docker-compose.dev.yml exec backend python seed.py
```

### 2. 导入演示模拟业务数据（可选，推荐）
```bash
docker compose -f docker-compose.dev.yml exec backend python seed_mock.py
```

---

## 🐳 Docker Compose 常用运维命令 (以 Dev 为例)

### 1. 启停控制
*   **后台启动服务**：
    ```bash
    docker compose -f docker-compose.dev.yml up -d
    ```
*   **停止并清理服务容器（最常用，推荐）**：
    ```bash
    docker compose -f docker-compose.dev.yml down
    ```
*   **强制重新构建镜像**：
    ```bash
    docker compose -f docker-compose.dev.yml up -d --build
    ```

### 2. 日志与状态查询
*   **查看所有服务实时滚动日志**：
    ```bash
    docker compose -f docker-compose.dev.yml logs -f
    ```
*   **进入后端容器**：
    ```bash
    docker compose -f docker-compose.dev.yml exec backend sh
    ```

---

## 🌐 局域网/移动端访问与 IP 配置

如果您想使用手机或其他处于同一局域网的电脑来访问开发环境系统：

### 1. 获取宿主机的局域网 IP (例如 `192.168.1.10`)
在 Windows 终端中输入 `ipconfig`，或在 Mac 中输入 `ifconfig` 获取 IPv4 地址。

### 2. 修改环境变量
在项目根目录编辑 `.env.dev` 文件，将 `VITE_API_BASE_URL` 的前缀替换为您的局域网 IP：
```env
VITE_API_BASE_URL=http://192.168.1.10:8080
```

### 3. 重启容器生效
```bash
docker compose -f docker-compose.dev.yml up -d
```
重启后，手机访问 `http://192.168.1.10:9956` 即可。

---

## 🧹 深度重置与环境清理

如果您需要清空数据库中的所有数据并重置所有结构，请执行以下命令：
```bash
docker compose -f docker-compose.dev.yml down -v
```
> **⚠️ 警告**：
> `-v` 参数会永久删除挂载的命名数据卷，从而清空所有数据库表。下一次启动后需重新运行种子数据注入命令。
