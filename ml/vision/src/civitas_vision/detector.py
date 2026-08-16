"""Visual intelligence pipeline (Phase 3).

End-to-end media analysis for one citizen upload:

    image/video
       |  quality check (blur, exposure, resolution, saturation)
       v
    blur / unusable media?  -> rejected frames are reported, not classified
       v
    frame selection if video (key frames)
       v
    useful visual evidence -> per-frame features -> classification (k-NN
                              with softmax confidence) -> evidence rules
       v
    merged structured result: primary_category, secondary_categories,
    observable_evidence, confidence (plus provenance/basis)

The pipeline is a real CV/ML capability: all measurements come from numpy
pixel statistics, the classifier is trained and evaluated on the benchmark
harness (`civitas_vision.benchmark.run_evaluation`), and evidence strings
are rule outputs over measured features — not LLM descriptions.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from civitas_vision import evidence as evidence_rules
from civitas_vision.classifier import (
    KNNClassifier,
    merge_media_probs,
    secondary_categories,
)
from civitas_vision.clip_classifier import CLIPZeroShotClassifier
from civitas_vision.contracts import (
    ClassificationProbs,
    SceneQuality,
    VisualClassificationResult,
)
from civitas_vision.descriptions import build_precise_description
from civitas_vision.features import extract_features
from civitas_vision.frames import frames_from_path, select_key_frames
from civitas_vision.nn_classifier import NNClassifier
from civitas_vision.quality import assess_quality


class VisualIntelligencePipeline:
    """Configurable image/video -> structured visual intelligence."""

    def __init__(
        self,
        classifier: KNNClassifier | NNClassifier | CLIPZeroShotClassifier | None = None,
        top_frames: int = 4,
    ) -> None:
        self.classifier = classifier or _default_classifier()
        self.top_frames = top_frames

    def analyze_image(self, image: Image.Image) -> VisualClassificationResult:
        quality = assess_quality(image)
        if not quality.usable:
            return VisualClassificationResult(
                media_usable=False,
                frames_selected=0,
                quality=quality,
                basis=[f"media rejected: {'; '.join(quality.reasons)}"],
            )
        return self._classify_frames([(image, quality)])

    def analyze_video(self, path: str | Path, video_extra_frames: list[Image.Image] | None = None) -> VisualClassificationResult:
        """Analyze a video path (or pre-extracted frames in tests/offline).

        Key-frame selection keeps temporal coverage (see `select_key_frames`);
        the zero-shot CLIP classifier additionally tolerates degraded frames
        from segments without any quality-passing frame, while the
        deterministic k-NN keeps strict quality gating.
        """
        frames = video_extra_frames if video_extra_frames is not None else list(frames_from_path(str(path)))
        allow_degraded = isinstance(self.classifier, CLIPZeroShotClassifier)
        picks = select_key_frames(frames, top_k=self.top_frames, allow_degraded=allow_degraded)
        if not picks:
            return VisualClassificationResult(
                media_usable=False,
                frames_selected=0,
                quality=None,
                basis=["no usable frames after quality checks (blur/exposure)"],
            )
        return self._classify_frames(
            [(frames[pick.index], pick.quality) for pick in picks]
        )

    def _classify_frames(self, frames: list[tuple[Image.Image, SceneQuality]]) -> VisualClassificationResult:
        per_frame: list[ClassificationProbs] = []
        evidence_seen: list[str] = []
        basis: list[str] = []

        for image, quality in frames:
            feats = extract_features(image)
            probs = classifier_predict(self.classifier, image)
            per_frame.append(probs)
            ev = evidence_rules.extract_evidence(feats)
            evidence_seen.extend(ev)
            basis.append(
                f"frame quality: blur {quality.blur_score:.1f}, "
                f"luminance {quality.luminance_mean:.2f}"
            )
            if not quality.usable:
                basis.append(
                    "degraded-segment frame included for temporal coverage "
                    "(failed the quality gate; classification treated as weaker evidence)"
                )
            basis.extend(evidence_rules.evidence_basis(feats))

        merged = merge_media_probs(per_frame)
        supported = {
            c for c, p in merged.probabilities.items() if c == merged.primary_category or p >= 0.25
        }
        evidence = evidence_rules.filter_evidence_for_categories(
            list(dict.fromkeys(evidence_seen)), supported
        )
        description, description_basis = build_precise_description(
            merged.primary_category,
            merged.secondary_label,
            merged.probabilities,
            evidence,
        )
        basis.append(
            f"classification over {len(per_frame)} usable frame(s); "
            f"confidence {merged.confidence:.3f}"
        )
        basis.extend(description_basis)
        return VisualClassificationResult(
            primary_category=merged.primary_category,
            secondary_categories=secondary_categories(merged.probabilities, merged.primary_category),
            secondary_label=merged.secondary_label,
            precise_observable_description=description,
            observable_evidence=evidence,
            confidence=merged.confidence,
            ood_ratio=merged.ood_ratio,
            media_usable=True,
            frames_selected=len(per_frame),
            quality=frames[0][1],
            probability_vector=merged.probabilities,
            basis=basis,
        )


def classifier_predict(
    classifier: KNNClassifier | NNClassifier | CLIPZeroShotClassifier, image: Image.Image
) -> ClassificationProbs:
    """Predict for one image via the natural entry point of the classifier.

    The k-NN baseline consumes the classical 16-feature vector; the
    neural classifier consumes pixels; the zero-shot CLIP classifier
    consumes pixels through its frozen vision tower. All expose
    `predict(image)`.
    """
    return classifier.predict(image)


def _default_classifier() -> KNNClassifier | NNClassifier:
    """Vision-nn-v1 when the trained checkpoint exists, else the k-NN baseline.

    The deterministic k-NN stays the default so offline/synthetic-manifold
    behaviour (frozen Phase 11/12 evaluation, demo walk-throughs) never
    depends on an external model download. Callers analysing real-world
    media select the zero-shot CLIP classifier explicitly
    (`CLIPZeroShotClassifier.load()` / `civitas_ml.vision_model`).
    """
    cached = getattr(_default_classifier, "_cached", None)
    if cached is not None:
        return cached
    classifier = NNClassifier.load()
    if classifier is None:
        from civitas_vision.benchmark import train_default_model

        classifier = train_default_model()
    _default_classifier._cached = classifier
    return classifier


__all__ = ["VisualIntelligencePipeline"]