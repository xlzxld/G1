# 热流道生产管理系统 — 设计文档 (v4 Final)

**日期:** 2026-06-21
**模式:** 内部项目
**采用方案:** B — 分层架构
**状态:** 全部 6 个子任务完成，QA 通过 (92/100)

---

## 技术架构

- **前端:** Vue3 + Element Plus + Vite + Pinia + Vue Router
- **后端:** Node.js + Express (路由→服务→数据三层分离)
- **数据库:** SQLite + Knex 迁移
- **认证:** JWT (access 15min + refresh 7d) + bcrypt
- **文件存储:** 本地 uploads/{订单号}/{分类}/ 目录

## 数据库表 (14 张)

| 表 | 用途 |
|------|------|
| `users` | 用户，含 is_admin/is_active，密码 bcrypt 哈希 |
| `page_permissions` | 用户×页面权限矩阵 (can_view, can_edit) |
| `customers` | 客户，联系方式为 JSON 数组 contact_methods |
| `orders` | 订单，status 由工序引擎自动驱动 |
| `process_flows` | 工艺模板+订单实例 (is_template 区分) |
| `process_steps` | 工序步骤，支持并行/依赖/必做/外协 |
| `documents` | 图纸文件，版本管理，标题描述可编辑 |
| `inventory_items` | 库存物料，总量+已预留+预警阈值 |
| `inventory_reservations` | 库存预留记录 |
| `notifications` | 通知 (手动派发+自动规则) |
| `notification_rules` | 自动通知规则 |
| `vendors` | 外协厂商 |
| `system_settings` | 系统参数 key-value |
| `audit_logs` | 操作日志 (表存在，中间件待集成) |

## 权限模型 (最终版)

- **管理员豁免:** is_admin=1 的用户绕过所有权限检查（前端路由守卫+后端中间件）
- **页面权限矩阵:** 用户 × 页面 = {不可见, 只读, 可编辑}
- **管理员防护:** 配置自己权限时"用户管理"页面的开关锁定，防止锁死
- **双重保护:** 前端路由守卫 + 后端 requirePermission 中间件（API 层）

## 工序引擎

- 支持线性流转、退回上一步、跳过非必做步骤、并行步骤
- 退回时自动处理并行组（回退到并行组之前）
- 工艺模板复制到订单时生成独立步骤实例
- 步骤完成自动更新订单 status 和 current_step_id

## 订单状态

draft → {工序名}进行中 → ... → completed / paused / aborted (客户取消)

## 10 个业务模块

| 模块 | 前端页面 | 后端路由 |
|------|---------|---------|
| 仪表台 | Dashboard.vue — 6 张可点击汇总卡片 | dashboard.js |
| 客户管理 | Customers.vue + CustomerDetail.vue — 动态联系方式 | customers.js |
| 订单管理 | Orders.vue + OrderDetail.vue — 工序时间线 | orders.js |
| 工艺流程 | ProcessFlow.vue — 步骤拖拽编辑 | process-flows.js |
| 图纸管理 | Drawings.vue + DrawingDetail.vue — 图片预览+元数据 | documents.js |
| 库存管理 | Inventory.vue — 预留关联订单 | inventory.js |
| 用户管理 | Users.vue — 权限矩阵配置 | users.js |
| 通知中心 | Notifications.vue — 手动派发 | notifications.js |
| 系统设置 | Settings.vue — 参数/密码/通知规则/日志 | settings.js |
| 外协管理 | Outsourcing.vue | vendors.js |

## 最新变更 (v3→v4)

### 客户联系方式
- 从固定字段 (contact/phone/wechat/email) 改为 JSON 数组 contact_methods
- 支持自定义类型：电话、微信、QQ、邮箱、联系人、传真 → 可无限添加
- 创建时至少需要一种联系方式

### 图纸管理增强
- 上传限制为图片格式 (png/jpg/gif/webp/bmp/svg)，Multer fileFilter 校验
- 列表页缩略图内联预览 (el-image)
- 详情页：上半部大图显示 + 下半部可编辑标题和描述数据
- 上传新版本自动将同分类旧版本标为"作废"(保留不删除)

### 权限 Bug 修复
- 管理员给自己配权限时"用户管理"开关锁定
- 前端路由守卫添加 isAdmin 豁免 (与后端一致)
- 权限拒绝时智能跳转到第一个可访问页面（而非死循环 /）

### 工序引擎修复
- rollbackStep 回退时正确处理并行组
- order 删除时先置空 current_step_id 再级联删除

## 核心交互规范

- 所有列表页: 搜索栏 + 列头排序 + 点击行跳转详情
- 所有关联数据可点击跳转 (客户名→客户详情, 库存→关联订单)
- 图纸下载: 自定义路由处理中文文件名 URL 编码
- 操作日志: 审计表已建，中间件待集成

## 演示数据

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| laowang | 123456 | 车间工人 |
| xiaoli | 123456 | 设计师 |

3 张订单、2 个客户、5 种物料、3 家外协厂商、8 步标准热流道流程

## 运行

```bash
cd server && npm start      # http://localhost:3000
cd client && npm run dev    # http://localhost:5173
```

## 未解决项 (V1.1)

- 操作日志中间件 (audit.js 已写但未集成)
- 自动通知规则引擎的定时检查
- 请求频率限制
- 部署方案 (SSL/PM2/nginx)
- node_modules 历史提交清理
