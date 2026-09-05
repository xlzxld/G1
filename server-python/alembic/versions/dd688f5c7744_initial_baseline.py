"""initial_baseline — 完整建表基线（V2.5 全量 schema）

Revision ID: dd688f5c7744
Revises:
Create Date: 2026-09-06（重写；原版本仅建索引，无法用于全新数据库——8/6 审查报告 P1）

策略（stamp-then-cutover）：
- 全新数据库：`alembic upgrade head` 从本基线开始完整建表；
- 存量数据库（由 seed.py 的 create_all 建表、从未跑过 Alembic）：
  先 `alembic stamp dd688f5c7744`（登记版本，不执行任何 DDL），
  再 `alembic upgrade head` 执行其后的 cutover 迁移。
- 本基线的 DDL 与 `Base.metadata.create_all` 输出逐列一致（含 ix_*_id），
  由 tests/test_migrations.py 的新库一致性断言守护。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd688f5c7744'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = sa.text('now()')


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'page_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('page_key', sa.String(), nullable=True),
        sa.Column('can_view', sa.Integer(), nullable=True),
        sa.Column('can_edit', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_page_permissions_id'), 'page_permissions', ['id'], unique=False)

    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('wechat', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('contact_methods', sa.JSON(), nullable=True),
        sa.Column('contacts', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('customer_name', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('current_step_id', sa.Integer(), nullable=True),
        sa.Column('shipment_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('inventory_deducted', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_no'), 'orders', ['order_no'], unique=True)
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_priority'), 'orders', ['priority'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_created_at'), 'orders', ['created_at'], unique=False)

    op.create_table(
        'process_flows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_template', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_process_flows_id'), 'process_flows', ['id'], unique=False)
    op.create_index(op.f('ix_process_flows_order_id'), 'process_flows', ['order_id'], unique=False)
    op.create_index(op.f('ix_process_flows_created_at'), 'process_flows', ['created_at'], unique=False)

    op.create_table(
        'process_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=True),
        sa.Column('required', sa.Integer(), nullable=True),
        sa.Column('outsourced', sa.Integer(), nullable=True),
        sa.Column('vendor_id', sa.Integer(), nullable=True),
        sa.Column('sent_date', sa.DateTime(), nullable=True),
        sa.Column('return_date', sa.DateTime(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('assignee', sa.String(), nullable=True),
        sa.Column('completion_condition', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['flow_id'], ['process_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['completed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_process_steps_id'), 'process_steps', ['id'], unique=False)
    op.create_index(op.f('ix_process_steps_flow_id'), 'process_steps', ['flow_id'], unique=False)
    op.create_index(op.f('ix_process_steps_status'), 'process_steps', ['status'], unique=False)

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['process_steps.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_order_id'), 'documents', ['order_id'], unique=False)
    op.create_index(op.f('ix_documents_step_id'), 'documents', ['step_id'], unique=False)
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'], unique=False)

    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('spec', sa.String(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('reserved', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('alert_threshold', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_inventory_items_id'), 'inventory_items', ['id'], unique=False)

    op.create_table(
        'inventory_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_inventory_reservations_id'), 'inventory_reservations', ['id'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=True),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('body', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('link', sa.String(), nullable=True),
        sa.Column('is_read', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)

    op.create_table(
        'notification_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('event', sa.String(), nullable=False),
        sa.Column('condition_field', sa.String(), nullable=True),
        sa.Column('condition_op', sa.String(), nullable=True),
        sa.Column('condition_value', sa.String(), nullable=True),
        sa.Column('notify_role', sa.String(), nullable=True),
        sa.Column('title_template', sa.String(), nullable=False),
        sa.Column('body_template', sa.String(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notification_rules_id'), 'notification_rules', ['id'], unique=False)

    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('contact_methods', sa.JSON(), nullable=True),
        sa.Column('contacts', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_vendors_id'), 'vendors', ['id'], unique=False)

    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.UniqueConstraint('key'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_system_settings_id'), 'system_settings', ['id'], unique=False)

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('detail', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=NOW, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)


def downgrade() -> None:
    # 基线 downgrade = 全部 drop（仅供全新库回滚演练；存量库走 pg_dump 恢复）
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_system_settings_id'), table_name='system_settings')
    op.drop_table('system_settings')
    op.drop_index(op.f('ix_vendors_id'), table_name='vendors')
    op.drop_table('vendors')
    op.drop_index(op.f('ix_notification_rules_id'), table_name='notification_rules')
    op.drop_table('notification_rules')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_inventory_reservations_id'), table_name='inventory_reservations')
    op.drop_table('inventory_reservations')
    op.drop_index(op.f('ix_inventory_items_id'), table_name='inventory_items')
    op.drop_table('inventory_items')
    op.drop_index(op.f('ix_documents_created_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_step_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_order_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_process_steps_status'), table_name='process_steps')
    op.drop_index(op.f('ix_process_steps_flow_id'), table_name='process_steps')
    op.drop_index(op.f('ix_process_steps_id'), table_name='process_steps')
    op.drop_table('process_steps')
    op.drop_index(op.f('ix_process_flows_created_at'), table_name='process_flows')
    op.drop_index(op.f('ix_process_flows_order_id'), table_name='process_flows')
    op.drop_index(op.f('ix_process_flows_id'), table_name='process_flows')
    op.drop_table('process_flows')
    op.drop_index(op.f('ix_orders_created_at'), table_name='orders')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_priority'), table_name='orders')
    op.drop_index(op.f('ix_orders_customer_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_no'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    op.drop_table('customers')
    op.drop_index(op.f('ix_page_permissions_id'), table_name='page_permissions')
    op.drop_table('page_permissions')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
