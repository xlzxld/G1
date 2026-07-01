# 🐳 Docker Compose 项目运维指南

由于系统实施了开发与生产环境的强隔离，所有的 `docker compose` 运维命令都需要显式指定环境编排文件，例如 `-f docker-compose.dev.yml`（开发环境）或 `-f docker-compose.prod.yml`（生产环境）。本指南以开发环境为例。

---

## 📌 一、 常用控制命令

所有命令均需在**项目根目录**下运行。

### 1. 启动服务（开机）
*   **后台启动（最常用）**：
    ```bash
    docker compose -f docker-compose.dev.yml up -d
    ```
*   **强制重新构建镜像并启动**：
    ```bash
    docker compose -f docker-compose.dev.yml up -d --build
    ```
    *当修改了 `Dockerfile.dev`、后端 `requirements.txt` 或前端 `package.json` 时，必须使用此命令重新构建镜像。*

### 2. 停止服务（关机）
*   **停止并删除容器（推荐，最干净）**：
    ```bash
    docker compose -f docker-compose.dev.yml down
    ```
    *停止运行并释放容器资源，但**不会**删除您的数据库数据卷。*
*   **仅停止容器（不删除）**：
    ```bash
    docker compose -f docker-compose.dev.yml stop
    ```

### 3. 重启服务（Restart）
*   **重启所有服务**：
    ```bash
    docker compose -f docker-compose.dev.yml restart
    ```
*   **仅重启特定服务（如只重启后端）**：
    ```bash
    docker compose -f docker-compose.dev.yml restart backend
    ```

---

## 🔍 二、 状态监控与调试

### 1. 查看容器运行状态
```bash
docker compose -f docker-compose.dev.yml ps
```

### 2. 查看日志
*   **查看所有服务实时日志**：
    ```bash
    docker compose -f docker-compose.dev.yml logs -f
    ```
*   **只查看某一服务的日志（如只看后端）**：
    ```bash
    docker compose -f docker-compose.dev.yml logs -f backend
    ```

### 3. 进入容器内部命令行
*   **进入后端容器**：
    ```bash
    docker compose -f docker-compose.dev.yml exec backend sh
    ```

---

## 💾 三、 数据同步与种子导入

在项目首次拉起或数据库重置后，需要执行以下命令进行初始化：

*   **导入基础系统权限与用户（必须）**：
    ```bash
    docker compose -f docker-compose.dev.yml exec backend python seed.py
    ```
*   **导入演示模拟业务数据（可选，推荐）**：
    ```bash
    docker compose -f docker-compose.dev.yml exec backend python seed_mock.py
    ```

---

## 🌐 四、 局域网访问与 IP 配置

### 1. 当前网络配置状态
环境已经实现了配置解耦。开发环境变量均存放在根目录的 `.env.dev` 文件中，例如：
```env
# 当前无线网络 IP
VITE_API_BASE_URL=http://192.168.1.10:8080
```

### 2. 生效局域网配置
如果您修改了 `.env.dev` 中的 IP，只需执行：
```bash
docker compose -f docker-compose.dev.yml up -d
```
启动后，局域网内的其他设备可通过以下地址访问系统：
*   **前端 Web 系统**：`http://192.168.1.10:9956`
*   **后端 API 文档**：`http://192.168.1.10:8080/docs`

---

## 🧹 五、 深度清理与重置

*   **完全清空数据库（谨慎！）**：
    如果你想清除所有数据库数据和结构，完全重新开始：
    ```bash
    docker compose -f docker-compose.dev.yml down -v
    ```
    *`-v` 参数会删除持久化数据卷。下次启动后需重新运行种子导入脚本。*
