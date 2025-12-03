"""FastAPI dependencies for telephony providers.

Provides dependency injection for telephony providers in API endpoints.
"""

from typing import Annotated

from fastapi import Depends

from app.lib.telephony.base import TelephonyProvider
from app.lib.telephony.factory import get_telephony_provider

TelephonyProviderDep = Annotated[TelephonyProvider, Depends(get_telephony_provider)]
