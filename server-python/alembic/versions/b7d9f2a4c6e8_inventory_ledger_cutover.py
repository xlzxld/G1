"""inventory_ledger_cutover — V3 库存域切换（本批风险最高工件，全部 DDL+数据在一个事务内）

Revision ID: b7d9f2a4c6e8
Revises: dd688f5c7744
Create Date: 2026-09-06

存量库执行路径（迁移窗口必须写冻结——停机或只读维护页）：
    1. pg_dump 全库备份
    2. alembic stamp dd688f5c7744     # 存量 V2.5 库登记基线（若从未跑过 Alembic）
    3. alembic upgrade head            # 执行本迁移
    4. 重启应用
已用新版 seed.py（create_all）建过 V3 表的开发库：`alembic stamp b7d9f2a4c6e8` 跳过 DDL。

本迁移内容：
A. 结构：users.token_version / orders.product_type / inventory_items.{category,location,is_archived}
   / alert_threshold→min_stock 改名 / 新表 stock_movements, boms, bom_items, purchase_orders
   / inventory_reservations (order_id,item_id) 唯一约束
B. 数据：
   - inventory_reservations 重复行合并（求和保留最小 id）后加唯一约束
   - 每个物料回填一条 OPENING 期初流水（quantity = 当前 total）
   - reserved 孤儿值重算：reserved = SUM(有效预留)（8/6 报告：删单不释放遗留的虚增）
   - notification_rules 的 condition_field 与模板占位符 alert_threshold → min_stock
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d9f2a4c6e8'
down_revision: Union[str, Sequence[str], None] = 'dd688f5c7744'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = sa.text('now()')


def upgrade() -> None:
    # ---- A1. users.token_version（JWT 无状态吊销） ----
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=True))

    # ---- A2. orders.product_type（BOM 受控枚举匹配键） ----
    op.add_column('orders', sa.Column('product_type', sa.String(), nullable=True))
    op.create_index(op.f('ix_orders_product_type'), 'orders', ['product_type'], unique=False)

    # ---- A3. inventory_items 主数据列 + 改名（改名在加列之后，统一一个窗口） ----
    op.add_column('inventory_items', sa.Column('category', sa.String(), nullable=True, server_default=''))
    op.add_column('inventory_items', sa.Column('location', sa.String(), nullable=True, server_default=''))
    op.add_column('inventory_items', sa.Column('is_archived', sa.Integer(), nullable=True, server_default='0'))
    op.alter_column('inventory_items', 'alert_threshold', new_column_name='min_stock', existing_type=sa.Integer())

    # ---- A4. 新表 ----
    op.create_table(
        'stock_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('inventory_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('batch_no', sa.String(), nullable=True),
        sa.Column('unit_cost', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('operator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stock_movements_id'), 'stock_movements', ['id'], unique=False)
    op.create_index(op.f('ix_stock_movements_item_id'), 'stock_movements', ['item_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_type'), 'stock_movements', ['type'], unique=False)
    op.create_index(op.f('ix_stock_movements_source_type'), 'stock_movements', ['source_type'], unique=False)
    op.create_index(op.f('ix_stock_movements_source_id'), 'stock_movements', ['source_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_created_at'), 'stock_movements', ['created_at'], unique=False)

    op.create_table(
        'boms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('product_type', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_boms_id'), 'boms', ['id'], unique=False)
    op.create_index(op.f('ix_boms_product_type'), 'boms', ['product_type'], unique=False)

    op.create_table(
        'bom_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bom_id', sa.Integer(), sa.ForeignKey('boms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity_per_set', sa.Integer(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bom_items_id'), 'bom_items', ['id'], unique=False)
    op.create_index(op.f('ix_bom_items_bom_id'), 'bom_items', ['bom_id'], unique=False)

    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('po_no', sa.String(), nullable=False),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('received_quantity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('expected_date', sa.DateTime(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('received_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('po_no'),
    )
    op.create_index(op.f('ix_purchase_orders_id'), 'purchase_orders', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_po_no'), 'purchase_orders', ['po_no'], unique=True)
    op.create_index(op.f('ix_purchase_orders_item_id'), 'purchase_orders', ['item_id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_status'), 'purchase_orders', ['status'], unique=False)
    op.create_index(op.f('ix_purchase_orders_created_at'), 'purchase_orders', ['created_at'], unique=False)

    # ---- B1. 预留去重：同 (order_id, item_id) 合并数量到最小 id 行 ----
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE inventory_reservations r
        SET quantity = agg.total
        FROM (
            SELECT order_id, item_id, MIN(id) AS keep_id, SUM(quantity) AS total
            FROM inventory_reservations
            GROUP BY order_id, item_id
            HAVING COUNT(*) > 1
        ) agg
        WHERE r.id = agg.keep_id
    """))
    conn.execute(sa.text("""
        DELETE FROM inventory_reservations r
        USING (
            SELECT order_id, item_id, MIN(id) AS keep_id
            FROM inventory_reservations
            GROUP BY order_id, item_id
            HAVING COUNT(*) > 1
        ) agg
        WHERE r.order_id = agg.order_id
          AND r.item_id = agg.item_id
          AND r.id <> agg.keep_id
    """))

    # ---- A5. 预留唯一约束（去重之后才可能建成功） ----
    op.create_unique_constraint('uq_reservation_order_item', 'inventory_reservations', ['order_id', 'item_id'])

    # ---- B2. OPENING 期初回填：每个物料一条，quantity = 当前 total ----
    conn.execute(sa.text("""
        INSERT INTO stock_movements
            (item_id, type, source_type, quantity, balance_after, note, created_at)
        SELECT id, 'OPENING', 'manual', COALESCE(total, 0), COALESCE(total, 0),
               'cutover 期初回填', now()
        FROM inventory_items
    """))

    # ---- B3. reserved 孤儿重算：reserved = SUM(有效预留)，无预留清零 ----
    conn.execute(sa.text("""
        UPDATE inventory_items i
        SET reserved = agg.total
        FROM (
            SELECT item_id, SUM(quantity) AS total
            FROM inventory_reservations
            GROUP BY item_id
        ) agg
        WHERE i.id = agg.item_id
    """))
    conn.execute(sa.text("""
        UPDATE inventory_items i
        SET reserved = 0
        WHERE i.reserved <> 0
          AND NOT EXISTS (SELECT 1 FROM inventory_reservations r WHERE r.item_id = i.id)
    """))

    # ---- B4. 通知规则键修复：alert_threshold → min_stock（静默失配防护） ----
    conn.execute(sa.text(
        "UPDATE notification_rules SET condition_field = 'min_stock' WHERE condition_field = 'alert_threshold'"
    ))
    conn.execute(sa.text(
        "UPDATE notification_rules SET body_template = REPLACE(body_template, '{alert_threshold}', '{min_stock}') "
        "WHERE body_template LIKE '%{alert_threshold}%'"
    ))
    conn.execute(sa.text(
        "UPDATE notification_rules SET title_template = REPLACE(title_template, '{alert_threshold}', '{min_stock}') "
        "WHERE title_template LIKE '%{alert_threshold}%'"
    ))


