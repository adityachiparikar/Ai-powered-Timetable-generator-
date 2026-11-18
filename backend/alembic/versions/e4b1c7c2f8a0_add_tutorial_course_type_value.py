"""add tutorial course type value

Revision ID: e4b1c7c2f8a0
Revises: 28cf4cf07d6e
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e4b1c7c2f8a0"
down_revision: Union[str, None] = "28cf4cf07d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE coursetype ADD VALUE IF NOT EXISTS 'TUTORIAL'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be safely removed without recreating the type.
    pass
