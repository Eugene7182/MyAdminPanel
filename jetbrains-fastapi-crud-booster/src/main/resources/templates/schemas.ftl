"""Pydantic schemas for ${entity.name}."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

<#if settings.pydanticMajor == 2>
from pydantic import BaseModel, ConfigDict
<#else>
from pydantic import BaseModel
</#if>

# >>> FASTAPI_CRUD_BOOSTER
class ${entity.name}Base(BaseModel):
<#list entity.fields as field>
    ${field.name}: Optional[${field.type?switch('int','int','float','float','decimal','Decimal','str','str','bool','bool','date','date','datetime','datetime')}] = None  # ${field.description!""}
</#list>


class ${entity.name}Create(${entity.name}Base):
    pass


class ${entity.name}Update(${entity.name}Base):
    pass


class ${entity.name}InDBBase(${entity.name}Base):
    id: int
<#if settings.pydanticMajor == 2>
    model_config = ConfigDict(from_attributes=True)
<#else>
    class Config:
        orm_mode = True
</#if>


class ${entity.name}(${entity.name}InDBBase):
    pass


class ${entity.name}InDB(${entity.name}InDBBase):
    pass
# <<< FASTAPI_CRUD_BOOSTER
