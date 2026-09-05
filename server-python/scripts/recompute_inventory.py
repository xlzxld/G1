"""缓存列一致性重算工具（可观测性四件套之一，D15）。

用途：当 total/reserved 缓存列与流水/预留汇总出现漂移（bug、手工改库）时，
一键重算并打印每笔差额。默认 dry-run 只报告；--apply 执行修复。

运行（后端容器内）：
    python scripts/recompute_inventory.py            # 只报告漂移
    python scripts/recompute_inventory.py --apply    # 以流水为准修复
"""
import sys
import argparse

sys.path.insert(0, ".")

from sqlalchemy import func
from database import SessionLocal
import models
from services.inventory_service import verify_ledger_consistency


def main() -> int:
    parser = argparse.ArgumentParser(description="库存缓存列一致性重算")
    parser.add_argument("--apply", action="store_true", help="执行修复（默认仅报告）")
    args = parser.parse_args()

    db = SessionLocal()
    drifted = 0
    try:
        items = db.query(models.InventoryItem).all()
        for item in items:
            r = verify_ledger_consistency(db, item.id)
            if r["drift"]:
                drifted += 1
                print(f"[DRIFT] 物料 #{item.id} {item.name}: 缓存 total={r['cache_total']} 流水合计={r['ledger_sum']} 差额={r['drift']}")
                if args.apply:
                    item.total = r["ledger_sum"]
                    print(f"        -> 已按流水修正 total={r['ledger_sum']}")

        # reserved 一致性：reserved = SUM(预留)
        sums = dict(
            db.query(models.InventoryReservation.item_id, func.sum(models.InventoryReservation.quantity))
            .group_by(models.InventoryReservation.item_id)
            .all()
        )
        for item in items:
            expect = int(sums.get(item.id, 0))
            if (item.reserved or 0) != expect:
                drifted += 1
                print(f"[DRIFT] 物料 #{item.id} {item.name}: 缓存 reserved={item.reserved} 预留合计={expect}")
                if args.apply:
                    item.reserved = expect

        if args.apply and drifted:
            db.commit()
            print(f"完成：共 {drifted} 处漂移已修复。")
        elif drifted:
            print(f"发现 {drifted} 处漂移（dry-run 未修改）。执行 --apply 修复。")
        else:
            print("所有缓存列与流水/预留一致 ✓")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
