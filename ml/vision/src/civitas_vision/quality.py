"""Media quality checks (Phase 3).

Classical, measurable gating before any classification runs:

- blur: variance of the 3x3 Laplacian on a downscaled grayscale frame;
  higher variance = sharper image. Dark, textureless scenes score low, so
  bright-scene dead zones are treated conservatively (see `reasons`).
- exposure: mean luminance; near-black and near-white frames are unusable.
- saturation: mean HSV saturation; a nearly monochrome image carries little
  color evidence (kept as a warning, not a hard rejection).
- resolution: too-small frames are rejected.

Every verdict lists the concrete measurements behind it.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from civitas_vision.contracts import SceneQuality

MIN_WIDTH_PX = 64
MIN_HEIGHT_PX = 64
MAX_BLUR_SCORE = 0.001    # variance-of-Laplacian below this = too blurry
                          # (calibrated on the synthetic quality set: sharp
                          # frames >= 0.0028, radius-4 Gaussian blur <= 0.0001;
                          # 0.001 keeps margin on both sides)
MIN_LUMINANCE = 0.02      # near-black
MAX_LUMINANCE = 0.98      # near-white
MIN_SATURATION_WARN = 0.04  # below this the frame is near-monochrome

_WORK_SIZE = 128


def to_rgb_array(image: Image.Image) -> np.ndarray:
    """Convert a PIL image to a float RGB array in [0, 1]."""
    rgb = image.convert("RGB").resize(
        (_WORK_SIZE, _WORK_SIZE), Image.Resampling.BILINEAR
    )
    return np.asarray(rgb, dtype=np.float64) / 255.0


def _grayscale(arr: np.ndarray) -> np.ndarray:
    return 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]


def _saturation(arr: np.ndarray) -> np.ndarray:
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    denom = np.maximum(mx, 1e-6)
    return (mx - mn) / denom


def laplacian_variance(gray: np.ndarray) -> float:
    """Variance of the 3x3 Laplacian (blur/sharpness measure)."""
    g = gray.astype(np.float64)
    up = g[:-2, 1:-1]
    down = g[2:, 1:-1]
    left = g[1:-1, :-2]
    right = g[1:-1, 2:]
    center = g[1:-1, 1:-1]
    lap = 4.0 * center - (up + down + left + right)
    return float(np.var(lap))


def _blur_reason(blur: float) -> str:
    return (
        f"variance of Laplacian {blur:.4f} on normalized [0,1] grayscale "
        f"(threshold {MAX_BLUR_SCORE:.4f}); "
        f"{'sharp enough' if blur >= MAX_BLUR_SCORE else 'motion/defocus blur suspected'}"
    )


def assess_quality(image: Image.Image, width_px: int | None = None, height_px: int | None = None) -> SceneQuality:
    """Assess one image/frame. All thresholds are documented in this module."""
    w = width_px if width_px is not None else image.width
    h = height_px if height_px is not None else image.height
    arr = to_rgb_array(image)
    gray = _grayscale(arr)
    sat = _saturation(arr)
    blur_score = laplacian_variance(gray)
    lum_mean = float(gray.mean())
    sat_mean = float(sat.mean())

    reasons: list[str] = []
    basis = [_blur_reason(blur_score)]
    usable = True

    if w < MIN_WIDTH_PX or h < MIN_HEIGHT_PX:
        reasons.append(f"resolution {w}x{h}px below minimum {MIN_WIDTH_PX}x{MIN_HEIGHT_PX}px")
        usable = False
    if blur_score < MAX_BLUR_SCORE:
        reasons.append(f"blurry: variance of Laplacian {blur_score:.4f} < {MAX_BLUR_SCORE:.4f}")
        usable = False
    if lum_mean < MIN_LUMINANCE:
        reasons.append(f"near-black frame: mean luminance {lum_mean:.3f}")
        usable = False
    if lum_mean > MAX_LUMINANCE:
        reasons.append(f"over-exposed frame: mean luminance {lum_mean:.3f}")
        usable = False
    if sat_mean < MIN_SATURATION_WARN:
        reasons.append(
            f"near-monochrome: saturation {sat_mean:.3f}; color evidence weak "
            "(kept for shape/texture classification)"
        )
    if not reasons:
        reasons.append("resolution, sharpness and exposure checks passed")

    return SceneQuality(
        usable=usable,
        width_px=w,
        height_px=h,
        blur_score=round(blur_score, 3),
        luminance_mean=round(lum_mean, 3),
        saturation_mean=round(sat_mean, 3),
        reasons=reasons,
        basis=basis,
    )