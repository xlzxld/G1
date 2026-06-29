# 🐳 Docker Compose 项目运维指南

本指南整理了本项目在 Docker 环境下的常用运维命令与网络配置说明，方便日常开发与局域网调试。

---

## 📌 一、 常用控制命令

所有命令均需在**项目根目录**（包含 `docker-compose.yml` 的目录）下运行。

### 1. 启动服务（开机）
*   **后台启动（最常用）**：
    ```bash
    docker compose up -d
    ```
    *后台拉起所有服务，释放当前控制台。*
*   **前台启动（看实时日志）**：
    ```bash
    docker compose up
    ```
    *日志直接输出在控制台。按 `Ctrl + C` 会关闭并停止所有容器。*
*   **强制重新构建镜像并启动**：
    ```bash
    docker compose up -d --build
    ```
    *当修改了 `Dockerfile`、后端 `requirements.txt` 或前端 `package.json` 等环境配置时，必须使用此命令重新构建镜像。*

### 2. 停止服务（关机）
*   **停止并删除容器（推荐，最干净）**：
    ```bash
    docker compose down
    ```
    *停止运行并释放容器资源，但**不会**删除您的数据库数据卷。*
*   **仅停止容器（不删除）**：
    ```bash
    docker compose stop
    ```
*   **重新运行已被 stop 的容器**：
    ```bash
    docker compose start
    ```

### 3. 重启服务（Restart）
*   **重启所有服务**：
    ```bash
    docker compose restart
    ```
*   **仅重启特定服务（如只重启后端）**：
    ```bash
    docker compose restart backend
    ```

---

## 🔍 二、 状态监控与调试

### 1. 查看容器运行状态
```bash
docker compose ps
```
*显示所有容器的 ID、运行状态（Up / Exit）和端口映射。*

### 2. 查看日志
*   **查看所有服务实时日志**：
    ```bash
    docker compose logs -f
    ```
    *按 `Ctrl + C` 可以退出日志监控。*
*   **只查看某一服务的日志（如只看后端）**：
    ```bash
    docker compose logs -f backend
    ```

### 3. 进入容器内部命令行
*   **进入后端容器**：
    ```bash
    docker compose exec backend sh
    ```
    *输入 `exit` 退出容器。*

---

## 💾 三、 数据同步与种子导入

在项目首次拉起或数据库重置后，需要执行以下命令进行初始化：

*   **导入基础系统权限与用户（必须）**：
    ```bash
    docker compose exec backend python seed.py
    ```
*   **导入演示模拟业务数据（可选，推荐）**：
    ```bash
    docker compose exec backend python seed_mock.py
    ```

---

## 🌐 四、 局域网访问与 IP 配置

为了在手机或局域网其他设备中访问系统，需要在 `docker-compose.yml` 中配置宿主机的局域网 IP。

### 1. 当前网络配置状态
在 [docker-compose.yml](file:///c:/Users/5600/Documents/G1/docker-compose.yml) 中，`VITE_API_BASE_URL` 已经为您做好了多环境兼容：

```yaml
    environment:
      - DATABASE_URL=postgresql://mes_user:mes_password@db:5432/hotrunner_mes
      # 当前无线网络 IP (WLAN 2)
      - VITE_API_BASE_URL=http://192.168.1.10:8080
      # 备用环境 IP
      # - VITE_API_BASE_URL=http://192.168.5.33:8080
```

### 2. 局域网访问地址
启动后，局域网内的其他设备（如手机）可通过以下地址进行访问：
*   **前端 Web 系统**：`http://192.168.1.10:9956`
*   **后端 API 文档**：`http://192.168.1.10:8080/docs`

---

## 🧹 五、 深度清理与重置

*   **完全清空数据库（谨慎！）**：
    如果你想清除所有数据库数据和结构，完全重新开始：
    ```bash
    docker compose down -v
    ```
    *`-v` 参数会删除名为 `postgres_data` 的持久化数据卷。下次启动后需重新运行种子导入脚本。*
