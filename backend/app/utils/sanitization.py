"""Input sanitization utilities to prevent Cross-Site Scripting (XSS) and injection."""

from __future__ import annotations

import html
import re
from typing import Any

# Pattern matching dangerous tags and inline scripts
DANGEROUS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onload=, onerror=, etc.
]


def sanitize_text(value: Any) -> Any:
    """Sanitize string values by stripping script injections and escaping HTML entities."""
    if not isinstance(value, str):
        return value

    cleaned = value.strip()
    # Strip known malicious patterns
    for pat in DANGEROUS_PATTERNS:
        cleaned = pat.sub("", cleaned)

    # HTML escape any remaining angle brackets and quotes
    return html.escape(cleaned)


def sanitize_dict_strings(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize string values in a dictionary."""
    sanitized = {}
    for k, v in d.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_text(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict_strings(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_text(x) if isinstance(x, str) else x for x in v]
        else:
            sanitized[k] = v
    return sanitized
