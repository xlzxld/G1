# 热流道生产管理系统 — 文档

## 文档导航

### 教程 (Tutorial)
- [快速上手](tutorial-getting-started.md) — 基于 Docker Compose 运行系统，十分钟看到结果

### 操作指南 (How-to)
- [创建工艺流程](howto-setup-workflow.md) — 新建工艺模板，配置工序步骤与拍照完成条件
- [管理用户和权限](howto-manage-users.md) — 创建用户账号、分配页面访问与编辑权限

### 参考 (Reference)
- [API 参考](reference-api.md) — FastAPI 交互式接口文档 (Swagger UI) 访问与路由组说明
- [数据库表结构](reference-database.md) — PostgreSQL 12 张核心业务表的字段定义与约束
- [配置文件](reference-configuration.md) — Docker Compose 环境变量、FastAPI 挂载及 Vite 代理配置

### 解释 (Explanation)
- [系统架构](explanation-architecture.md) — FastAPI + PostgreSQL + Vue 3 架构设计与局域网接入共享设计
- [权限模型](explanation-permission-model.md) — 页面权限可见/只读/编辑设计、管理员豁免及前端路由守卫
- [工序引擎](explanation-process-engine.md) — 线性工序推进状态机、工序拍照落盘关联及库存自动扣减/回退规则

## 项目概览

热流道生产管理系统是一套面向热流道制造车间的 MES（生产执行系统），覆盖从客户管理、订单录入、工序流转、图纸版本管理到库存跟踪和外协管理的完整生产链路。

**技术栈:** Vue 3 + Element Plus (前端) | FastAPI + PostgreSQL (后端) | SQLAlchemy ORM | Docker Compose 容器化部署

**系统内置演示账号:**
* **系统管理员 (admin):** 用户名 `admin`，密码 `123`
* **车间操作工 (laowang):** 用户名 `laowang`，密码 `123`
* **工程设计师 (xiaoli):** 用户名 `xiaoli`，密码 `123`

## 参考文件

- [CLAUDE.md](../CLAUDE.md) — AI 编码助手的项目开发与指令上下文
- [V2.3更新总结.md](../V2.3更新总结.md) — 系统 V2.3 版本重构与体验优化总结
