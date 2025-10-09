"""add zalo instagram tiktok to channel_type enum

Revision ID: 9eea59675ee4
Revises: c40668857d93
Create Date: 2025-10-09 10:28:18.908122

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9eea59675ee4"
down_revision: Union[str, Sequence[str], None] = "c40668857d93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old check constraint
    op.drop_constraint("valid_channel_type", "user_channels", type_="check")

    # Add new check constraint with updated channel types
    op.create_check_constraint(
        "valid_channel_type",
        "user_channels",
        "channel_type IN ('telegram', 'whatsapp', 'messenger', 'zalo', 'instagram', 'tiktok', 'direct')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new check constraint
    op.drop_constraint("valid_channel_type", "user_channels", type_="check")

    # Restore old check constraint
    op.create_check_constraint(
        "valid_channel_type",
        "user_channels",
        "channel_type IN ('telegram', 'whatsapp', 'messenger', 'direct')",
    )
