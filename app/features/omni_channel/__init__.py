"""Omni-channel feature - vertical slice for multi-channel messaging.

Contains models, services, handlers, and API for managing users,
conversations, and messages across channels (Telegram, WhatsApp, Messenger, etc.).

Import models, services, and handlers from their respective submodules
"""

# Re-exports are available but use direct imports for better clarity
__all__ = [
    # Submodules to import from directly
    "models",
    "services",
    "handlers",
    "schemas",
    "api",
]
