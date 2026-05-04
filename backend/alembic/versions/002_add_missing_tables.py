"""Add missing tables and fields for complete schema

Revision ID: 002_add_missing_tables
Revises: 001_initial
Create Date: 2024-05-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_missing_tables'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to users table
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # Add indexes for users table
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    
    # Create knowledge_bases table
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.String(), nullable=False),
        sa.Column('embedding_provider', sa.String(), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=False),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False),
        sa.Column('chunking_strategy', sa.String(), nullable=False),
        sa.Column('top_k', sa.Integer(), nullable=False),
        sa.Column('similarity_threshold', sa.Float(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('vector_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_knowledge_bases_user_id', 'knowledge_bases', ['user_id'])
    op.create_index('idx_knowledge_bases_is_active', 'knowledge_bases', ['is_active'])
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('knowledge_base_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_documents_knowledge_base_id', 'documents', ['knowledge_base_id'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('graph_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_workflows_user_id', 'workflows', ['user_id'])
    op.create_index('idx_workflows_status', 'workflows', ['status'])
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workflow_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('trigger_type', sa.String(), nullable=False),
        sa.Column('inputs', sa.JSON(), nullable=True),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('idx_workflow_executions_user_id', 'workflow_executions', ['user_id'])
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'])
    
    # Create node_executions table
    op.create_table(
        'node_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('execution_id', sa.String(), nullable=False),
        sa.Column('node_id', sa.String(), nullable=False),
        sa.Column('node_type', sa.String(), nullable=False),
        sa.Column('node_name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('inputs', sa.JSON(), nullable=True),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_node_executions_execution_id', 'node_executions', ['execution_id'])
    
    # Create agent_groups table
    op.create_table(
        'agent_groups',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mode', sa.String(), nullable=False),
        sa.Column('mode_config', sa.JSON(), nullable=True),
        sa.Column('default_model', sa.String(), nullable=False),
        sa.Column('default_provider', sa.String(), nullable=False),
        sa.Column('enable_orchestrator', sa.Boolean(), nullable=False),
        sa.Column('orchestrator_prompt', sa.Text(), nullable=True),
        sa.Column('max_iterations', sa.Integer(), nullable=False),
        sa.Column('termination_prompt', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_agent_groups_user_id', 'agent_groups', ['user_id'])
    
    # Create agent_members table
    op.create_table(
        'agent_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('group_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('model_provider', sa.String(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['group_id'], ['agent_groups.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_agent_members_group_id', 'agent_members', ['group_id'])
    
    # Create collaboration_sessions table
    op.create_table(
        'collaboration_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('group_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('current_iteration', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('inputs', sa.JSON(), nullable=True),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['group_id'], ['agent_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_collaboration_sessions_group_id', 'collaboration_sessions', ['group_id'])
    op.create_index('idx_collaboration_sessions_user_id', 'collaboration_sessions', ['user_id'])
    
    # Create agent_messages table
    op.create_table(
        'agent_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('member_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_agent_messages_session_id', 'agent_messages', ['session_id'])
    
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_format', sa.String(), nullable=False),
        sa.Column('format_type', sa.String(), nullable=False),
        sa.Column('total_samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('avg_turns', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_validated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('train_ratio', sa.Float(), nullable=False, server_default='0.9'),
        sa.Column('validation_ratio', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_datasets_user_id', 'datasets', ['user_id'])
    
    # Create finetune_jobs table
    op.create_table(
        'finetune_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('dataset_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_model', sa.String(), nullable=False),
        sa.Column('base_model_type', sa.String(), nullable=False),
        sa.Column('training_config', sa.JSON(), nullable=False),
        sa.Column('lora_config', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_epoch', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_epochs', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('current_loss', sa.Float(), nullable=True),
        sa.Column('best_loss', sa.Float(), nullable=True),
        sa.Column('output_dir', sa.String(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('logs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_finetune_jobs_user_id', 'finetune_jobs', ['user_id'])
    op.create_index('idx_finetune_jobs_status', 'finetune_jobs', ['status'])
    
    # Create mcp_servers table
    op.create_table(
        'mcp_servers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transport_type', sa.String(), nullable=False),
        sa.Column('sse_url', sa.String(), nullable=True),
        sa.Column('sse_endpoint', sa.String(), nullable=True),
        sa.Column('stdio_command', sa.String(), nullable=True),
        sa.Column('stdio_args', sa.JSON(), nullable=True),
        sa.Column('stdio_env', sa.JSON(), nullable=True),
        sa.Column('http_url', sa.String(), nullable=True),
        sa.Column('http_headers', sa.JSON(), nullable=True),
        sa.Column('auth_type', sa.String(), nullable=True),
        sa.Column('auth_config', sa.JSON(), nullable=True),
        sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_connected_at', sa.DateTime(), nullable=True),
        sa.Column('connection_error', sa.Text(), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_mcp_servers_user_id', 'mcp_servers', ['user_id'])
    
    # Create mcp_tools table
    op.create_table(
        'mcp_tools',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_schema', sa.JSON(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('total_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_execution_time', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_discovered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('discovered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['server_id'], ['mcp_servers.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_mcp_tools_server_id', 'mcp_tools', ['server_id'])
    
    # Create mcp_logs table
    op.create_table(
        'mcp_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('tool_id', sa.String(), nullable=True),
        sa.Column('tool_name', sa.String(), nullable=True),
        sa.Column('request', sa.JSON(), nullable=True),
        sa.Column('response', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['server_id'], ['mcp_servers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['mcp_tools.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_mcp_logs_server_id', 'mcp_logs', ['server_id'])
    op.create_index('idx_mcp_logs_created_at', 'mcp_logs', ['created_at'])


def downgrade() -> None:
    # Drop all new tables in reverse order
    op.drop_table('mcp_logs')
    op.drop_table('mcp_tools')
    op.drop_table('mcp_servers')
    op.drop_table('finetune_jobs')
    op.drop_table('datasets')
    op.drop_table('agent_messages')
    op.drop_table('collaboration_sessions')
    op.drop_table('agent_members')
    op.drop_table('agent_groups')
    op.drop_table('node_executions')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
    op.drop_table('documents')
    op.drop_table('knowledge_bases')
    
    # Drop columns from users table
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
