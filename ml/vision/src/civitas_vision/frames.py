"""Video frame handling (Phase 3): extraction and key-frame selection.

A citizen's short video is reduced to a small set of usable frames:

0. acquire frames (from an iterable of PIL images, or from a video file path
   via OpenCV — the `video` extra; clean error if cv2 is missing),
1. quality-check each frame,
2. select the sharpest, well-exposed `top_k` frames as key frames.

Selection is deterministic: frames are ranked by (usable, sharpness,
luminance distance from mid-exposure), ties broken by earliest index.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from PIL import Image

from civitas_vision.contracts import FramePick, SceneQuality
from civitas_vision.quality import assess_quality

DEFAULT_TOP_K = 4
_FRAME_SCALE = 0.5  # video frames are downscaled before quality ranking


def frames_from_path(path: str, max_frames: int = 120) -> Iterator[Image.Image]:
    """Yield downscaled frames from a video file (OpenCV, optional extra)."""
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "Video decoding requires the 'civitas-vision[video]' extra "
            "(opencv-python-headless)."
        ) from exc
    cap = cv2.VideoCapture(path)  # type: ignore[attr-defined]
    try:
        count = 0
        while count < max_frames:
            ok, frame = cap.read()  # type: ignore[attr-defined]
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # type: ignore[attr-defined]
            img = Image.fromarray(rgb)
            img = img.resize(
                (max(1, int(img.width * _FRAME_SCALE)), max(1, int(img.height * _FRAME_SCALE))),
                Image.Resampling.BILINEAR,
            )
            count += 1
            yield img
    finally:
        cap.release()  # type: ignore[attr-defined]


def select_key_frames(
    frames: Iterable[Image.Image], top_k: int = DEFAULT_TOP_K
) -> list[FramePick]:
    """Deterministic key-frame selection by quality ranking."""
    ranked: list[tuple[float, int, SceneQuality]] = []
    for index, image in enumerate(frames):
        quality = assess_quality(image)
        if not quality.usable:
            continue
        sharpness = quality.blur_score
        exposure_grade = 1.0 - abs(quality.luminance_mean - 0.5)
        score = sharpness * 1.0 + exposure_grade * 10.0
        ranked.append((score, index, quality))
    ranked.sort(key=lambda entry: (-entry[0], entry[1]))
    return [
        FramePick(index=index, quality=quality)
        for _, index, quality in ranked[:top_k]
    ]


__all__ = ["DEFAULT_TOP_K", "frames_from_path", "select_key_frames"]