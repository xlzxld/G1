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
