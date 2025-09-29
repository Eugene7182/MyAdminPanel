"""Create ${entity.name} table."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "${timestamp}_${entity.name?lower_case}"
down_revision = None
branch_labels = None
depends_on = None


# >>> FASTAPI_CRUD_BOOSTER
def upgrade() -> None:
    op.create_table(
        "${entity.tableName}",
        sa.Column("id", sa.Integer(), primary_key=True),
<#list entity.fields as field>
        sa.Column(
            "${field.name}",
            ${field.type?switch('int','sa.Integer()','float','sa.Float()','decimal','sa.Numeric()','str','sa.String(length=255)','bool','sa.Boolean()','date','sa.Date()','datetime','sa.DateTime()')},
            nullable=${field.nullable?string('True','False')},
            unique=${field.unique?string('True','False')}
        ),
</#list>
    )
<#list entity.fields as field>
<#if field.indexed>
    op.create_index("ix_${entity.tableName}_${field.name}", "${entity.tableName}", ["${field.name}"])
</#if>
</#list>


def downgrade() -> None:
<#list entity.fields as field>
<#if field.indexed>
    op.drop_index("ix_${entity.tableName}_${field.name}", table_name="${entity.tableName}")
</#if>
</#list>
    op.drop_table("${entity.tableName}")
# <<< FASTAPI_CRUD_BOOSTER
