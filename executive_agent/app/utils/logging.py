"""Logging helpers that respect the ENABLE_LOGS setting."""

import logging
import sys
from typing import Any

from app.config.settings import get_settings


def get_logger(name: str) -> logging.Logger:
    """Create a configured logger for application modules."""

    settings = get_settings()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO if settings.enable_logs else logging.CRITICAL)
    logger.propagate = False
    return logger


def redact_sensitive(payload: dict[str, Any]) -> dict[str, Any]:
    """Redact known secret-like keys before logging dictionaries."""

    redacted = dict(payload)
    for key in list(redacted.keys()):
        lowered = key.lower()
        if "secret" in lowered or "token" in lowered or "password" in lowered:
            redacted[key] = "***"
    return redacted
