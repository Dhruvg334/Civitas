"""Classical visual measurements (Phase 3).

Real pixel statistics computed with numpy; nothing here is a language-model
guess. Each named feature is a documented measurement used downstream by the
classifier and the evidence rules:

    blur / edge energy:
      laplacian_variance         variance of 3x3 Laplacian (sharpness)
      edge_density               share of pixels with strong gradient
      vertical_edge_ratio        share of strong edges that are near-vertical
                                 (tree trunks, poles)
      flow_edge_ratio            share of strong edges that are near-horizontal
                                 (flowing water surface)
    photometric / color:
      luminance_mean, luminance_std
      saturation_mean, saturation_std
      hue_variance               variance of hue over the frame
      blue_dominance             mean(B) - 0.5*(mean(R)+mean(G)), /255
      blue_smooth_share          share of blue-dominant low-texture pixels
                                 (standing water)
      color_scatter              saturation_std^2 * hue_variance (garbage piles)
      bright_peak_mean           mean of the top 1% brightest pixels (streetlight)
      bright_upper_share         share of the bright peak in the upper half
                                 (streetlight bulb / sign)
      dark_lowtexture_share      share of dark, low-texture pixels (pothole
                                 cavity, shadowed piles)
      contrast_ratio             luminance_std / luminance_mean

Measurements run on a normalized 128x128 working frame; thresholds live in
the classifier/evidence modules and are calibration candidates, not facts.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from civitas_vision.quality import _grayscale, _saturation, to_rgb_array

FEATURE_NAMES: tuple[str, ...] = (
    "laplacian_variance",
    "edge_density",
    "vertical_edge_ratio",
    "flow_edge_ratio",
    "flow_blue_ratio",
    "band_dark_ratio",
    "luminance_mean",
    "luminance_std",
    "saturation_mean",
    "saturation_std",
    "hue_variance",
    "blue_dominance",
    "green_dominance",
    "blue_smooth_share",
    "color_scatter",
    "bright_peak_mean",
    "bright_upper_share",
    "dark_lowtexture_share",
    "contrast_ratio",
)

_EDGE_THRESHOLD = 0.08
_DARK_LEVEL = 0.20
_SMOOTH_GRADIENT = 0.04
_BLUE_BIAS = 0.08
_HUE_EPS = 1e-6

# Strong horizontal banding within blue-dominant regions: flowing water
# surface ripples (gy-dominant). Banding in dark pixels: recumbent trunks.
_FLOW_EDGE_RATIO = 2.0
_VERTICAL_EDGE_RATIO = 2.0


def _gradient_magnitude(gray: np.ndarray) -> np.ndarray:
    """Same-shape gradient magnitude via padded central differences."""
    g = np.pad(gray.astype(np.float64), 1, mode="edge")
    dx = g[1:-1, 2:] - g[1:-1, :-2]
    dy = g[2:, 1:-1] - g[:-2, 1:-1]
    return np.sqrt(dx**2 + dy**2)


def _laplacian_variance(gray: np.ndarray) -> float:
    g = gray.astype(np.float64)
    up = g[:-2, 1:-1]
    down = g[2:, 1:-1]
    left = g[1:-1, :-2]
    right = g[1:-1, 2:]
    center = g[1:-1, 1:-1]
    lap = 4.0 * center - (up + down + left + right)
    return float(np.var(lap))


def _hue(arr: np.ndarray) -> np.ndarray:
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    delta = mx - mn
    hue = np.zeros_like(mx)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mask = delta > _HUE_EPS
    np.copyto(hue, np.mod(60.0 * (g - b) / np.maximum(delta, _HUE_EPS), 360.0), where=mask & (mx == r))
    np.copyto(hue, np.mod(60.0 * (b - r) / np.maximum(delta, _HUE_EPS) + 120.0, 360.0), where=mask & (mx == g))
    np.copyto(hue, np.mod(60.0 * (r - g) / np.maximum(delta, _HUE_EPS) + 240.0, 360.0), where=mask & (mx == b))
    return hue


def extract_features(image: Image.Image) -> dict[str, float]:
    """Compute the full documented measurement set for one image."""
    arr = to_rgb_array(image)
    gray = _grayscale(arr)
    sat = _saturation(arr)
    mag = _gradient_magnitude(gray)

    strong_edges = mag > _EDGE_THRESHOLD
    edge_density = float(strong_edges.mean())

    g = np.pad(gray.astype(np.float64), 1, mode="edge")
    gx = g[1:-1, 2:] - g[1:-1, :-2]
    gy = g[2:, 1:-1] - g[:-2, 1:-1]
    if edge_density > 0.0:
        vertical_edge_ratio = float((strong_edges & (np.abs(gy) > _VERTICAL_EDGE_RATIO * np.abs(gx))).mean() / edge_density)
        flow_edge_ratio = float((strong_edges & (np.abs(gx) > _FLOW_EDGE_RATIO * np.abs(gy))).mean() / edge_density)
    else:
        vertical_edge_ratio = 0.0
        flow_edge_ratio = 0.0

    blue_dominant = (arr[:, :, 2] - arr[:, :, 0] > _BLUE_BIAS) & (
        arr[:, :, 2] - arr[:, :, 1] > _BLUE_BIAS
    )
    # Flowing water: horizontal ripple banding (strong gy) inside blue regions.
    flow_in_blue = strong_edges & blue_dominant & (np.abs(gy) > 2.0 * np.abs(gx))
    flow_blue_ratio = float(flow_in_blue.mean() / max(float(blue_dominant.mean()), 1e-6))
    # Recumbent objects (tree trunk): horizontal banding (strong gy) in dark
    # pixels.
    dark_mask = gray < _DARK_LEVEL * 2.0
    band_in_dark = strong_edges & dark_mask & (np.abs(gy) > 2.0 * np.abs(gx))
    band_dark_ratio = float(band_in_dark.mean() / max(float(dark_mask.mean()), 1e-6))

    bright_peak = np.percentile(gray, 99.0)
    bright_peak_mask = gray >= bright_peak
    bright_peak_mean = float(gray[bright_peak_mask].mean())
    h, _ = gray.shape
    bright_upper_share = float(
        bright_peak_mask[: h // 2, :].sum() / max(float(bright_peak_mask.sum()), 1.0)
    )

    hue = _hue(arr)
    dark_lowtexture = (gray < _DARK_LEVEL) & (mag < _SMOOTH_GRADIENT)
    blue_smooth_share = float((blue_dominant & (mag < _SMOOTH_GRADIENT * 3.0)).mean())

    features: dict[str, float] = {
        "laplacian_variance": _laplacian_variance(gray),
        "edge_density": edge_density,
        "vertical_edge_ratio": vertical_edge_ratio,
        "flow_edge_ratio": flow_edge_ratio,
        "flow_blue_ratio": flow_blue_ratio,
        "band_dark_ratio": band_dark_ratio,
        "luminance_mean": float(gray.mean()),
        "luminance_std": float(gray.std()),
        "saturation_mean": float(sat.mean()),
        "saturation_std": float(sat.std()),
        "hue_variance": float(hue.std() ** 2),
        "blue_dominance": float(
            arr[:, :, 2].mean() - 0.5 * (arr[:, :, 0].mean() + arr[:, :, 1].mean())
        ),
        "green_dominance": float(
            arr[:, :, 1].mean() - 0.5 * (arr[:, :, 0].mean() + arr[:, :, 2].mean())
        ),
        "blue_smooth_share": blue_smooth_share,
        "color_scatter": float(sat.std() ** 2 * hue.std() ** 2),
        "bright_peak_mean": bright_peak_mean,
        "bright_upper_share": bright_upper_share,
        "dark_lowtexture_share": float(dark_lowtexture.mean()),
        "contrast_ratio": float(gray.std() / max(gray.mean(), 1e-6)),
    }
    return {k: round(float(v), 6) for k, v in features.items()}


__all__ = ["FEATURE_NAMES", "extract_features"]