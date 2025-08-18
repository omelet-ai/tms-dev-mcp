#!/usr/bin/env python3
"""
Provider-specific utilities for OpenAPI processing.
"""

from .models import PathPrefix, Provider


def get_provider_from_path(path: str) -> Provider:
    """
    Determine provider based on API path.

    Args:
        path: API endpoint path

    Returns:
        Provider enum
    """
    if path.startswith(PathPrefix.OMELET.value):
        return Provider.OMELET
    return Provider.INAVI
