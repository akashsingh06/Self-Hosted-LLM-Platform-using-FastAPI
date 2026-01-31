Write-Host "Setting up Alembic configuration..." -ForegroundColor Green

# Create directories
if (-not (Test-Path "alembic")) {
    New-Item -ItemType Directory -Path "alembic" | Out-Null
}
if (-not (Test-Path "alembic\versions")) {
    New-Item -ItemType Directory -Path "alembic\versions" | Out-Null
}

Write-Host "1. Creating alembic.ini..." -ForegroundColor Yellow
# Create alembic.ini
@"
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://llm_user:llm_password@localhost:5432/llm_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"@ | Out-File -FilePath "alembic.ini" -Encoding ascii

Write-Host "2. Creating alembic\env.py..." -ForegroundColor Yellow
# Create env.py
@"
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.session import Base
from src.database.models import (
    User, Conversation, Message, 
    FinetuneJob, FinetuneDataset, 
    CodeBlock, SystemLog, CacheEntry
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.config.settings import settings
config.set_main_option(""sqlalchemy.url"", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option(""sqlalchemy.url"")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={""paramstyle"": ""named""},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix=""sqlalchemy."",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"@ | Out-File -FilePath "alembic\env.py" -Encoding ascii

Write-Host "3. Creating alembic\script.py.mako..." -ForegroundColor Yellow
# Create script.py.mako
@"""`${""$""}{message}

Revision ID: `${""$""}{up_revision}
Revises: `${""$""}{down_revision | comma,n}
Create Date: `${""$""}{create_date}

"""
from alembic import op
import sqlalchemy as sa
`${""$""}{imports if imports else ""}

# revision identifiers, used by Alembic.
revision = `${""$""}{repr(up_revision)}
down_revision = `${""$""}{repr(down_revision)}
branch_labels = `${""$""}{repr(branch_labels)}
depends_on = `${""$""}{repr(depends_on)}

def upgrade() -> None:
    `${""$""}{upgrades if upgrades else ""pass""}

def downgrade() -> None:
    `${""$""}{downgrades if downgrades else ""pass""}
"@ | Out-File -FilePath "alembic\script.py.mako" -Encoding ascii

Write-Host "4. Creating initial migration..." -ForegroundColor Yellow
# Create initial migration
@"""Initial migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('ix_conversations_user_id', 'user_id')
    )
    
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.Index('ix_messages_conversation_id', 'conversation_id')
    )
    
    op.create_table('finetune_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('base_model', sa.String(length=100), nullable=False),
        sa.Column('new_model_name', sa.String(length=100), nullable=True),
        sa.Column('dataset_path', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('epochs', sa.Integer(), nullable=True),
        sa.Column('batch_size', sa.Integer(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('lora_rank', sa.Integer(), nullable=True),
        sa.Column('target_modules', sa.JSON(), nullable=True),
        sa.Column('loss_history', sa.JSON(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('ix_finetune_jobs_user_id', 'user_id')
    )
    
    op.create_table('finetune_datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('ix_finetune_datasets_user_id', 'user_id')
    )
    
    op.create_table('code_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=True),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.Index('ix_code_blocks_message_id', 'message_id')
    )
    
    op.create_table('system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_system_logs_created_at', 'created_at')
    )
    
    op.create_table('cache_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('ttl', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_cache_entries_key', 'key', unique=True)
    )

def downgrade() -> None:
    op.drop_table('cache_entries')
    op.drop_table('system_logs')
    op.drop_table('code_blocks')
    op.drop_table('finetune_datasets')
    op.drop_table('finetune_jobs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')
"@ | Out-File -FilePath "alembic\versions\001_initial_migration.py" -Encoding ascii

Write-Host "✅ Configuration files created successfully!" -ForegroundColor Green
Write-Host "`nRunning database migrations..." -ForegroundColor Yellow

# Run migrations
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Database setup completed successfully!" -ForegroundColor Green
    Write-Host "`n📊 Tables created:" -ForegroundColor Cyan
    Write-Host "  • users" -ForegroundColor White
    Write-Host "  • conversations" -ForegroundColor White
    Write-Host "  • messages" -ForegroundColor White
    Write-Host "  • finetune_jobs" -ForegroundColor White
    Write-Host "  • finetune_datasets" -ForegroundColor White
    Write-Host "  • code_blocks" -ForegroundColor White
    Write-Host "  • system_logs" -ForegroundColor White
    Write-Host "  • cache_entries" -ForegroundColor White
} else {
    Write-Host "`n❌ Migration failed. Check the error above." -ForegroundColor Red
}