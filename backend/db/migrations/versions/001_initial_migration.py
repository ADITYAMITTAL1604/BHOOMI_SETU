"""Initial migration with all models

Revision ID: 001
Revises: 
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='FIELD_OFFICER'),
        sa.Column('state_scope', sa.String(length=100), nullable=True),
        sa.Column('district_scope', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_index('ix_users_state_scope', 'users', ['state_scope'], unique=False)
    op.create_index('ix_users_district_scope', 'users', ['district_scope'], unique=False)

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=False)
    op.create_index('idx_refresh_token_lookup', 'refresh_tokens', ['token', 'is_revoked'], unique=False)

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('states', postgresql.ARRAY(sa.String(length=100)), nullable=False, server_default='{}'),
        sa.Column('districts', postgresql.ARRAY(sa.String(length=100)), nullable=False, server_default='{}'),
        sa.Column('land_required_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('land_acquired_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNING'),
        sa.Column('corridor_geometry', sa.types.UserDefinedType(), nullable=True),  # PostGIS Geometry
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('project_id')
    )
    op.create_index('ix_projects_name', 'projects', ['name'], unique=False)
    op.create_index('ix_projects_type', 'projects', ['type'], unique=False)
    op.create_index('ix_projects_status', 'projects', ['status'], unique=False)
    op.create_index('idx_project_status_type', 'projects', ['status', 'type'], unique=False)

    # Create parcels table
    op.create_table(
        'parcels',
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('survey_number', sa.String(length=100), nullable=False),
        sa.Column('area_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('geometry', sa.types.UserDefinedType(), nullable=True),  # PostGIS Geometry
        sa.Column('owner_name', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('owner_reference', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('current_stage', sa.String(length=50), nullable=False, server_default='PROPOSAL'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='NOT_STARTED'),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('village', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('district', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('state', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('assigned_officer', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['assigned_officer'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('parcel_id')
    )
    op.create_index('ix_parcels_project_id', 'parcels', ['project_id'], unique=False)
    op.create_index('ix_parcels_survey_number', 'parcels', ['survey_number'], unique=False)
    op.create_index('ix_parcels_current_stage', 'parcels', ['current_stage'], unique=False)
    op.create_index('ix_parcels_status', 'parcels', ['status'], unique=False)
    op.create_index('ix_parcels_village', 'parcels', ['village'], unique=False)
    op.create_index('ix_parcels_district', 'parcels', ['district'], unique=False)
    op.create_index('ix_parcels_state', 'parcels', ['state'], unique=False)
    op.create_index('ix_parcels_assigned_officer', 'parcels', ['assigned_officer'], unique=False)
    op.create_index('idx_parcel_state_district', 'parcels', ['state', 'district'], unique=False)
    op.create_index('idx_parcel_project_stage', 'parcels', ['project_id', 'current_stage'], unique=False)
    op.create_index('idx_parcel_risk_score', 'parcels', ['risk_score'], unique=False, postgresql_using='btree')

    # Create acquisition_stages table
    op.create_table(
        'acquisition_stages',
        sa.Column('stage_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage_name', sa.String(length=50), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='NOT_STARTED'),
        sa.Column('assigned_officer', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['assigned_officer'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.parcel_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('stage_id')
    )
    op.create_index('ix_acquisition_stages_parcel_id', 'acquisition_stages', ['parcel_id'], unique=False)
    op.create_index('ix_acquisition_stages_stage_name', 'acquisition_stages', ['stage_name'], unique=False)
    op.create_index('ix_acquisition_stages_status', 'acquisition_stages', ['status'], unique=False)
    op.create_index('idx_stage_parcel_order', 'acquisition_stages', ['parcel_id', 'stage_order'], unique=False)

    # Create compensation table
    op.create_table(
        'compensation',
        sa.Column('compensation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessed_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('approved_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('paid_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('payment_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.parcel_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('compensation_id'),
        sa.UniqueConstraint('parcel_id')
    )
    op.create_index('ix_compensation_parcel_id', 'compensation', ['parcel_id'], unique=False)
    op.create_index('ix_compensation_payment_status', 'compensation', ['payment_status'], unique=False)

    # Create rr_records table
    op.create_table(
        'rr_records',
        sa.Column('rr_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paf_name', sa.String(length=255), nullable=False),
        sa.Column('paf_type', sa.String(length=50), nullable=False, server_default='TITLE_HOLDER'),
        sa.Column('family_size', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('affected_area_ha', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0'),
        sa.Column('rehabilitation_status', sa.String(length=50), nullable=False, server_default='IDENTIFIED'),
        sa.Column('compensation_paid', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('relocation_site', sa.String(length=255), nullable=True),
        sa.Column('plot_allotted', sa.String(length=100), nullable=True),
        sa.Column('geometry', sa.types.UserDefinedType(), nullable=True),  # PostGIS POINT Geometry
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.parcel_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rr_id')
    )
    op.create_index('ix_rr_records_parcel_id', 'rr_records', ['parcel_id'], unique=False)
    op.create_index('ix_rr_records_paf_name', 'rr_records', ['paf_name'], unique=False)
    op.create_index('ix_rr_records_rehabilitation_status', 'rr_records', ['rehabilitation_status'], unique=False)
    op.create_index('idx_rr_parcel_status', 'rr_records', ['parcel_id', 'rehabilitation_status'], unique=False)
    op.create_index('idx_rr_paf_name', 'rr_records', ['paf_name'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stage_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(length=100), nullable=False, server_default='application/octet-stream'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.parcel_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stage_id'], ['acquisition_stages.stage_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('document_id')
    )
    op.create_index('ix_documents_project_id', 'documents', ['project_id'], unique=False)
    op.create_index('ix_documents_parcel_id', 'documents', ['parcel_id'], unique=False)
    op.create_index('ix_documents_stage_id', 'documents', ['stage_id'], unique=False)
    op.create_index('ix_documents_uploaded_by', 'documents', ['uploaded_by'], unique=False)
    op.create_index('ix_documents_document_type', 'documents', ['document_type'], unique=False)
    op.create_index('idx_document_project_type', 'documents', ['project_id', 'document_type'], unique=False)
    op.create_index('idx_document_parcel_type', 'documents', ['parcel_id', 'document_type'], unique=False)
    op.create_index('idx_document_uploaded_by', 'documents', ['uploaded_by'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'], unique=False)
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'], unique=False)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_user_action', 'audit_logs', ['user_id', 'action'], unique=False)
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'], unique=False, postgresql_using='btree')

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='INFO'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.parcel_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alert_id')
    )
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'], unique=False)
    op.create_index('ix_alerts_project_id', 'alerts', ['project_id'], unique=False)
    op.create_index('ix_alerts_parcel_id', 'alerts', ['parcel_id'], unique=False)
    op.create_index('ix_alerts_severity', 'alerts', ['severity'], unique=False)
    op.create_index('ix_alerts_is_read', 'alerts', ['is_read'], unique=False)
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'], unique=False)
    op.create_index('idx_alert_user_read', 'alerts', ['user_id', 'is_read'], unique=False)
    op.create_index('idx_alert_project', 'alerts', ['project_id'], unique=False)
    op.create_index('idx_alert_parcel', 'alerts', ['parcel_id'], unique=False)
    op.create_index('idx_alert_severity_created', 'alerts', ['severity', 'created_at'], unique=False, postgresql_using='btree')

    # Create project_history table
    op.create_table(
        'project_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('land_required_ha', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.0'),
        sa.Column('land_acquired_ha', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.0'),
        sa.Column('parcels_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parcels_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parcels_in_progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parcels_blocked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('compensation_paid_total', sa.Numeric(precision=16, scale=2), nullable=False, server_default='0.0'),
        sa.Column('compensation_pending_total', sa.Numeric(precision=16, scale=2), nullable=False, server_default='0.0'),
        sa.Column('stages_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('history_id')
    )
    op.create_index('ix_project_history_project_id', 'project_history', ['project_id'], unique=False)
    op.create_index('ix_project_history_snapshot_date', 'project_history', ['snapshot_date'], unique=False)
    op.create_index('idx_history_project_date', 'project_history', ['project_id', 'snapshot_date'], unique=False, postgresql_using='btree')


def downgrade() -> None:
    op.drop_index('idx_history_project_date', table_name='project_history')
    op.drop_index('ix_project_history_snapshot_date', table_name='project_history')
    op.drop_index('ix_project_history_project_id', table_name='project_history')
    op.drop_table('project_history')

    op.drop_index('idx_alert_severity_created', table_name='alerts')
    op.drop_index('idx_alert_parcel', table_name='alerts')
    op.drop_index('idx_alert_project', table_name='alerts')
    op.drop_index('idx_alert_user_read', table_name='alerts')
    op.drop_index('ix_alerts_created_at', table_name='alerts')
    op.drop_index('ix_alerts_is_read', table_name='alerts')
    op.drop_index('ix_alerts_severity', table_name='alerts')
    op.drop_index('ix_alerts_parcel_id', table_name='alerts')
    op.drop_index('ix_alerts_project_id', table_name='alerts')
    op.drop_index('ix_alerts_user_id', table_name='alerts')
    op.drop_table('alerts')

    op.drop_index('idx_audit_created', table_name='audit_logs')
    op.drop_index('idx_audit_user_action', table_name='audit_logs')
    op.drop_index('idx_audit_entity', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('idx_document_uploaded_by', table_name='documents')
    op.drop_index('idx_document_parcel_type', table_name='documents')
    op.drop_index('idx_document_project_type', table_name='documents')
    op.drop_index('ix_documents_document_type', table_name='documents')
    op.drop_index('ix_documents_uploaded_by', table_name='documents')
    op.drop_index('ix_documents_stage_id', table_name='documents')
    op.drop_index('ix_documents_parcel_id', table_name='documents')
    op.drop_index('ix_documents_project_id', table_name='documents')
    op.drop_table('documents')

    op.drop_index('idx_rr_paf_name', table_name='rr_records')
    op.drop_index('idx_rr_parcel_status', table_name='rr_records')
    op.drop_index('ix_rr_records_rehabilitation_status', table_name='rr_records')
    op.drop_index('ix_rr_records_paf_name', table_name='rr_records')
    op.drop_index('ix_rr_records_parcel_id', table_name='rr_records')
    op.drop_table('rr_records')

    op.drop_index('ix_compensation_payment_status', table_name='compensation')
    op.drop_index('ix_compensation_parcel_id', table_name='compensation')
    op.drop_table('compensation')

    op.drop_index('idx_stage_parcel_order', table_name='acquisition_stages')
    op.drop_index('ix_acquisition_stages_status', table_name='acquisition_stages')
    op.drop_index('ix_acquisition_stages_stage_name', table_name='acquisition_stages')
    op.drop_index('ix_acquisition_stages_parcel_id', table_name='acquisition_stages')
    op.drop_table('acquisition_stages')

    op.drop_index('idx_parcel_risk_score', table_name='parcels')
    op.drop_index('idx_parcel_project_stage', table_name='parcels')
    op.drop_index('idx_parcel_state_district', table_name='parcels')
    op.drop_index('ix_parcels_assigned_officer', table_name='parcels')
    op.drop_index('ix_parcels_state', table_name='parcels')
    op.drop_index('ix_parcels_district', table_name='parcels')
    op.drop_index('ix_parcels_village', table_name='parcels')
    op.drop_index('ix_parcels_status', table_name='parcels')
    op.drop_index('ix_parcels_current_stage', table_name='parcels')
    op.drop_index('ix_parcels_survey_number', table_name='parcels')
    op.drop_index('ix_parcels_project_id', table_name='parcels')
    op.drop_table('parcels')

    op.drop_index('idx_project_status_type', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_type', table_name='projects')
    op.drop_index('ix_projects_name', table_name='projects')
    op.drop_table('projects')

    op.drop_index('idx_refresh_token_lookup', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index('ix_users_district_scope', table_name='users')
    op.drop_index('ix_users_state_scope', table_name='users')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')

    op.execute("DROP EXTENSION IF EXISTS postgis")