"""Make unavailable FACEIT statistics nullable in legacy databases."""
from alembic import op

revision = "20260809_02"
down_revision = "20260809_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE cs2_profiles ALTER COLUMN kd_ratio DROP NOT NULL;
    ALTER TABLE cs2_profiles ALTER COLUMN role DROP NOT NULL;
    """)


def downgrade() -> None:
    op.execute("UPDATE cs2_profiles SET kd_ratio=0 WHERE kd_ratio IS NULL; ALTER TABLE cs2_profiles ALTER COLUMN kd_ratio SET NOT NULL")
