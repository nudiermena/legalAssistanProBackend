"""
Helper utilities to resolve canonical source URLs from RAG records.
Prefers origin URLs stored in database rows.
"""

from typing import Any, Dict, Optional


PREFERRED_URL_KEYS = [
    "source_url",
    "origin_url",
    "original_url",
    "url",
]


def resolve_record_url(record: Dict[str, Any]) -> Optional[str]:
    """Return best available URL from a RAG record, if present.

    Looks through common fields used across tables: source_url, origin_url, original_url, url.
    """
    if not isinstance(record, dict):
        return None

    for key in PREFERRED_URL_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Try nested metadata
    meta = record.get("metadata")
    if isinstance(meta, dict):
        for key in PREFERRED_URL_KEYS:
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None





