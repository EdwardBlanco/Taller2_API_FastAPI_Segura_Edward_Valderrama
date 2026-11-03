from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_multa_pagada"
down_revision: Union[str, Sequence[str], None] = "0001_estado_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestamos",
        sa.Column("multa_pagada", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE prestamos SET multa_pagada = true WHERE multa = 0")


def downgrade() -> None:
    op.drop_column("prestamos", "multa_pagada")

