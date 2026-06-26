# 汇易通热流道管理系统 V2 (Hot Runner MES API)

一套轻量级、现代化的制造执行系统（MES），前后端分离架构，专为热流道及相关模具加工行业设计。包含客户管理、外协管理、工艺引擎、库存状态以及完整的订单调度闭环功能。

## 🌟 核心特性
- **纯净依赖**：仅需 Docker 环境即可一键拉起整个技术栈，无需在宿主机安装繁杂的 Python/Node.js 依赖。
- **现代化架构**：
  - 前端：`Vue 3` + `Vite` + `Element Plus` + `Tailwind CSS` (高颜值 Bento 风格面板，支持暗色模式)
  - 后端：`Python` + `FastAPI` (原生高并发与数据校验) + `SQLAlchemy`
  - 数据库：`PostgreSQL 15` (通过 Docker 编排)
- **核心模块**：
  - 订单与流程调度 (Orders & Process Flow)
  - 动态外协及客户 CRM (Vendors & Customers)
  - 实时仪表盘监控 (Dashboard)
  - 图纸与技术文档版本控制 (Documents)

## 🚀 极速启动指南 (Docker 方式)

为了确保能在任何电脑上做到“克隆即用”，本项目已深度容器化。**不需要**在宿主机单独安装 Python 或 Node.js环境。

### 1. 环境准备
确保您的计算机上已安装了：
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) 或 Docker Engine (Linux)
- [Git](https://git-scm.com/)

### 2. 克隆项目
```bash
git clone <repository_url> -b V2
cd G1
```

### 3. 一键启动
在项目根目录运行以下命令拉起所有服务：
```bash
docker compose up -d
```
*提示：首次运行会自动拉取基础镜像，并执行 npm install 及 pip install（由于网络原因国内可能需要一定时间），后续启动即秒开。*

### 4. 访问系统
当服务启动完毕后，在浏览器访问：
- **前端系统界面**：[http://localhost:5173](http://localhost:5173)
- **后端 API 文档 (Swagger)**：[http://localhost:8080/docs](http://localhost:8080/docs)

数据库已由 FastAPI 在首次启动时自动完成所有的表结构建置，您可直接登录使用！

## 🛠️ 常见问题 (FAQ)

**Q: 启动后界面一直是转圈/白屏？**
A: 请检查后端容器是否正常运行，可使用 `docker compose logs backend` 检查后端是否已启动完毕。

**Q: 想要修改代码后生效需要重启吗？**
A: 容器已经通过 volume 挂载了本地的 `./client` 和 `./server-python` 目录，并分别开启了 Vite 客户端热重载和 FastAPI 服务端的热重载 (`--reload`)。您只需在宿主机修改代码，服务会**自动热更新**！

**Q: 怎么完全清理本地环境并重置数据？**
A: 使用 `docker compose down -v` 可以彻底停止服务并清理数据库挂载的数据卷。
