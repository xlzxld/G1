# TODOS

> 由 `/plan-ceo-review`（2026-09-06）评审产生。每项格式：What / Why / Effort / Priority / Depends。
> 配套计划：`docs/designs/inventory-ledger-and-cockpit.md`（CEO 计划，已含本批全部范围）。

## T1 车间移动端工位模式（领料/退料/报工大按钮页面）

- **What**：为车间平板提供领料/退料/工序报工的大按钮专用页面（局域网访问，物料选择器代替扫码，避免硬件依赖）。
- **Why**：10x 愿景"车间单一事实来源"的最后一块。桌面页面不适合工位操作；领料录入的及时性直接决定流水账本的可信度。
- **Effort**: M（人工 4-6 天 / CC 约 1-2 小时）　**Priority**: P1　**Depends on**: 库存服务层与流水模型上线（本批 CEO 计划）。
- **Context**：CEO 评审 D8 用户主动缓办。建议上线后先观察 D18 SOP（工序推进即录）两周的漏录率（看驾驶舱"已完成未领料"风险项堆积速度），漏录率高则提前启动本项。

## T2 SSE 多 worker 推送可靠性修复

- **What**：修复 `ConnectionManager` 进程内对象导致的多 worker 通知丢失（跨 worker 投递或改单 worker + 队列）；SSE URL query token 改一次性短 token。
- **Why**：生产 `--workers 2` 下通知只推送到连到同一 worker 的连接，实时刷新不可靠；8/6 报告 P1-6。
- **Effort**: S-M（人工 2-3 天 / CC 约 30-60 分钟）　**Priority**: P2　**Depends on**: 无。
- **Context**：驾驶舱已用 60s 轮询 `/dashboard/stats` 兜底，此项是体验升级不是阻塞项。

## T3 8/6 报告 P1/P2 存量债清偿

- **What**：工艺模板编辑丢字段（数据完整性 #4）、依赖版本锁定 + 补 python-dotenv + pool_pre_ping、Caddy HTTPS、CI 接入与存量代码测试（本批只覆盖新域）。
- **Why**：与本次批次互补的存量债。本批已清掉全部 P0 与数据完整性 #1/#2/#6/#7，剩余按报告节奏走。
- **Effort**: L（分批）　**Priority**: P2　**Depends on**: 本批上线后按 8/6 报告第二批/第三批顺序。
- **Context**：详见 `项目全面审查报告-2026-08-06.md` 第四~六节。

## T4 订单数量字段 + BOM 版本快照（autoplan 第二轮缓办，2026-09-07）

- **What**: Order 增加 quantity（套数）字段；BOM apply 按套数乘算预留；模板编辑时版本号递增并在订单上快照当时用料行。
- **Why**: 当前 apply 固定预留 1 套——100 套的订单只预留 1 套用料；模板改版后"该订单当时用了哪版模板"不可追溯。
- **Effort**: L（人工 3-5 天 / CC 1-2 小时）　**Priority**: P1　**Depends**: 需要 schema 迁移 + 建单弹窗改动。

## T5 全局流水查询 + 导出（autoplan 第二轮缓办）

- **What**: 新增 `/inventory/movements` 全局端点（类型/日期/批次/来源筛选+分页）与导出；Excel 导出支持当前筛选条件。
- **Why**: 目前只能按物料查最近 50 条流水；"昨天全部出库""哪个订单消耗了批次 X"无法回答。
- **Effort**: M（人工 2-3 天 / CC 1 小时）　**Priority**: P2　**Depends**: 无。

## T6 其余缓办项（autoplan 第二轮）

- 多选补货意向批量生成采购单（当前逐项，10 项缺料约 30 次点击）
- 物料名称唯一索引（需先去重存量 + 迁移；当前仅导入/创建时校验）
- SSE one-time ticket 鉴权（token 在 URL query 中会进代理日志；沿用 T2 依赖）
- BOM apply 单事务化（当前逐项 commit + 全量 catch 警告清单，部分成功语义已可用）

## T7 外协全生命周期（autoplan R3 缓办首项，2026-09-07）

- **What**: 订单工序"发外协/收回"动作（写 sent_date/return_date/vendor_id/cost，当前全库零写入）；外协页加"在外协件"列表（厂商→工序→发出天数）与成本汇总。
- **Why**: 老板最痛的"外协件在外面压了多久、花了多少钱"系统完全失明；外协页现状只是厂商通讯录。
- **Effort**: L（人工 4-6 天 / CC 1-2 小时）　**Priority**: P1（建议下一个大项）　**Depends**: 无（字段已就位）。

## T8 R3 其余缓办项

- 图纸按图纸本身（title）版本化：现按"订单+分类"递增，同类第二张图纸会把第一张挤成历史版；工序照片应独立命名空间（P1）
- 订单 cancelled 状态 + 建单后重选模板（录错流程只能整单删，有流水还删不掉）（P2）
- 逾期/临期定时通知扫描（驾驶舱已算出但只展示不推送；需调度器）（P2）
- 文档版本唯一索引 (order_id,category,version) + 上传先落库后写盘 + step_id 归属校验（P2）
- SSE put_nowait 线程安全（call_soon_threadsafe）与一次性 ticket（并入 T2 SSE 专项）（P2）
- 图纸库独立页面（drawings 权限行当前无落地页面）+ PDF 内嵌预览 + 审计日志过滤分页前端（P3）
