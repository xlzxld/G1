# 热流道生产管理系统 (Hot Runner MES)

一套面向热流道制造车间的生产执行系统，覆盖客户管理、订单录入、工序流转、图纸版本管理、库存跟踪和外协管理。

## 快速开始

```bash
# 后端 (http://localhost:3000)
cd server && npm install && npm run dev

# 前端 (http://localhost:5173)
cd client && npm install && npm run dev
```

详细教程见 [快速上手](docs/tutorial-getting-started.md)。

## 演示账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| laowang | 123456 | 车间工人 |
| xiaoli | 123456 | 设计师 |

## 功能模块

- **仪表台** — 6 张可点击汇总卡片（今日待处理、进行中、客户确认、今日完成、我的待办）
- **客户管理** — 动态联系方式、关联订单统计
- **订单管理** — 搜索排序分页、工序时间线、状态流转
- **工艺流程** — 步骤拖拽编辑、依赖/并行/外协配置、模板复制到订单
- **图纸管理** — 图片上传预览、版本管理、可编辑元数据
- **库存管理** — 总量/预留/预警、订单预留关联
- **用户管理** — 权限矩阵配置、管理员防锁死
- **通知中心** — 手动派发、规则引擎
- **系统设置** — 参数/密码/通知规则/操作日志
- **外协管理** — 外协厂商信息维护

## 技术栈

- **前端:** Vue 3 + Element Plus + Pinia + Vue Router + Vite + Axios
- **后端:** Node.js + Express + better-sqlite3 + Knex + JWT + bcrypt
- **数据库:** SQLite (14 张表, 迁移管理)
- **文件存储:** 本地 `uploads/{订单号}/{分类}/`

## 文档

完整文档在 [`docs/`](docs/README.md):

- [快速上手](docs/tutorial-getting-started.md)
- [API 参考](docs/reference-api.md)
- [数据库表结构](docs/reference-database.md)
- [配置文件](docs/reference-configuration.md)
- [系统架构](docs/explanation-architecture.md)
- [权限模型](docs/explanation-permission-model.md)
- [工序引擎](docs/explanation-process-engine.md)
- [创建工艺流程](docs/howto-setup-workflow.md)
- [管理用户和权限](docs/howto-manage-users.md)

设计决策见 [DESIGN.md](DESIGN.md)。

## 目录结构

```
.
├── README.md
├── DESIGN.md              # 设计文档和开发日志
├── CLAUDE.md              # AI 编码助手上下文
├── docs/                  # 完整文档
│   ├── README.md
│   ├── tutorial-getting-started.md
│   ├── howto-*.md
│   ├── reference-*.md
│   └── explanation-*.md
├── server/
│   ├── src/
│   │   ├── app.js         # 入口，Express 应用
│   │   ├── middleware/    # auth, permissions, audit
│   │   ├── routes/        # 10 个业务路由文件
│   │   ├── services/      # processEngine.js
│   │   └── data/          # migrations, seeds
│   ├── uploads/           # 图纸文件存储
│   ├── data/              # SQLite 数据库文件
│   ├── knexfile.js
│   ├── .env
│   └── package.json
└── client/
    ├── src/
    │   ├── main.js        # Vue 应用入口
    │   ├── App.vue        # 布局 (侧边栏 + 顶栏 + 主体)
    │   ├── router/        # 14 个路由定义 + 守卫
    │   ├── stores/        # Pinia auth store
    │   ├── api/           # Axios 实例 + 拦截器
    │   ├── components/    # Sidebar
    │   └── views/         # 15 个页面组件
    ├── index.html
    ├── vite.config.js
    └── package.json
```
