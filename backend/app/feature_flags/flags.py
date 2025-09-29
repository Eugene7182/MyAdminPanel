"""Feature flag toggles."""
from __future__ import annotations

from app.core.settings import settings


class FeatureFlags:
    ENABLE_BONUSES = settings.enable_bonuses
    ENABLE_MESSAGES = settings.enable_messages


flags = FeatureFlags()
