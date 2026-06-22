# 快速上手: 运行热流道生产管理系统

这篇教程带你从零开始，10 分钟内看到一个可用的生产管理系统。

## 你需要什么

- Node.js 18+ (推荐 20 LTS)
- npm 9+
- 终端和浏览器

## 第 1 步: 安装后端依赖

```bash
cd server
npm install
```

这会安装 Express、better-sqlite3、Knex、JWT 等依赖。

## 第 2 步: 配置环境变量

后端已自带 `.env` 文件，可直接使用。如果你需要修改:

```bash
# server/.env
JWT_SECRET=your-secret-key
JWT_REFRESH_SECRET=your-refresh-secret
PORT=3000
```

## 第 3 步: 启动后端

```bash
npm run dev
```

输出:

```
Migrations up to date
Seed data created
Server running on http://localhost:3000
```

首次启动自动创建数据库 (`data/mes.db`)、运行迁移、插入演示数据。

## 第 4 步: 安装和启动前端

打开另一个终端:

```bash
cd client
npm install
npm run dev
```

输出:

```
VITE v6.x.x  ready in xxx ms
→  Local:   http://localhost:5173/
```

## 第 5 步: 登录系统

打开浏览器访问 `http://localhost:5173`，登录页已出现。用演示账号登录:

- **管理员:** 用户名 `admin`，密码 `admin123`
- **车间工人:** 用户名 `laowang`，密码 `123456`
- **设计师:** 用户名 `xiaoli`，密码 `123456`

## 你看到了什么

登录后进入**仪表台**，顶部显示 6 张统计卡片:

- 今日待处理订单
- 进行中订单
- 客户确认中
- 库存预警
- 今日完成
- 我的待办

左侧菜单有 10 个功能模块。点开任意一个试试。

## 快速验证: 走一遍完整流程

用 admin 账号，几分钟体验核心链路:

1. **创建客户** — 点击"客户管理" → "新增客户"，填写名称和至少一种联系方式
2. **查看工艺模板** — 点击"工艺流程"，已有"标准热流道流程"模板（8 个步骤）
3. **创建订单** — 点击"订单管理" → "新增订单"，填写订单号、产品名，选择工艺模板
4. **推进工序** — 打开订单详情，点击"开始"按钮推进步骤
5. **上传图纸** — 点击"图纸管理" → 上传一张图片文件
6. **预留库存** — 点击"库存管理" → 选择物料 → 预留到订单

## 接下来

- [创建工艺流程](howto-setup-workflow.md) — 自定义你的工艺模板
- [管理用户和权限](howto-manage-users.md) — 添加新员工并分配权限
- [API 参考](reference-api.md) — 完整的接口文档
- [系统架构](explanation-architecture.md) — 了解技术选型和数据流

## 故障排除

| 问题 | 解决 |
|------|------|
| 端口 3000 被占用 | 修改 `server/.env` 中的 `PORT`，并同步更新 `client/vite.config.js` 中的 proxy 目标 |
| `npm install` 报错 | 确认 Node.js 版本 >= 18，尝试 `rm -rf node_modules package-lock.json && npm install` |
| 登录后白屏 | 打开浏览器控制台检查 401 错误，确认 JWT_SECRET 配置正确 |
| 数据库损坏 | 运行 `npm run db:reset` 重建数据库（会丢失数据） |
