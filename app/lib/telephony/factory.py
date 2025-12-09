"""Telephony provider factory for runtime provider selection.

Implements the Strategy pattern by selecting the appropriate telephony provider
based on application configuration.
"""

from collections.abc import Callable
from typing import Annotated

from app.core.autodiscover import ModuleType, require_module
from app.lib.telephony.base import TelephonyProvider
from app.lib.telephony.config import TelephonyProviderType


_DEFAULT_PROVIDER = TelephonyProviderType.TELNYX


def get_telephony_provider(
    provider_type: Annotated[
        TelephonyProviderType | None, "Provider type override, defaults to Telnyx"
    ] = None,
) -> TelephonyProvider:
    """Get the configured telephony provider."""
    provider_type = provider_type or _DEFAULT_PROVIDER

    providers: dict[str, Callable[[], TelephonyProvider]] = {
        TelephonyProviderType.TELNYX.value: _get_telnyx_provider,
    }

    provider_factory = providers.get(provider_type.value)
    if not provider_factory:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown telephony provider: {provider_type}. Available: {available}"
        )

    return provider_factory()


@require_module(ModuleType.INTEGRATIONS, "telnyx")
def _get_telnyx_provider() -> TelephonyProvider:
    """Get cached Telnyx telephony provider."""
    from app.integrations.telnyx.provider import get_telephony_provider

    return get_telephony_provider()
