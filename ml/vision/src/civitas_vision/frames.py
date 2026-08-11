"""Video frame handling (Phase 3): extraction and key-frame selection.

A citizen's short video is reduced to a small set of usable frames:

0. acquire frames (from an iterable of PIL images, or from a video file path
   via OpenCV — the `video` extra; clean error if cv2 is missing),
1. quality-check each frame,
2. select key frames with temporal coverage: the video is split into
   `top_k` equal time segments and the best-quality usable frame of each
   segment is picked, so an incident that appears mid- or late-clip is
   still represented (ranking the globally sharpest frames alone can miss
   the only frames that show the incident).

Selection is deterministic: per segment, frames are ranked by (usable,
sharpness, luminance distance from mid-exposure), ties broken by earliest
index. With `allow_degraded=True` (the zero-shot CLIP classifier, which
handles natural degraded frames) a segment whose frames all fail the
quality gate still contributes its best available frame — recorded with
its `quality.usable=False` — so video evidence that only exists in
degraded footage is not silently dropped. With `allow_degraded=False`
(the deterministic k-NN, trained on clean synthetic scenes) such segments
contribute nothing, and a video with *no* usable frames at all is always
rejected.
"""

from __future__ import annotations

import math
from typing import Iterable, Iterator

from PIL import Image

from civitas_vision.contracts import FramePick, SceneQuality
from civitas_vision.quality import assess_quality

DEFAULT_TOP_K = 4
# Bounded full-duration decode: short citizen clips (~10 s at 30 fps) are
# covered end-to-end instead of only their opening seconds.
MAX_FRAMES = 300
_FRAME_SCALE = 0.5  # video frames are downscaled before quality ranking


def frames_from_path(path: str, max_frames: int = MAX_FRAMES) -> Iterator[Image.Image]:
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


def _quality_score(quality: SceneQuality) -> float:
    sharpness = quality.blur_score
    exposure_grade = 1.0 - abs(quality.luminance_mean - 0.5)
    return sharpness * 1.0 + exposure_grade * 10.0


def select_key_frames(
    frames: Iterable[Image.Image],
    top_k: int = DEFAULT_TOP_K,
    allow_degraded: bool = True,
) -> list[FramePick]:
    """Deterministic key-frame selection: best quality per time segment.

    Pass 1 picks the best-quality *usable* frame of each time segment.
    Pass 2 (when `allow_degraded`) covers segments whose frames all failed
    the quality gate with their best available frame. Pass 3 fills any
    remaining slots with the best usable frames not yet picked.
    """
    usable: list[tuple[float, int, SceneQuality]] = []
    all_scored: list[tuple[float, int, SceneQuality]] = []
    total = 0
    for index, image in enumerate(frames):
        total = index + 1
        quality = assess_quality(image)
        score = _quality_score(quality)
        all_scored.append((score, index, quality))
        if quality.usable:
            usable.append((score, index, quality))
    usable.sort(key=lambda entry: (-entry[0], entry[1]))
    if not usable:
        return []
    all_scored.sort(key=lambda entry: (-entry[0], entry[1]))
    seg_size = max(1, math.ceil(total / top_k))
    picked: list[FramePick] = []
    picked_indices: set[int] = set()
    covered: set[int] = set()
    for _, index, quality in usable:  # pass 1: best usable per segment
        if len(picked) >= top_k:
            break
        segment = index // seg_size
        if segment not in covered:
            covered.add(segment)
            picked.append(FramePick(index=index, quality=quality))
            picked_indices.add(index)
    if allow_degraded:
        for segment in range(math.ceil(total / seg_size)):  # pass 2: degraded-segment fallback
            if len(picked) >= top_k or segment in covered:
                continue
            for _, index, quality in all_scored:
                if index // seg_size == segment and index not in picked_indices:
                    covered.add(segment)
                    picked.append(FramePick(index=index, quality=quality))
                    picked_indices.add(index)
                    break
    for _, index, quality in usable:  # pass 3: fill shortfall from usable remainder
        if len(picked) >= top_k:
            break
        if index not in picked_indices:
            picked.append(FramePick(index=index, quality=quality))
            picked_indices.add(index)
    picked.sort(key=lambda pick: pick.index)
    return picked


__all__ = ["DEFAULT_TOP_K", "MAX_FRAMES", "frames_from_path", "select_key_frames"]