"""Centralized OpenAPI tag registry for API documentation.

Single source of truth for all API tags, their descriptions, and grouping.
Auto-generates OpenAPI tags metadata and x-tagGroups for nested navigation.
"""

from enum import Enum


class TagGroup(str, Enum):
    """Top-level tag groups for organizing API endpoints."""

    CORE = "Core"
    LIB = "Lib"
    EXTENSIONS = "Extensions"


class APITag(str, Enum):
    """API endpoint tags - use these in router decorators for type safety."""

    # Core tags
    HEALTH = "Health"
    EXAMPLES = "Examples"
    MESSAGING = "Messaging"
    TASKS = "Tasks"

    # Lib tags
    LLM = "LLM"
    LANGCHAIN = "LangChain"


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


def get_openapi_tags(extension_tags: list[str] | None = None) -> list[dict]:
    """Generate OpenAPI tags metadata from TAG_METADATA.

    Args:
        extension_tags: Optional list of extension tag names to append

    Returns:
        List of tag dictionaries for FastAPI openapi_tags parameter
    """
    tags = [
        {"name": tag.value, "description": meta["description"]}
        for tag, meta in TAG_METADATA.items()
    ]

    # Add extension tags dynamically
    if extension_tags:
        for ext_name in extension_tags:
            tags.append(
                {
                    "name": ext_name,
                    "description": f"🔌 {ext_name.lower().replace(' ', '_')} extension features",
                }
            )

    return tags


def get_tag_groups(extension_tags: list[str] | None = None) -> list[dict]:
    """Generate x-tagGroups for nested navigation in API docs.

    Groups tags by their assigned TagGroup from TAG_METADATA.

    Args:
        extension_tags: Optional list of extension tag names to group

    Returns:
        List of tag group dictionaries for x-tagGroups extension
    """
    # Group tags by their assigned group
    groups: dict[TagGroup, list[str]] = {}
    for tag, meta in TAG_METADATA.items():
        group = meta["group"]
        if group not in groups:
            groups[group] = []
        groups[group].append(tag.value)

    # Convert to x-tagGroups format
    tag_groups = [{"name": group.value, "tags": tags} for group, tags in groups.items()]

    # Add extensions group if extensions exist
    if extension_tags:
        tag_groups.append({"name": TagGroup.EXTENSIONS.value, "tags": extension_tags})

    return tag_groups
