"""Redact secrets from captured streams."""

from __future__ import annotations

import re

_BEGIN_END = re.compile(
    r"-----BEGIN[^-]+-----.*?-----END[^-]+-----",
    re.DOTALL,
)
_SK = re.compile(r"sk-[A-Za-z0-9_-]+")
_AWS = re.compile(r"\bAWS_[A-Z0-9_]+\b")
_TOKEN_IDENT = re.compile(r"\b[A-Za-z0-9_]{0,40}TOKEN[A-Za-z0-9_]*\b", re.IGNORECASE)
_TOKEN_ASSIGN = re.compile(r"(?i)\btoken\s*[=:]\s*\S+")


def redact(text: str) -> str:
    text = _BEGIN_END.sub("[REDACTED]", text)
    text = _SK.sub("[REDACTED]", text)
    text = _AWS.sub("[REDACTED]", text)
    text = _TOKEN_ASSIGN.sub("token=[REDACTED]", text)
    text = _TOKEN_IDENT.sub("[REDACTED]", text)
    return text
