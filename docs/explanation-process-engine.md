 # 工序引擎

 ## 这是什么

 工序引擎是系统的核心业务逻辑，负责驱动订单在工艺流程中按步骤推进。它解决了"订单现在该谁做？下一步是什么？能不能跳过？出错了怎么退回？"这些车间管理的日常问题。

 ## 步骤生命周期

 每个工序步骤有 4 种状态:

 ```
 pending ──→ in_progress ──→ completed
   │                             ↑ (可回退)
   └─────────→ skipped ─────────┘
 ```

- **pending:** 等待开始。步骤刚创建或被回退后的状态。
- **in_progress:** 正在进行（实际通过 advance 直接标记为 completed，in_progress 是中间状态）。
- **completed:** 已完成。
- **skipped:** 已跳过（仅非必做步骤 `required=0` 可跳过）。

## 步骤流转规则

### 推进 (advanceStep)

调用 `POST /api/orders/:id/steps/:stepId/advance` 触发。引擎执行以下操作:

1. 将当前步骤状态设为 `completed`，记录完成时间和完成人
2. 调用 `getNextSteps` 计算下一步
3. 更新订单的 `status` 和 `current_step_id`

**下一步计算逻辑 (`getNextSteps`):**

```
1. 获取所有步骤，按 seq 排序
2. 筛选 pending 状态的步骤
3. 再筛选: 依赖已满足的 (depends_on_step_id 指向已完成步骤，或无依赖)
4. 如果当前没有正在进行的步骤 (in_progress):
   → 所有 can_parallel=1 的 ready 步骤都变为下一步 (并行)
5. 如果有正在进行的步骤:
   → 只有 can_parallel=1 的步骤可以和它并行
6. 如果所有步骤都完成了:
   → 订单状态变为 completed
```

### 回退 (rollbackStep)

只能回退 `completed` 或 `skipped` 状态的步骤。引擎:

1. 将步骤重置为 `pending` (清除完成信息)
2. 确定回退目标:
   - 如果被回退步骤是**并行步骤** (`can_parallel=1`)，回退到并行组开始之前
   - 否则回退到 `seq - 1` 的步骤
3. 更新订单状态为 `{前一步骤名}进行中` 或 `draft`

**并行回退场景:** 假设步骤 2 和 3 都是并行步骤 (`can_parallel=1`)，步骤 4 是非并行的。当回退步骤 4 时:
- 引擎找到步骤 4 之前的最后一个非并行步骤（步骤 1）
- 回退到步骤 1
- 避免回到并行组中间导致状态混乱

### 跳过 (skipStep)

只能跳过非必做步骤 (`required=0`)。引擎标记步骤为 `skipped`，然后调用 `getNextSteps` 计算下一个步骤。

## 工艺模板到订单

创建订单时如果指定了 `template_flow_id`，引擎执行 `copyFlowToOrder`:

1. 查找模板 (is_template=1)
2. 创建新的流程实例 (is_template=0, order_id=订单ID)
3. 逐步骤复制: 每个模板步骤创建一个新步骤实例 (status=pending)
4. 映射 `depends_on_step_id`: 原步骤依赖的旧 ID 替换为新 ID
5. 将第一个步骤设为当前步骤，订单状态更新为 `{第一步名}进行中`

流程实例是**独立的**——修改模板不会影响已有订单的流程实例。

## 订单删除

删除订单时，先删除关联的流程实例 (process_flows where order_id=...) —— 这会级联删除 process_steps (ON DELETE CASCADE)。然后再删除订单本身。

## 状态值命名

订单状态采用中文动态命名:

- `draft` — 草稿（无流程或尚未开始）
- `{步骤名}进行中` — 如 "设计进行中"、"加工进行中"
- `completed` — 所有步骤完成
- `paused` — 暂停（管理员手动设置）
- `aborted` — 客户取消（管理员手动设置）

`current_step_id` 总是指向当前正在进行的步骤（可能有多个，但只存一个 ID）。

## 相关文档

- [API 参考](reference-api.md) — orders 路由，advance/rollback/skip 接口
- [创建工艺流程](howto-setup-workflow.md) — 如何定义步骤依赖和并行规则
- [数据库表结构](reference-database.md) — process_flows、process_steps、orders 表
