"""Tests for ${entity.name} routes."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal

client = TestClient(app)


# >>> FASTAPI_CRUD_BOOSTER
@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_${entity.name?lower_case}(db_session):
    payload = {
<#list entity.fields as field>
        "${field.name}": ${field.type?switch('int','1','float','1.0','decimal','"1.00"','str','"sample"','bool','true','date','"2024-01-01"','datetime','"2024-01-01T00:00:00"')},
</#list>
    }
    response = client.post("/api/v1/${entity.name?lower_case}s/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data


def test_list_${entity.name?lower_case}s(db_session):
    response = client.get("/api/v1/${entity.name?lower_case}s/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
# <<< FASTAPI_CRUD_BOOSTER
