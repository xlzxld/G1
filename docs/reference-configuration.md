 # 配置文件

 ## 环境变量 (`server/.env`)

 | 变量 | 默认值 | 说明 |
 |------|------|------|
 | JWT_SECRET | — | Access token 签名密钥 (必填) |
 | JWT_REFRESH_SECRET | — | Refresh token 签名密钥 (必填) |
 | JWT_ACCESS_EXPIRES | 15m | Access token 有效期 |
 | JWT_REFRESH_EXPIRES | 7d | Refresh token 有效期 |
 | PORT | 3000 | 服务端口 |
 | DB_PATH | ./data/mes.db | SQLite 数据库文件路径 (Knexfile 中使用) |

 示例:

 ```env
 JWT_SECRET=mes-dev-secret-change-in-production
 JWT_REFRESH_SECRET=mes-refresh-secret-change-in-production
 JWT_ACCESS_EXPIRES=15m
 JWT_REFRESH_EXPIRES=7d
 PORT=3000
 DB_PATH=./data/mes.db
 ```

 ## Knex 配置 (`server/knexfile.js`)

 ```js
 export default {
   client: 'better-sqlite3',
   connection: { filename: './data/mes.db' },
   useNullAsDefault: true,
   migrations: { directory: './src/data/migrations' },
   seeds: { directory: './src/data/seeds' },
 };
 ```

 `connection.filename` 指向 SQLite 文件。可用环境变量 `DB_PATH` 覆盖。

 迁移和种子脚本位于 `server/src/data/migrations/` 和 `server/src/data/seeds/`。  
 启动时 `app.js` 自动运行 `db.migrate.latest()`，所以无需手动迁移。

 ## Vite 配置 (`client/vite.config.js`)

 ```js
 export default defineConfig({
   plugins: [vue()],
   server: {
     port: 5173,
     proxy: { '/api': 'http://localhost:3000' },
   },
 });
 ```

 开发模式下 Vite 代理 `/api` 请求到后端端口 3000。

 ## Multer 上传限制

 图纸上传通过 Multer 中间件处理，配置在 `documents.js` 路由中：

- **存储:** 磁盘，路径为 `uploads/{order_no}/{category}/`
- **文件大小:** 最大 50MB
- **文件类型:** 仅图片 (png, jpg, gif, webp, bmp, svg)
- **文件名:** `v{timestamp}-{originalname}`

 ## Express Body Parser

 ```js
 app.use(express.json({ limit: "50mb" }));
 ```

 JSON body 限制为 50MB（与文件上传大小保持一致）。

 ## npm scripts

 **server/package.json:**

 | 命令 | 说明 |
 |------|------|
 | `npm start` | 生产模式启动 |
 | `npm run dev` | 开发模式（带 --watch 自动重启） |
 | `npm run migrate` | 手动运行迁移 |
 | `npm run seed` | 手动运行种子数据 |
 | `npm run db:reset` | 删除数据库 → 迁移 → 种子（重置到初始状态） |

 **client/package.json:**

 | 命令 | 说明 |
 |------|------|
 | `npm run dev` | Vite 开发服务器 (localhost:5173) |
 | `npm run build` | 生产构建 |
 | `npm run preview` | 预览生产构建 |

## 相关文档

- [快速上手](tutorial-getting-started.md) — 环境配置的使用场景
- [系统架构](explanation-architecture.md) — 配置项在架构中的位置
- [API 参考](reference-api.md) — 上传接口的 Multer 配置细节
