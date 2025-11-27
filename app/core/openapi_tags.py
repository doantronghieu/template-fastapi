"""Centralized OpenAPI tag registry for API documentation.

Single source of truth for all API tags, their descriptions, and grouping.
Auto-generates OpenAPI tags metadata and x-tagGroups for nested navigation.
"""

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


class TagGroup(str, Enum):
    """Top-level tag groups for organizing API endpoints."""

    CORE = "Core"
    LIB = "Lib"
    INTEGRATION = "Integration"
    EXTENSIONS = "Extensions"


class APITag(str, Enum):
    """API endpoint tags - use these in router decorators for type safety."""

    # Core tags
    HEALTH = "Health"
    EXAMPLES = "Examples"
    MESSAGING = "Messaging"
    TASKS = "Tasks"
    USERS = "Users"
    WEBHOOKS = "Webhooks"
    DOCUMENTS = "Documents"

    # Lib tags
    LLM = "LLM"
    LANGCHAIN = "LangChain"

    # Integration tags
    MESSENGER = "Messenger"
    GMAIL = "Gmail"


# Tag metadata: description and group assignment
TAG_METADATA: dict[APITag, dict] = {
    # Core
    APITag.HEALTH: {
        "description": "Health check and status endpoints",
        "group": TagGroup.CORE,
    },
    APITag.EXAMPLES: {
        "description": "Example CRUD operations",
        "group": TagGroup.CORE,
    },
    APITag.MESSAGING: {
        "description": "Messaging system endpoints",
        "group": TagGroup.CORE,
    },
    APITag.TASKS: {
        "description": "Celery background task management",
        "group": TagGroup.CORE,
    },
    APITag.USERS: {
        "description": "User management and details",
        "group": TagGroup.CORE,
    },
    APITag.WEBHOOKS: {
        "description": "Webhook endpoints for external integrations",
        "group": TagGroup.CORE,
    },
    APITag.DOCUMENTS: {
        "description": "Document conversion to markdown",
        "group": TagGroup.CORE,
    },
    # Integration
    APITag.MESSENGER: {
        "description": "Facebook Messenger API operations",
        "group": TagGroup.INTEGRATION,
    },
    APITag.GMAIL: {
        "description": "Gmail IMAP integration for searching emails",
        "group": TagGroup.INTEGRATION,
    },
    # Lib
    APITag.LLM: {
        "description": "LLM provider-agnostic test endpoints",
        "group": TagGroup.LIB,
    },
    APITag.LANGCHAIN: {
        "description": "LangChain library-specific endpoints",
        "group": TagGroup.LIB,
    },
}


def get_openapi_tags() -> list[dict]:
    """Generate OpenAPI tags metadata from TAG_METADATA.

    Returns:
        List of tag dictionaries for FastAPI openapi_tags parameter
    """
    return [
        {"name": tag.value, "description": meta["description"]}
        for tag, meta in TAG_METADATA.items()
    ]


def get_extension_tags_from_routes(app: "FastAPI") -> list[dict]:
    """Auto-discover extension tags by scanning registered routes.

    Called once at OpenAPI schema generation (lazy evaluation).
    Scans all routes under /api/extensions/ prefix and extracts unique tags.

    Args:
        app: FastAPI application instance with registered routes

    Returns:
        List of tag dictionaries with auto-generated descriptions
    """
    extension_tags = set()

    for route in app.routes:
        if hasattr(route, "path") and "/extensions/" in route.path:
            tags = getattr(route, "tags", [])
            extension_tags.update(tags)

    return [
        {"name": tag, "description": f"🔌 {tag} features"}
        for tag in sorted(extension_tags)
    ]


def get_tag_groups_from_routes(app: "FastAPI") -> list[dict]:
    """Generate x-tagGroups including auto-discovered extension tags.

    Args:
        app: FastAPI application instance

    Returns:
        List of tag group dictionaries for x-tagGroups extension
    """
    groups: dict[TagGroup, list[str]] = {}
    for tag, meta in TAG_METADATA.items():
        group = meta["group"]
        if group not in groups:
            groups[group] = []
        groups[group].append(tag.value)

    tag_groups = [{"name": group.value, "tags": tags} for group, tags in groups.items()]

    extension_tag_dicts = get_extension_tags_from_routes(app)
    if extension_tag_dicts:
        extension_tag_names = [tag_dict["name"] for tag_dict in extension_tag_dicts]
        tag_groups.append(
            {"name": TagGroup.EXTENSIONS.value, "tags": extension_tag_names}
        )

    return tag_groups
