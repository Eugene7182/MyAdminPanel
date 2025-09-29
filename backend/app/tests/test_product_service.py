from __future__ import annotations

from datetime import datetime

from app.services.products.service import build_filters


def test_build_filters_handles_contains():
    filters = list(build_filters({"title_contains": "abc"}))
    assert len(filters) == 1


def test_build_filters_handles_date_range():
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 31)
    filters = list(build_filters({"created_from": start, "created_to": end}))
    assert len(filters) == 1
