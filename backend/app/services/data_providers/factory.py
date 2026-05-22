"""DataProvider factory — picks the right implementation from settings."""
from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings
from app.services.data_providers.base import DataProvider
from app.services.data_providers.demo import DemoDataProvider

logger = logging.getLogger(__name__)


@lru_cache
def get_data_provider() -> DataProvider:
    """Return the configured DataProvider singleton.

    Selection rule: ``settings.data_provider`` ∈ {"demo", "salesforce"}.
    Defaults to "demo" so the app is demonstrable out-of-the-box.
    """
    settings = get_settings()
    mode = (settings.data_provider or "demo").lower()
    if mode == "salesforce":
        # Lazy import — simple_salesforce is only required when actually used
        from app.services.data_providers.salesforce import SalesforceDataProvider
        logger.info("DataProvider = Salesforce (live OAuth)")
        return SalesforceDataProvider()
    if mode != "demo":
        logger.warning("Unknown DATA_PROVIDER=%r, falling back to 'demo'", mode)
    logger.info("DataProvider = Demo (deterministic in-memory)")
    return DemoDataProvider()
