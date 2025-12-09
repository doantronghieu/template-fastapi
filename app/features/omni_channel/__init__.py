"""Omni-channel feature - vertical slice for multi-channel messaging.

Contains models, service, workflows, and API for managing users,
conversations, and messages across channels (Telegram, WhatsApp, Messenger, etc.).
"""

# Re-exports are available but use direct imports for better clarity
__all__ = [
    "models",
    "service",
    "workflows",
    "schemas",
    "router",
]
