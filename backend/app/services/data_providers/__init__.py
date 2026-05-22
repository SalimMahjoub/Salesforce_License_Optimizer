"""Data providers: pluggable sources of Salesforce-like user data.

Two implementations:
- DemoDataProvider: deterministic fake org for offline demos / CI.
- SalesforceDataProvider: real OAuth + SOQL (requires credentials + simple-salesforce).

The Salesforce provider is imported lazily inside ``get_data_provider`` so
the demo path does not require the simple-salesforce dependency.
"""
from app.services.data_providers.base import CollectedSnapshot, DataProvider
from app.services.data_providers.demo import DemoDataProvider
from app.services.data_providers.factory import get_data_provider

__all__ = [
    "DataProvider",
    "CollectedSnapshot",
    "DemoDataProvider",
    "get_data_provider",
]
