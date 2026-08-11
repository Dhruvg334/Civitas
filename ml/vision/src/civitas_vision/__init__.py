"""Civitas computer vision pipeline (Phase 3)."""

from civitas_vision.benchmark import EvaluationReport, make_image, run_evaluation, train_default_model
from civitas_vision.classifier import KNNClassifier, merge_media_probs, secondary_categories
from civitas_vision.contracts import (
    CIVITAS_CATEGORIES,
    ClassificationProbs,
    FramePick,
    REAL_MEDIA_CATEGORIES,
    SceneQuality,
    VisualClassificationResult,
)
from civitas_vision.descriptions import build_precise_description
from civitas_vision.detector import VisualIntelligencePipeline
from civitas_vision.evidence import extract_evidence
from civitas_vision.features import FEATURE_NAMES, extract_features
from civitas_vision.frames import frames_from_path, select_key_frames
from civitas_vision.quality import assess_quality

__all__ = [
    "EvaluationReport",
    "make_image",
    "run_evaluation",
    "train_default_model",
    "KNNClassifier",
    "merge_media_probs",
    "secondary_categories",
    "CIVITAS_CATEGORIES",
    "REAL_MEDIA_CATEGORIES",
    "ClassificationProbs",
    "FramePick",
    "SceneQuality",
    "VisualClassificationResult",
    "VisualIntelligencePipeline",
    "build_precise_description",
    "extract_evidence",
    "FEATURE_NAMES",
    "extract_features",
    "frames_from_path",
    "select_key_frames",
    "assess_quality",
]