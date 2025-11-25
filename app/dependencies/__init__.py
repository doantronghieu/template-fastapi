"""Centralized dependency injection providers."""

# Core infrastructure dependencies
from app.dependencies.core import (
    RedisDep,
    SessionDep,
    SettingsDep,
    get_redis_client,
    get_session,
    get_settings,
    verify_api_key,
)

# API-layer dependencies
from app.dependencies.api import PaginationParams

__all__ = [
    # Core dependencies
    "SessionDep",
    "SettingsDep",
    "RedisDep",
    "get_session",
    "get_settings",
    "get_redis_client",
    "verify_api_key",
    # API dependencies
    "PaginationParams",
]
