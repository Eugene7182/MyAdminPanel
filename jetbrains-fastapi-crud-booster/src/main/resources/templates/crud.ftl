"""CRUD services for ${entity.name}."""
from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.${entity.name} import ${entity.name}
from app.schemas.${entity.name} import ${entity.name}Create, ${entity.name}Update
<#if settings.enableFeatureFlags>
from app.feature_flags import toggles
</#if>

# >>> FASTAPI_CRUD_BOOSTER
def get(db: Session, *, id: int) -> Optional[${entity.name}]:
    stmt = select(${entity.name}).where(${entity.name}.id == id)
<#if settings.sqlalchemyMajor == 2>
    return db.scalar(stmt)
<#else>
    return db.execute(stmt).scalar_one_or_none()
</#if>


def get_multi(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, str]] = None,
) -> List[${entity.name}]:
<#if settings.enableFeatureFlags>
    if not toggles.is_enabled("enable_${entity.name?lower_case}_module"):
        return []
</#if>
    stmt = select(${entity.name})
<#if settings.enableFilters>
    if filters:
        for key, value in filters.items():
            column = getattr(${entity.name}, key, None)
            if column is not None:
                stmt = stmt.where(column == value)
</#if>
<#if settings.enablePagination>
    stmt = stmt.offset(skip).limit(limit)
</#if>
<#if settings.sqlalchemyMajor == 2>
    return list(db.scalars(stmt).all())
<#else>
    return list(db.execute(stmt).scalars().all())
</#if>


def create(db: Session, *, obj_in: ${entity.name}Create) -> ${entity.name}:
<#if settings.enableFeatureFlags>
    if not toggles.is_enabled("enable_${entity.name?lower_case}_module"):
        raise RuntimeError("${entity.name} module is disabled via feature flag")
</#if>
<#if settings.pydanticMajor == 2>
    payload = obj_in.model_dump(exclude_unset=True)
<#else>
    payload = obj_in.dict(exclude_unset=True)
</#if>
    instance = ${entity.name}(**payload)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def update(db: Session, *, db_obj: ${entity.name}, obj_in: ${entity.name}Update) -> ${entity.name}:
<#if settings.pydanticMajor == 2>
    update_data = obj_in.model_dump(exclude_unset=True)
<#else>
    update_data = obj_in.dict(exclude_unset=True)
</#if>
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove(db: Session, *, id: int) -> Optional[${entity.name}]:
    obj = get(db, id=id)
    if not obj:
        return None
    db.delete(obj)
    db.commit()
    return obj
# <<< FASTAPI_CRUD_BOOSTER
