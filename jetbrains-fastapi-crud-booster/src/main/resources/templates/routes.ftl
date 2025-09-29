"""API routes for ${entity.name}."""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.${entity.name} import create, get, get_multi, remove, update
from app.schemas.${entity.name} import ${entity.name}, ${entity.name}Create, ${entity.name}Update

router = APIRouter(prefix="/api/v1/${entity.name?lower_case}s", tags=["${entity.name}"])

# >>> FASTAPI_CRUD_BOOSTER
@router.get("/", response_model=List[${entity.name}], summary="List ${entity.name?lower_case}s with pagination and filters")
def read_${entity.name?lower_case}s(
    db: Session = Depends(get_db),
<#if settings.enablePagination>
    skip: int = 0,
    limit: int = Query(100, le=500, description="Max items per page"),
</#if>
<#if settings.enableFilters>
<#list entity.fields as field>
    ${field.name}: Optional[str] = Query(None, description="Filter by ${field.name}"),
</#list>
</#if>
) -> List[${entity.name}]:
<#if settings.enableFilters>
    filters: Dict[str, str] = {
<#list entity.fields as field>
        "${field.name}": ${field.name},
</#list>
    }
    filters = {k: v for k, v in filters.items() if v is not None}
<#else>
    filters: Dict[str, str] = {}
</#if>
    return get_multi(
        db=db,
<#if settings.enablePagination>
        skip=skip,
        limit=limit,
</#if>
        filters=filters or None,
    )


@router.get("/{item_id}", response_model=${entity.name}, summary="Get ${entity.name?lower_case} by id")
def read_${entity.name?lower_case}(item_id: int, db: Session = Depends(get_db)) -> ${entity.name}:
    obj = get(db, id=item_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="${entity.name} not found")
    return obj


@router.post("/", response_model=${entity.name}, status_code=status.HTTP_201_CREATED, summary="Create ${entity.name?lower_case}")
def create_${entity.name?lower_case}(payload: ${entity.name}Create, db: Session = Depends(get_db)) -> ${entity.name}:
    return create(db, obj_in=payload)


@router.put("/{item_id}", response_model=${entity.name}, summary="Update ${entity.name?lower_case}")
def update_${entity.name?lower_case}(item_id: int, payload: ${entity.name}Update, db: Session = Depends(get_db)) -> ${entity.name}:
    obj = get(db, id=item_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="${entity.name} not found")
    return update(db, db_obj=obj, obj_in=payload)


@router.delete("/{item_id}", response_model=${entity.name}, summary="Delete ${entity.name?lower_case}")
def delete_${entity.name?lower_case}(item_id: int, db: Session = Depends(get_db)) -> ${entity.name}:
    obj = remove(db, id=item_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="${entity.name} not found")
    return obj
# <<< FASTAPI_CRUD_BOOSTER
