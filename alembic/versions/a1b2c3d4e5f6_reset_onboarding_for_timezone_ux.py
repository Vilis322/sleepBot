"""Reset onboarding for timezone UX update

Revision ID: a1b2c3d4e5f6
Revises: 04d2a6bb3420
Create Date: 2026-03-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '04d2a6bb3420'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET is_onboarded = false")


def downgrade() -> None:
    pass
