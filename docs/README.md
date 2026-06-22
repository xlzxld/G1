 # 热流道生产管理系统 — 文档

 ## 文档导航

 ### 教程 (Tutorial)
- [快速上手](tutorial-getting-started.md) — 从零开始运行系统，十分钟看到结果

 ### 操作指南 (How-to)
- [创建工艺流程](howto-setup-workflow.md) — 新建工艺模板，配置步骤和依赖
- [管理用户和权限](howto-manage-users.md) — 创建用户、分配页面权限

 ### 参考 (Reference)
- [API 参考](reference-api.md) — 所有接口的路径、参数和返回值
- [数据库表结构](reference-database.md) — 14 张表的字段定义和约束
- [配置文件](reference-configuration.md) — 环境变量、Knex、Vite 配置

 ### 解释 (Explanation)
- [系统架构](explanation-architecture.md) — 分层设计、技术选型和数据流
- [权限模型](explanation-permission-model.md) — 管理员豁免、页面权限矩阵、双重保护
- [工序引擎](explanation-process-engine.md) — 状态机、并行步骤、回退和跳过逻辑

 ## 项目概览

 热流道生产管理系统是一套面向热流道制造车间的 MES（生产执行系统），覆盖从客户管理、订单录入、工序流转、图纸版本管理到库存跟踪和外协管理的完整生产链路。

 **技术栈:** Vue 3 + Element Plus (前端) | Express + better-sqlite3 (后端) | Knex 迁移 | JWT 认证

 **账号:** admin / admin123 (管理员) | laowang / 123456 (车间工人) | xiaoli / 123456 (设计师)

 ## 参考文件

- [CLAUDE.md](../CLAUDE.md) — AI 编码助手的项目上下文
- [DESIGN.md](../DESIGN.md) — 设计决策和开发日志
