"""Telephony provider abstraction layer.

Defines interfaces for telephony providers (PSTN, SIP, call control),
enabling runtime provider switching via the Strategy pattern.

See docs/patterns/libraries.md for architecture details.
"""

from app.lib.telephony.base import TelephonyProvider
from app.lib.telephony.factory import get_telephony_provider

__all__ = ["TelephonyProvider", "get_telephony_provider"]
