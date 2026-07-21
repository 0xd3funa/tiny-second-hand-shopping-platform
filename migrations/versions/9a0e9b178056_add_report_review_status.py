"""add report review status

Revision ID: 9a0e9b178056
Revises: 6bbe19095984
Create Date: 2026-07-21 21:22:10.148950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a0e9b178056'
down_revision = '6bbe19095984'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "reports",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=10),
                server_default=sa.text("'pending'"),
                nullable=False,
            )
        )

        batch_op.add_column(
            sa.Column(
                "reviewed_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

        batch_op.create_check_constraint(
            "ck_reports_status",
            "status IN ('pending', 'resolved', 'dismissed')",
        )


def downgrade():
    with op.batch_alter_table(
        "reports",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "ck_reports_status",
            type_="check",
        )

        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("status")
