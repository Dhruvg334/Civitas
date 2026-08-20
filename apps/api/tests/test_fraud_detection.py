"""Unit tests for contractor fraud, perceptual dHash, and EXIF spoofing detection."""

import io
from datetime import datetime, timedelta
from PIL import Image
from civitas_ml.fraud_detection import (
    compute_difference_hash,
    compute_hamming_distance,
    verify_contractor_resolution_media,
)


def _create_test_image(color: str, size: tuple[int, int] = (100, 100)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_dhash_identical_images():
    img_bytes = _create_test_image("red")
    h1 = compute_difference_hash(img_bytes)
    h2 = compute_difference_hash(img_bytes)
    assert h1 == h2
    assert compute_hamming_distance(h1, h2) == 0


def test_dhash_different_images():
    img_red = _create_test_image("red")
    img_blue = _create_test_image("blue")
    h1 = compute_difference_hash(img_red)
    h2 = compute_difference_hash(img_blue)
    # Different colors/gradients should produce valid hashes
    assert isinstance(h1, str)
    assert isinstance(h2, str)


def test_verify_resolution_media_identical_fraud():
    img_bytes = _create_test_image("gray")
    wo_created = datetime(2026, 8, 20, 10, 0, 0)
    after_captured = datetime(2026, 8, 20, 12, 0, 0)

    res = verify_contractor_resolution_media(
        before_image_bytes=img_bytes,
        after_image_bytes=img_bytes,  # Same photo!
        work_order_created_at=wo_created,
        after_photo_captured_at=after_captured,
        incident_latitude=20.29614,
        incident_longitude=85.82451,
        after_photo_latitude=20.29614,
        after_photo_longitude=85.82451,
    )
    assert res.is_fraudulent is True
    assert any(v.code == "FRAUD_IDENTICAL_MEDIA" for v in res.violations)


def test_verify_resolution_media_stale_timestamp_fraud():
    before_img = _create_test_image("black")
    after_img = _create_test_image("white")
    wo_created = datetime(2026, 8, 20, 15, 0, 0)
    after_captured = datetime(2026, 8, 20, 10, 0, 0)  # Captured BEFORE dispatch!

    res = verify_contractor_resolution_media(
        before_image_bytes=before_img,
        after_image_bytes=after_img,
        work_order_created_at=wo_created,
        after_photo_captured_at=after_captured,
        incident_latitude=20.29614,
        incident_longitude=85.82451,
        after_photo_latitude=20.29614,
        after_photo_longitude=85.82451,
    )
    assert res.is_fraudulent is True
    assert any(v.code == "FRAUD_STALE_PHOTO" for v in res.violations)


def test_verify_resolution_media_geo_mismatch_fraud():
    before_img = _create_test_image("black")
    after_img = _create_test_image("white")
    wo_created = datetime(2026, 8, 20, 10, 0, 0)
    after_captured = datetime(2026, 8, 20, 12, 0, 0)

    res = verify_contractor_resolution_media(
        before_image_bytes=before_img,
        after_image_bytes=after_img,
        work_order_created_at=wo_created,
        after_photo_captured_at=after_captured,
        incident_latitude=20.29614,
        incident_longitude=85.82451,
        after_photo_latitude=28.61390,  # 1200km away in Delhi!
        after_photo_longitude=77.20900,
    )
    assert res.is_fraudulent is True
    assert any(v.code == "FRAUD_GEO_MISMATCH" for v in res.violations)


def test_verify_corrupted_image_handling():
    corrupted_bytes = b"CORRUPTED_RAW_NON_IMAGE_DATA_BYTES"
    valid_bytes = _create_test_image("blue")
    wo_created = datetime(2026, 8, 20, 10, 0, 0)

    res = verify_contractor_resolution_media(
        before_image_bytes=corrupted_bytes,
        after_image_bytes=valid_bytes,
        work_order_created_at=wo_created,
    )
    assert isinstance(res.is_fraudulent, bool)
    assert isinstance(res.dhash_hamming_distance, int)
