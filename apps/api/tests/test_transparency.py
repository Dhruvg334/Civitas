"""Unit tests for differential privacy spatial jitter and PII redaction."""

from civitas_knowledge.transparency import apply_differential_privacy_jitter, redact_pii_text


def test_redact_pii_phone_and_email():
    raw = "Citizen John reported burst pipe at Flat 402, call me on +91 9876543210 or email john.doe@example.com."
    sanitized = redact_pii_text(raw)
    assert "+91 9876543210" not in sanitized
    assert "john.doe@example.com" not in sanitized
    assert "Flat 402" not in sanitized
    assert "[PHONE_REDACTED]" in sanitized
    assert "[EMAIL_REDACTED]" in sanitized
    assert "[ADDRESS_REDACTED]" in sanitized


def test_redact_pii_vehicle_plate():
    raw = "Car with license plate KA 05 MH 1234 hit the streetlight pole."
    sanitized = redact_pii_text(raw)
    assert "KA 05 MH 1234" not in sanitized
    assert "[VEHICLE_PLATE_REDACTED]" in sanitized


def test_differential_privacy_jitter_bounding():
    raw_lat, raw_lon = 20.29614, 85.82451
    jit_lat, jit_lon = apply_differential_privacy_jitter(raw_lat, raw_lon, seed_key="test-123", epsilon_meters=25.0)

    # Calculate distance between raw and jittered
    from civitas_ml.fraud_detection import _haversine_meters

    dist = _haversine_meters(raw_lat, raw_lon, jit_lat, jit_lon)
    assert 0.0 <= dist <= 50.0  # Bounded within 2 * epsilon
    assert (jit_lat, jit_lon) != (raw_lat, raw_lon)


def test_differential_privacy_jitter_deterministic():
    # Same seed should produce identical coordinates
    j1 = apply_differential_privacy_jitter(20.29614, 85.82451, seed_key="same-seed")
    j2 = apply_differential_privacy_jitter(20.29614, 85.82451, seed_key="same-seed")
    assert j1 == j2
