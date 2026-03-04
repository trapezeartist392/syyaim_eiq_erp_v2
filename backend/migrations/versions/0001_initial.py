"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def create_enum_safe(name, values):
    """Create a PostgreSQL ENUM type, silently skipping if it already exists."""
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({vals});
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

def upgrade() -> None:
    create_enum_safe('userrole', ['super_admin','admin','manager','accountant','hr_manager','purchase_manager','sales_manager','warehouse_manager','viewer'])
    create_enum_safe('leadstatus', ['new','contacted','qualified','proposal','negotiation','won','lost'])
    create_enum_safe('prstatus', ['draft','pending_approval','approved','rejected','po_created'])
    create_enum_safe('postatus', ['draft','sent','acknowledged','partially_received','received','invoiced','paid','cancelled'])
    create_enum_safe('itemcategory', ['raw_material','wip','finished_goods','consumables','spares'])
    create_enum_safe('employmenttype', ['full_time','part_time','contract'])
    create_enum_safe('transactiontype', ['debit','credit'])
    create_enum_safe('accounttype', ['asset','liability','equity','income','expense'])

    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('super_admin','admin','manager','accountant','hr_manager','purchase_manager','sales_manager','warehouse_manager','viewer', name='userrole', create_type=False), nullable=False, server_default='viewer'),
        sa.Column('department', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('leads',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(20)),
        sa.Column('source', sa.String(100)),
        sa.Column('status', postgresql.ENUM('new','contacted','qualified','proposal','negotiation','won','lost', name='leadstatus', create_type=False), server_default='new'),
        sa.Column('value', sa.Float(), server_default='0'),
        sa.Column('ai_score', sa.Integer(), server_default='0'),
        sa.Column('ai_notes', sa.Text()),
        sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('sales_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_number', sa.String(50), unique=True),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_email', sa.String(255)),
        sa.Column('total_amount', sa.Float(), server_default='0'),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id')),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('vendors',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), unique=True),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.Text()),
        sa.Column('gstin', sa.String(15)),
        sa.Column('payment_terms', sa.Integer(), server_default='30'),
        sa.Column('rating', sa.Float(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('purchase_requisitions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pr_number', sa.String(50), unique=True),
        sa.Column('item_description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), server_default='pcs'),
        sa.Column('estimated_cost', sa.Float()),
        sa.Column('department', sa.String(100)),
        sa.Column('required_by', sa.DateTime(timezone=True)),
        sa.Column('status', postgresql.ENUM('draft','pending_approval','approved','rejected','po_created', name='prstatus', create_type=False), server_default='draft'),
        sa.Column('ai_recommendation', sa.Text()),
        sa.Column('requested_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('po_number', sa.String(50), unique=True),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id'), nullable=False),
        sa.Column('pr_id', sa.Integer(), sa.ForeignKey('purchase_requisitions.id')),
        sa.Column('total_amount', sa.Float(), server_default='0'),
        sa.Column('tax_amount', sa.Float(), server_default='0'),
        sa.Column('status', postgresql.ENUM('draft','sent','acknowledged','partially_received','received','invoiced','paid','cancelled', name='postatus', create_type=False), server_default='draft'),
        sa.Column('delivery_date', sa.DateTime(timezone=True)),
        sa.Column('terms', sa.Text()),
        sa.Column('three_way_match_status', sa.String(50), server_default='pending'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(50), unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM('raw_material','wip','finished_goods','consumables','spares', name='itemcategory', create_type=False), server_default='raw_material'),
        sa.Column('unit', sa.String(20), server_default='pcs'),
        sa.Column('current_stock', sa.Float(), server_default='0'),
        sa.Column('reorder_point', sa.Float(), server_default='0'),
        sa.Column('reorder_qty', sa.Float(), server_default='0'),
        sa.Column('unit_cost', sa.Float(), server_default='0'),
        sa.Column('location', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('ai_forecast_qty', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('stock_movements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('items.id'), nullable=False),
        sa.Column('movement_type', sa.String(20)),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('reference', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('employees',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.String(50), unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('phone', sa.String(20)),
        sa.Column('department', sa.String(100)),
        sa.Column('designation', sa.String(100)),
        sa.Column('employment_type', postgresql.ENUM('full_time','part_time','contract', name='employmenttype', create_type=False), server_default='full_time'),
        sa.Column('date_of_joining', sa.Date()),
        sa.Column('date_of_birth', sa.Date()),
        sa.Column('pan', sa.String(10)),
        sa.Column('aadhaar', sa.String(12)),
        sa.Column('bank_account', sa.String(20)),
        sa.Column('ifsc_code', sa.String(11)),
        sa.Column('basic_salary', sa.Float(), server_default='0'),
        sa.Column('hra', sa.Float(), server_default='0'),
        sa.Column('allowances', sa.Float(), server_default='0'),
        sa.Column('pf_applicable', sa.Boolean(), server_default='true'),
        sa.Column('esi_applicable', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('payrolls',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('month', sa.Integer()),
        sa.Column('year', sa.Integer()),
        sa.Column('working_days', sa.Float(), server_default='26'),
        sa.Column('present_days', sa.Float(), server_default='26'),
        sa.Column('basic', sa.Float(), server_default='0'),
        sa.Column('hra', sa.Float(), server_default='0'),
        sa.Column('allowances', sa.Float(), server_default='0'),
        sa.Column('gross_salary', sa.Float(), server_default='0'),
        sa.Column('pf_employee', sa.Float(), server_default='0'),
        sa.Column('pf_employer', sa.Float(), server_default='0'),
        sa.Column('esi_employee', sa.Float(), server_default='0'),
        sa.Column('esi_employer', sa.Float(), server_default='0'),
        sa.Column('tds', sa.Float(), server_default='0'),
        sa.Column('net_salary', sa.Float(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('ai_anomaly_flag', sa.Boolean(), server_default='false'),
        sa.Column('ai_anomaly_notes', sa.Text()),
    )
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(20), unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('account_type', postgresql.ENUM('asset','liability','equity','income','expense', name='accounttype', create_type=False)),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('accounts.id')),
        sa.Column('balance', sa.Float(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
    )
    op.create_table('journal_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_number', sa.String(50), unique=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('reference', sa.String(100)),
        sa.Column('total_debit', sa.Float(), server_default='0'),
        sa.Column('total_credit', sa.Float(), server_default='0'),
        sa.Column('is_balanced', sa.Boolean(), server_default='false'),
        sa.Column('ai_generated', sa.Boolean(), server_default='false'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('journal_lines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('journal_entries.id'), nullable=False),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('debit','credit', name='transactiontype', create_type=False)),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('narration', sa.Text()),
    )
    op.create_table('agent_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('module', sa.String(50)),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', sa.Integer()),
        sa.Column('input_data', sa.Text()),
        sa.Column('output_data', sa.Text()),
        sa.Column('tokens_used', sa.Integer(), server_default='0'),
        sa.Column('duration_ms', sa.Float(), server_default='0'),
        sa.Column('success', sa.Boolean(), server_default='true'),
        sa.Column('error_message', sa.Text()),
        sa.Column('triggered_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('agent_logs')
    op.drop_table('journal_lines')
    op.drop_table('journal_entries')
    op.drop_table('accounts')
    op.drop_table('payrolls')
    op.drop_table('employees')
    op.drop_table('stock_movements')
    op.drop_table('items')
    op.drop_table('purchase_orders')
    op.drop_table('purchase_requisitions')
    op.drop_table('vendors')
    op.drop_table('sales_orders')
    op.drop_table('leads')
    op.drop_table('users')
    for t in ['userrole','leadstatus','prstatus','postatus','itemcategory','employmenttype','transactiontype','accounttype']:
        op.execute(f"DROP TYPE IF EXISTS {t}")