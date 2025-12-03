"""Telephony provider configuration types.

Defines provider type enums used for configuration and factory selection.
"""

from enum import Enum


class TelephonyProviderType(str, Enum):
    """Available telephony providers."""

    TELNYX = "telnyx"
    # Future providers:
    # TWILIO = "twilio"
    # VONAGE = "vonage"
