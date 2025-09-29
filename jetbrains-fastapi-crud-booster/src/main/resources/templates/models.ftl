"""SQLAlchemy model for ${entity.name}."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String
<#if settings.sqlalchemyMajor == 2>
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
<#else>
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base
Base = declarative_base()
</#if>

# >>> FASTAPI_CRUD_BOOSTER
class ${entity.name}(Base):
    """${entity.description}"""
    __tablename__ = "${entity.tableName}"

<#if settings.sqlalchemyMajor == 2>
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
<#else>
    id = Column(Integer, primary_key=True, index=True)
</#if>
<#list entity.fields as field>
<#assign saType = field.type?switch('int','Integer','float','Float','decimal','Numeric','str','String','bool','Boolean','date','Date','datetime','DateTime')>
<#assign hintType = field.type?switch('int','int','float','float','decimal','Decimal','str','str','bool','bool','date','date','datetime','datetime')>
<#if settings.sqlalchemyMajor == 2>
    ${field.name}: Mapped[${hintType}] = mapped_column(
        ${saType},
        nullable=${field.nullable?string('True','False')},
        unique=${field.unique?string('True','False')},
        index=${field.indexed?string('True','False')}
        <#if field.defaultValue??>, default=${field.defaultValue}</#if>
    )  # ${field.description!""}
<#else>
    ${field.name} = Column(
        ${saType},
        nullable=${field.nullable?string('True','False')},
        unique=${field.unique?string('True','False')},
        index=${field.indexed?string('True','False')}
        <#if field.defaultValue??>, default=${field.defaultValue}</#if>
    )  # ${field.description!""}
</#if>
</#list>
# <<< FASTAPI_CRUD_BOOSTER
