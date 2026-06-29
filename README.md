# 汇易通热流道管理系统 V2 (Hot Runner MES V2)

一套轻量级、现代化的制造执行系统（MES），专为热流道及相关模具加工行业设计。本系统采用前后端分离架构，集成了客户管理、外协管理、工艺引擎、库存状态以及完整的订单调度闭环功能。

---

## 🌟 核心特性

- **一键极速部署**：深度容器化设计，仅需安装 Docker 即可在任何环境下一键拉起整个技术栈，无需在宿主机配置复杂的 Python/Node.js 开发环境。
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

## 🏗️ 架构与默认端口映射

启动后，容器服务在宿主机的端口映射如下：

| 服务名称 | 容器端口 | 宿主机映射端口 | 默认访问地址 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **前端 (frontend)** | `5173` | **`9956`** | [http://localhost:9956](http://localhost:9956) | Vue 3 客户端页面 |
| **后端 (backend)** | `8000` | **`8080`** | [http://localhost:8080/docs](http://localhost:8080/docs) | FastAPI 接口文档 (Swagger UI) |
| **数据库 (db)** | `5432` | **`5432`** | `localhost:5432` | PostgreSQL 15 数据库服务 |

---

## 🚀 极速启动指南 (Docker 部署)

无论是在 **Windows** (PowerShell / CMD) 还是 **macOS** (Terminal) 上，部署步骤均完全一致。

### 1. 环境准备
确保您的计算机上已安装并启动了以下软件：
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (已内置 `docker compose` 命令行工具)
- [Git](https://git-scm.com/)

### 2. 克隆并进入项目目录
打开您的终端（Windows 用户建议使用 PowerShell 或 Git Bash，Mac 用户使用 Terminal），运行：
```bash
git clone <repository_url> -b V2
cd G1
```

### 3. 一键启动所有服务
在项目根目录下，执行以下命令在后台启动系统：
```bash
docker compose up -d
```
> **💡 提示**：
> 1. 如果您的 Docker 环境较旧，可能需要将命令中的空格改为连字符，即运行 `docker-compose up -d`。
> 2. 首次运行会自动拉取基础镜像，并在容器内安装必要的 npm 与 pip 依赖包（视网络情况可能需要数分钟时间），后续再次启动即可秒开。

### 4. 访问系统
服务启动完毕后即可打开浏览器访问：
- **前端系统界面**：[http://localhost:9956](http://localhost:9956)
- **后端 API 文档 (Swagger)**：[http://localhost:8080/docs](http://localhost:8080/docs)

---

## 💾 数据库种子数据注入

当服务首次拉起，或者您重置了数据库后，需要手动注入初始数据以进行使用或演示。请在**项目根目录**下运行以下命令：

### 1. 导入基础系统权限与用户（必须）
此步骤会创建系统角色、权限以及默认管理员账号：
```bash
docker compose exec backend python seed.py
```
*执行成功后，您可以使用默认生成的管理员账号进行登录。*

### 2. 导入演示模拟业务数据（可选，推荐）
如果您需要测试或展示系统的全套业务闭环（如包含测试订单、客户、外协流程、工艺卡等），请运行：
```bash
docker compose exec backend python seed_mock.py
```

---

## 🐳 Docker Compose 常用运维命令 (Windows & macOS 通用)

所有命令均须在包含 `docker-compose.yml` 的项目根目录下运行。

### 1. 启停控制
*   **后台启动服务**：
    ```bash
    docker compose up -d
    ```
*   **前台启动服务（查看实时日志输出）**：
    ```bash
    docker compose up
    ```
    *注意：前台运行时，按下 `Ctrl + C` 会关闭并停止所有服务容器。*
*   **停止并清理服务容器（最常用，推荐）**：
    ```bash
    docker compose down
    ```
    *该命令会安全停止并删除容器，但**保留**您的数据库数据卷。*
*   **仅暂停容器（不释放容器）**：
    ```bash
    docker compose stop
    ```
*   **恢复已暂停的容器**：
    ```bash
    docker compose start
    ```
*   **重启所有服务**：
    ```bash
    docker compose restart
    ```

### 2. 局部重启与配置更新
*   **单独重启后端服务**：
    ```bash
    docker compose restart backend
    ```
*   **单独重启前端服务**：
    ```bash
    docker compose restart frontend
    ```
*   **更新依赖并强制重新构建**：
    如果您修改了 `server-python/requirements.txt` 或 `client/package.json`，或者更改了前端/后端的 `Dockerfile`，需要强制 Docker 重新构建镜像后启动：
    ```bash
    docker compose up -d --build
    ```

### 3. 日志与状态查询
*   **查看服务运行状态**：
    ```bash
    docker compose ps
    ```
*   **查看所有服务合并后的实时滚动日志**：
    ```bash
    docker compose logs -f
    ```
*   **仅查看后端/前端的实时日志**：
    ```bash
    docker compose logs -f backend
    docker compose logs -f frontend
    ```

### 4. 进入容器内命令行环境
如果您需要进入容器内部执行其他指令（如数据库迁移等），可以使用：
*   **进入后端容器**：
    ```bash
    docker compose exec backend sh
    ```
*   **进入前端容器**：
    ```bash
    docker compose exec frontend sh
    ```
    *输入 `exit` 即可退出容器命令行并回到宿主机。*

---

## 🌐 局域网/移动端访问与 IP 配置

如果您想使用手机或其他处于同一局域网的电脑来访问该 MES 系统，需要将前端配置中的 API 地址绑定为宿主机的局域网 IP。

### 1. 获取宿主机的局域网 IP
- **Windows 环境**：
  打开 PowerShell 或 CMD，输入：
  ```cmd
  ipconfig
  ```
  查找有源网卡（如“无线局域网适配器 WLAN”）下的 `IPv4 地址`（通常类似于 `192.168.x.x`）。
- **macOS / Linux 环境**：
  打开 Terminal，输入：
  ```bash
  ifconfig | grep "inet " | grep -v 127.0.0.1
  # 或者输入：
  ip a
  ```
  寻找与局域网段对应的 IP 地址（例如 `192.168.1.10`）。

### 2. 配置环境变量
修改根目录下的 [docker-compose.yml](file:///c:/Users/5600/Documents/G1/docker-compose.yml) 文件，找到 `backend` 和 `frontend` 服务下的 `VITE_API_BASE_URL`，将其更改为您宿主机的局域网 IP（以 `192.168.1.10` 为例）：

```yaml
  backend:
    ...
    environment:
      - DATABASE_URL=postgresql://mes_user:mes_password@db:5432/hotrunner_mes
      - VITE_API_BASE_URL=http://192.168.1.10:8080  # 更改为您的实际局域网 IP

  frontend:
    ...
    environment:
      - VITE_API_BASE_URL=http://192.168.1.10:8080  # 更改为您的实际局域网 IP
```

### 3. 重启容器生效
保存文件后，在终端中重新启动容器：
```bash
docker compose up -d
```
重启后，您局域网内的其他设备即可通过以下地址访问系统：
- **前端 Web 系统**：`http://<宿主机IP>:9956`
- **后端 API 文档**：`http://<宿主机IP>:8080/docs`

---

## 🧹 深度重置与环境清理

如果您需要清空数据库中的所有数据并重置所有结构，请执行以下命令：
```bash
docker compose down -v
```
> **⚠️ 警告**：
> `-v` 参数会永久删除挂载的命名数据卷 `postgres_data`，从而清空所有数据库表和存入的数据。下一次启动后，您需要重新运行种子数据注入命令来进行初始化。

---

## 🛠️ 常见问题 (FAQ)

**Q：启动后浏览器打开一直处于加载/白屏状态？**
1. 请先检查容器运行状态，执行 `docker compose ps` 确保所有容器都是 `Up` 状态。
2. 检查后端是否已正确启动完毕。执行 `docker compose logs backend` 查看是否有连接数据库失败等报错。
3. 检查浏览器控制台 (F12) 中的网络请求错误。如果是局域网访问，确认 `docker-compose.yml` 中的 `VITE_API_BASE_URL` IP 地址与您当前的宿主机局域网 IP 保持一致。

**Q：修改了本地的代码需要手动构建镜像或重启容器吗？**
- **不需要**。项目的 `docker-compose.yml` 已经把本地 of `./client` 和 `./server-python` 目录以 Volume 卷的方式挂载到容器内部。
- 前端项目开启了 Vite 的热重载 (HMR)，后端项目开启了 uvicorn 的 `--reload` 机制。您直接在宿主机修改代码，容器内会自动检测并实时热生效。