def downgrade() -> None:
    # 逆向：仅回滚结构；OPENING 流水随表删除。存量业务数据恢复走 pg_dump。
    op.drop_constraint('uq_reservation_order_item', 'inventory_reservations', type_='unique')

    op.drop_index(op.f('ix_purchase_orders_created_at'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_status'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_item_id'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_po_no'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_id'), table_name='purchase_orders')
    op.drop_table('purchase_orders')

    op.drop_index(op.f('ix_bom_items_bom_id'), table_name='bom_items')
    op.drop_index(op.f('ix_bom_items_id'), table_name='bom_items')
    op.drop_table('bom_items')

    op.drop_index(op.f('ix_boms_product_type'), table_name='boms')
    op.drop_index(op.f('ix_boms_id'), table_name='boms')
    op.drop_table('boms')

    op.drop_index(op.f('ix_stock_movements_created_at'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_source_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_source_type'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_type'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_item_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_id'), table_name='stock_movements')
    op.drop_table('stock_movements')

    op.alter_column('inventory_items', 'min_stock', new_column_name='alert_threshold', existing_type=sa.Integer())
    op.drop_column('inventory_items', 'is_archived')
    op.drop_column('inventory_items', 'location')
    op.drop_column('inventory_items', 'category')

    op.drop_index(op.f('ix_orders_product_type'), table_name='orders')
    op.drop_column('orders', 'product_type')

    op.drop_column('users', 'token_version')
