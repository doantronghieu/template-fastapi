"""Reusable library wrappers and framework customizations.

Custom adapters and abstractions around third-party libraries to streamline
development and provide consistent interfaces across the application.

Examples:
- Redis client wrappers with helper methods
- Storage/S3 abstraction layers
- Email service wrappers (SendGrid, SES, etc.)
- Caching utilities and decorators
- Custom middleware and exception handlers

Use this module for reusable library customizations that are used across
multiple services but aren't core infrastructure concerns.

Naming convention: Prefix private items with _ to exclude from exports.
"""
