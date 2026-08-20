"""Tests for sensitive data redacting in logging."""

import logging

from civitas_api.core.logging_security import SensitiveDataFilter, redact_sensitive_data


def test_redact_sensitive_data_patterns() -> None:
    # Test Bearer token redaction
    sample_auth = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    redacted = redact_sensitive_data(sample_auth)
    assert "Bearer [REDACTED]" in redacted
    assert "eyJhbGci" not in redacted

    # Test password redaction
    sample_pw = "connecting with password='my-secret-password-123' to db"
    redacted_pw = redact_sensitive_data(sample_pw)
    assert "[REDACTED]" in redacted_pw
    assert "my-secret-password-123" not in redacted_pw

    # Test api_key redaction
    sample_key = "api_key = 'gsk_1234567890abcdef'"
    redacted_key = redact_sensitive_data(sample_key)
    assert "[REDACTED]" in redacted_key
    assert "gsk_1234567890abcdef" not in redacted_key


def test_sensitive_data_logging_filter() -> None:
    sec_filter = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User authenticated with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
        args=(),
        exc_info=None,
    )
    sec_filter.filter(record)
    assert "Bearer [REDACTED]" in record.msg
    assert "eyJhbGci" not in record.msg
