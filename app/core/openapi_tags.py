"""Auto-generate OpenAPI tags and x-tagGroups from registered routes."""

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


class TagGroup(str, Enum):
    """Top-level tag groups for organizing API endpoints."""

    CORE = "Core"
    FEATURES = "Features"
    LIB = "Lib"
    INTEGRATION = "Integration"
    EXTENSIONS = "Extensions"


# Static core tags that don't come from auto-discovered modules
CORE_TAGS: dict[str, dict] = {
    "Health": {"description": "Health check and status endpoints", "group": TagGroup.CORE},
    "Examples": {"description": "Example CRUD operations", "group": TagGroup.CORE},
    "Tasks": {"description": "Celery background task management", "group": TagGroup.CORE},
    "Webhooks": {"description": "Webhook endpoints for external integrations", "group": TagGroup.CORE},
}

# Tag description prefixes by group
_GROUP_PREFIXES: dict[TagGroup, str] = {
    TagGroup.FEATURES: "📦",
    TagGroup.LIB: "📚",
    TagGroup.INTEGRATION: "🔗",
    TagGroup.EXTENSIONS: "🔌",
    TagGroup.CORE: "⚙️",
}

# Logical ordering for tag groups display
_GROUP_ORDER: list[TagGroup] = [
    TagGroup.CORE,
    TagGroup.FEATURES,
    TagGroup.LIB,
    TagGroup.INTEGRATION,
    TagGroup.EXTENSIONS,
]


def _infer_group_from_path(path: str) -> TagGroup:
    """Infer tag group from route path prefix."""
    if "/features/" in path:
        return TagGroup.FEATURES
    if "/integrations/" in path:
        return TagGroup.INTEGRATION
    if "/lib/" in path:
        return TagGroup.LIB
    if "/extensions/" in path:
        return TagGroup.EXTENSIONS
    return TagGroup.CORE


def _format_tag_name(tag: str) -> str:
    """Format tag name for display (Title Case with spaces)."""
    if " " in tag or tag[0].isupper():
        return tag
    return tag.replace("_", " ").replace("-", " ").title()


def get_openapi_tags_from_routes(app: "FastAPI") -> list[dict]:
    """Auto-discover all tags by scanning registered routes at OpenAPI schema generation time."""
    discovered_tags: dict[str, dict] = {}

    for route in app.routes:
        path = getattr(route, "path", "")
        tags = getattr(route, "tags", [])

        for tag in tags:
            if tag not in discovered_tags:
                if tag in CORE_TAGS:
                    discovered_tags[tag] = {
                        "name": tag,
                        "description": CORE_TAGS[tag]["description"],
                        "group": CORE_TAGS[tag]["group"],
                    }
                else:
                    group = _infer_group_from_path(path)
                    prefix = _GROUP_PREFIXES.get(group, "")
                    formatted = _format_tag_name(tag)
                    discovered_tags[tag] = {
                        "name": tag,
                        "description": f"{prefix} {formatted} endpoints",
                        "group": group,
                    }

    return [{"name": info["name"], "description": info["description"]} for info in discovered_tags.values()]


def get_tag_groups_from_routes(app: "FastAPI") -> list[dict]:
    """Generate x-tagGroups from auto-discovered tags, grouped by route path category."""
    groups: dict[TagGroup, list[str]] = {}

    for route in app.routes:
        path = getattr(route, "path", "")
        tags = getattr(route, "tags", [])

        for tag in tags:
            group = CORE_TAGS[tag]["group"] if tag in CORE_TAGS else _infer_group_from_path(path)
            if group not in groups:
                groups[group] = []
            if tag not in groups[group]:
                groups[group].append(tag)

    return [
        {"name": group.value, "tags": sorted(groups[group])}
        for group in _GROUP_ORDER
        if group in groups and groups[group]
    ]
