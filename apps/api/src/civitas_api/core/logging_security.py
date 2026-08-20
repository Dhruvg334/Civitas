"""Security logging filter for redacting credentials and tokens from log messages."""

import logging
import re

# Patterns matching sensitive keys and tokens
_SECRET_PATTERNS = [
    re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
    re.compile(r"(password\s*[:=]\s*['\"]?)[^'\",\s]+", re.IGNORECASE),
    re.compile(r"(secret\s*[:=]\s*['\"]?)[^'\",\s]+", re.IGNORECASE),
    re.compile(r"(api[_-]?key\s*[:=]\s*['\"]?)[^'\",\s]+", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
]


def redact_sensitive_data(text: str) -> str:
    """Mask credentials and tokens in a string."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        if pattern.groups > 0:
            sanitized = pattern.sub(r"\g<1>[REDACTED]", sanitized)
        else:
            sanitized = pattern.sub("[REDACTED_KEY]", sanitized)
    return sanitized


class SensitiveDataFilter(logging.Filter):
    """Logging filter that sanitizes record messages and arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_sensitive_data(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def install_security_logging() -> None:
    """Attach the sensitive data filter to the root logger handlers."""
    root_logger = logging.getLogger()
    security_filter = SensitiveDataFilter()
    for handler in root_logger.handlers:
        handler.addFilter(security_filter)
