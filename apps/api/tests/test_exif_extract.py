"""Unit tests for EXIF Geotag extraction and privacy sanitization."""

import io
from datetime import datetime
from PIL import Image, ExifTags
from civitas_api.operations.exif_extract import extract_and_sanitize_exif, _dms_to_decimal


def test_dms_to_decimal_conversion():
    # 28° 36' 50.04" N -> 28.6139
    d = (28, 1)
    m = (36, 1)
    s = (5004, 100)
    lat = _dms_to_decimal(d, m, s, "N")
    assert abs(lat - 28.6139) < 1e-4

    # 77° 12' 32.4" W -> -77.2090
    lon = _dms_to_decimal((77, 1), (12, 1), (324, 10), "W")
    assert abs(lon - (-77.2090)) < 1e-4


def test_extract_and_sanitize_no_exif():
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    res = extract_and_sanitize_exif(raw_bytes, "image/jpeg")
    assert res.has_exif is False
    assert res.latitude is None
    assert res.longitude is None
    assert res.stripped_tags_count == 0
    assert len(res.cleaned_bytes) > 0


def test_extract_and_sanitize_with_privacy_tags():
    img = Image.new("RGB", (100, 100), color="green")
    exif = img.getexif()
    # Add Make (0x010f), Model (0x0110), DateTime (0x0132)
    exif[0x010F] = "Apple"
    exif[0x0110] = "iPhone 15 Pro Max Serial #12345XYZ"
    exif[0x0132] = "2026:08:20 14:30:00"

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    raw_bytes = buf.getvalue()

    res = extract_and_sanitize_exif(raw_bytes, "image/jpeg")
    assert res.has_exif is True
    assert res.captured_at == datetime(2026, 8, 20, 14, 30, 0)
    assert res.stripped_tags_count >= 2

    # Verify that Make and Model are removed from cleaned image
    with Image.open(io.BytesIO(res.cleaned_bytes)) as cleaned_img:
        cleaned_exif = cleaned_img.getexif()
        assert 0x010F not in cleaned_exif
        assert 0x0110 not in cleaned_exif
