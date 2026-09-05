# 运维手册：上线烟雾检查 + 迁移与回滚 Runbook

> 生成：2026-09-06 CEO 计划（docs/designs/inventory-ledger-and-cockpit.md）可观测性四件套之一。
> 适用版本：V3 库存流水账本批次。

## 一、上线前迁移步骤（存量 V2.5 库）

```bash
# 0. 全库备份（必须）
docker compose -f docker-compose.prod.yml exec db pg_dump -U <user> <db> > backup_$(date +%Y%m%d_%H%M).sql

# 1. 停写（停机窗口或只读维护页）；迁移预计分钟级

# 2. 登记基线并执行 cutover（存量库从未跑过 Alembic 时）
docker compose -f docker-compose.prod.yml exec backend alembic stamp dd688f5c7744
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 3. 首次部署还需：设置 SECRET_KEY/CORS_ORIGINS 环境变量（无默认值，缺失即启动失败）

# 4. 重启应用（prod compose 已配置启动即 alembic upgrade head，幂等）
docker compose -f docker-compose.prod.yml up -d

# 5. （可选）重建演示数据：docker compose exec backend python seed_mock.py
```

迁移内容回顾（b7d9f2a4c6e8）：users.token_version、orders.product_type、
inventory_items.{category,location,min_stock,is_archived}、新表 stock_movements/boms/bom_items/purchase_orders、
预留 (order_id,item_id) 去重+唯一约束、OPENING 期初回填、reserved 孤儿重算、通知规则键 alert_threshold→min_stock。

## 二、回滚路径

- **迁移窗口内（尚无新交易）**：应用回退上一镜像 → `alembic downgrade`（或直接用 pg_dump 恢复）→ 恢复备份。
- **cutover 之后**：不承诺无损回滚——恢复 pg_dump 会丢失迁移后的全部交易。此时应改用：
  - 数据级修复：`python scripts/recompute_inventory.py --apply`（缓存列漂移）；
  - 或接受丢失窗口后按上述流程回滚。
- 全新空库：`alembic upgrade head` 直接建到最新（基线+cutover 幂等）。

## 三、上线后 5 分钟烟雾检查清单

| # | 检查项 | 命令/操作 | 通过标准 |
|---|---|---|---|
| 1 | 应用存活 | `curl http://<host>/api/healthz` | `{"ok":true}` |
| 2 | 登录 | admin 登录 | 拿到 token，旧 token 401（类型/版本校验）属预期 |
| 3 | 驾驶舱 | 打开首页 | 指标带+风险清单渲染；无红色报错条 |
| 4 | 库存列表 | 打开库存管理 | 列表出现"可用/安全库存"列；无 500 |
| 5 | 建流水 | 任选物料入库 1 件 | toast 显示可用量；流水弹窗出现新记录 |
| 6 | 预警穿越 | 领料使可用跌破安全库存 | 库存预警计数 +1，且只触发一次通知 |
| 7 | 匿名拦截 | `curl http://<host>/api/customers`（不带 token） | 401（不能返回数据） |
| 8 | 图纸鉴权 | 打开订单图纸 | 图片经鉴权加载正常；直接访问 /uploads/... 应 404/401 |
| 9 | 采购闭环 | 补货意向→建单→下单→到货 | 状态机流转，库存流水出现 INBOUND(source=purchase) |
| 10 | 账本一致性 | `python scripts/recompute_inventory.py` | "所有缓存列与流水/预留一致 ✓" |

## 四、日常运维

- **缓存列漂移修复**：`docker compose exec backend python scripts/recompute_inventory.py --apply`（先 dry-run 看报告）。
- **测试**：`docker compose -f docker-compose.dev.yml exec backend python -m pytest tests/ -v`（需容器内 `pip install -r requirements-dev.txt`；如代码更新，先重装）。
- **依赖安装**：镜像重建会自动装 requirements.txt；requirements-dev.txt 仅测试需要。
- **领料 SOP**（上线验收标准 D18）：领料在工序推进时由点完成的人录入，遗漏由驾驶舱"已完成未领料"风险项兜底——上线两周内每日关注该清单。
