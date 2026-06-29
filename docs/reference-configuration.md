# 配置文件参考 (Configuration Reference)

本系统采用容器化部署，配置逻辑分布在 Docker Compose 环境变量、后端数据库初始化及前端 Vite 代理设置中。

---

## 1. Docker Compose 配置与环境变量

全局容器编排配置位于根目录下的 [docker-compose.yml](file:///Users/xlz/Documents/G1-V2/docker-compose.yml)。

### 后端服务 (`backend`) 环境变量
后端容器基于 `server-python` 目录构建，并通过环境变量注入配置：

| 环境变量名称 | 默认值/示例 | 详细说明 |
|:---|:---|:---|
| `DATABASE_URL` | `postgresql://mes_user:mes_password@db:5432/hotrunner_mes` | PostgreSQL 数据库连接字符串（通过 Docker 桥接网络直接访问同组的 `db` 服务）。 |
| `VITE_API_BASE_URL`| `http://192.168.5.33:8080` | 后端服务暴露给前端浏览器访问的实际宿主机基准地址（推荐填写局域网 IP 以支持移动端访问）。 |

### 前端服务 (`frontend`) 环境变量
前端容器基于 `client` 目录构建，在构建和运行时需要将 API 基准地址传入：

| 环境变量名称 | 默认值/示例 | 详细说明 |
|:---|:---|:---|
| `VITE_API_BASE_URL`| `http://192.168.5.33:8080` | 前端页面渲染后发起 HTTP 请求的目标后端宿主机 API 地址。 |

---

## 2. 后端配置与依赖 (`server-python/`)

### 数据库配置 (`database.py`)
后端通过 Python 动态加载环境变量：
* **本地加载**：调用 `load_dotenv()`，如果当前目录下存在 `.env` 文件则会加载。
* **默认值**：如果系统未注入 `DATABASE_URL` 环境变量，则默认降级连接本地测试数据库 `postgresql://postgres:postgres@localhost:5432/hotrunner_mes`。

### 后端核心依赖清单 (`requirements.txt`)
后端基于 Python 3.11 运行，依赖以下核心模块：
* `fastapi`：API 框架核心。
* `uvicorn`：ASGI 服务器，托管 FastAPI 运行。
* `sqlalchemy`：关系型对象映射（ORM）。
* `psycopg2-binary`：PostgreSQL 官方数据库驱动。
* `python-jose[cryptography]`：用于 JWT 签名认证解密。
* `bcrypt`：用于密码强哈希计算。
* `python-multipart`：用于支持图纸、照片的文件上传请求体解析。

---

## 3. 前端 Vite 代理与监控配置 (`client/vite.config.js`)

前端通过 Vite 进行工程构建与反向代理，配置文件为 `client/vite.config.js`：

```js
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true, // 开启监听全部网卡，允许局域网设备接入
    allowedHosts: true, // 允许所有本地域名与 IP 访问
    proxy: { 
      // 代理前端 Axios 的 /api 请求到后端容器
      '/api': { 
        target: 'http://backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') // 去掉 /api 前缀，匹配 FastAPI 路由
      },
      // 代理静态文件 uploads 请求到后端静态挂载路径
      '/uploads': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    },
    watch: {
      usePolling: true, // 容器环境下开启轮询监听，确保 HMR (热更新) 能够跨容器边界生效
    }
  }
});
```

---

## 4. 图纸与照片上传限制

图纸文件通过 FastAPI 的 `UploadFile` 在路由 `documents.py` 中处理：
* **最大允许限制**：50MB。
* **格式过滤**：仅限图片格式文件（`png`, `jpg`, `jpeg`, `gif`, `webp`, `bmp`, `svg`）。
* **存储命名规范**：`v{timestamp}-{original_filename}` 自动加上递增版本号。

---

## 5. 项目常用开发运行指令 (Scripts)

### 全局服务管理（根目录下执行）
* **构建并启动全部容器服务**：
  ```bash
  docker-compose up --build
  ```
* **关闭服务并保留数据**：
  ```bash
  docker-compose down
  ```
* **彻底清除数据并销毁容器卷（慎用）**：
  ```bash
  docker-compose down -v
  ```
* **在后端容器中导入默认系统权限与三个初始账号**：
  ```bash
  docker-compose exec backend python seed.py
  ```
* **在后端容器中导入全套测试模拟业务数据**：
  ```bash
  docker-compose exec backend python seed_mock.py
  ```

### 前端开发管理（`client/` 目录下执行，需本地安装 Node.js）
* **启动本地热重载开发服务器 (localhost:5173)**：
  ```bash
  npm run dev
  ```
* **打包生产部署静态资源文件**：
  ```bash
  npm run build
  ```
