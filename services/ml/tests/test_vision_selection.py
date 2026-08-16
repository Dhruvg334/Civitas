"""Vision model selection tests (real-media track).

Covers `civitas_ml.vision_model.build_vision_pipeline` (knn/clip selection,
env default, loud errors, graceful degradation) and the `vision_pipeline`
routing through every composition entry point that accepts it
(`analyze_report`, `run_report`, `run_resolution`, `verify_resolution`).
A recording stub classifier proves the caller-supplied pipeline — not the
module default — is the classifier that actually runs.
"""

from __future__ import annotations

import pytest
from civitas_ml.analyze import analyze_report
from civitas_ml.contracts import MediaReference, ReportInput, ResolutionInput
from civitas_ml.pipeline import run_report, run_resolution
from civitas_ml.verify import verify_resolution
from civitas_ml.vision_model import (
    CID,
    KID,
    MODEL_CLIP,
    MODEL_KNN,
    build_vision_pipeline,
)
from civitas_vision.benchmark import make_image
from civitas_vision.contracts import CIVITAS_CATEGORIES, ClassificationProbs
from civitas_vision.detector import VisualIntelligencePipeline

IMAGE = make_image("water_leakage", 7101, "flow")


class RecordingClassifier:
    """Duck-typed classifier that records every image it sees."""

    model_version = "stub-vision-v1"
    calls: list[str] = []

    def predict(self, image) -> ClassificationProbs:
        self.calls.append(type(image).__name__)
        return ClassificationProbs(
            probabilities={
                "water_leakage": 0.6,
                **{c: 0.1 for c in CIVITAS_CATEGORIES if c != "water_leakage"},
            },
            primary_category="water_leakage",
            confidence=0.5,
            ood_ratio=1.0,
            basis=["stub classifier prediction (recording)"],
        )


@pytest.fixture
def stub_pipeline(monkeypatch):
    classifier = RecordingClassifier()
    classifier.calls = []
    monkeypatch.setattr(RecordingClassifier, "calls", [])
    pipeline = VisualIntelligencePipeline(classifier=classifier)
    yield pipeline
    classifier.calls = []


def _no_clip(monkeypatch) -> None:
    import civitas_vision.clip_classifier as clip

    monkeypatch.setattr(clip, "real_media_classifier", lambda: None)


def _fake_clip(monkeypatch) -> RecordingClassifier:
    import civitas_vision.clip_classifier as clip

    fake = RecordingClassifier()
    fake.model_version = CID
    fake.calls = []
    monkeypatch.setattr(clip, "real_media_classifier", lambda: fake)
    return fake


class TestModelSelection:
    def test_default_is_knn_without_env(self, monkeypatch):
        monkeypatch.delenv("CIVITAS_VISION_MODEL", raising=False)
        pipeline, version = build_vision_pipeline()
        assert version == KID
        assert type(pipeline.classifier).__name__ == "KNNClassifier"

    def test_env_selects_clip_when_available(self, monkeypatch):
        _fake_clip(monkeypatch)
        monkeypatch.setenv("CIVITAS_VISION_MODEL", MODEL_CLIP)
        pipeline, version = build_vision_pipeline()
        assert version == CID
        assert pipeline.classifier.model_version == CID

    def test_explicit_clip_degrades_to_knn_when_unavailable(self, monkeypatch, caplog):
        _no_clip(monkeypatch)
        pipeline, version = build_vision_pipeline(model=MODEL_CLIP)
        assert version == KID
        assert any("degrading" in r.message for r in caplog.records)

    def test_explicit_knn(self, monkeypatch):
        _fake_clip(monkeypatch)  # even with CLIP available, explicit knn wins
        pipeline, version = build_vision_pipeline(model=MODEL_KNN)
        assert version == KID

    def test_unknown_model_is_a_loud_config_error(self):
        with pytest.raises(ValueError):
            build_vision_pipeline(model="gpt-vision")
        with pytest.raises(ValueError):
            build_vision_pipeline(model="clip-v2")


class TestPipelineRouting:
    def test_analyze_report_uses_supplied_pipeline(self, stub_pipeline):
        analysis = analyze_report(
            image=IMAGE,
            description="water on the road",
            report_id="ROUTE-1",
            vision_pipeline=stub_pipeline,
        )
        assert analysis.vision.primary_category == "water_leakage"
        assert any(
            m.component == "vision" and m.model_version == "stub-vision-v1"
            for m in analysis.models
        )

    def test_run_report_uses_supplied_pipeline(self, stub_pipeline, tmp_path):
        from civitas_ml.adapters.mock import MockBackendAdapter

        image_path = tmp_path / "before.png"
        IMAGE.save(image_path)
        record = ReportInput(
            report_id="ROUTE-2",
            description="water on the road",
            media=[MediaReference(kind="image", local_path=str(image_path))],
            latitude=28.6139,
            longitude=77.2090,
        )
        analysis = run_report(
            record, backend=MockBackendAdapter(), vision_pipeline=stub_pipeline
        )
        assert analysis.vision.primary_category == "water_leakage"
        assert any(
            m.component == "vision" and m.model_version == "stub-vision-v1"
            for m in analysis.models
        )

    def test_run_resolution_uses_supplied_pipeline(self, stub_pipeline, tmp_path):
        from civitas_ml.adapters.mock import MockBackendAdapter

        before_path = tmp_path / "before.png"
        after_path = tmp_path / "after.png"
        make_image("water_leakage", 7101, "flow").save(before_path)
        make_image("garbage_overflow", 7102, "bin").save(after_path)
        record = ResolutionInput(
            incident_id="INC-1",
            before=MediaReference(kind="image", local_path=str(before_path)),
            after=MediaReference(kind="image", local_path=str(after_path)),
        )
        resp = run_resolution(
            record, backend=MockBackendAdapter(), vision_pipeline=stub_pipeline
        )
        assert len(stub_pipeline.classifier.calls) == 2
        assert resp.status in {"resolved", "partial", "unverifiable", "conflicting"}

    def test_verify_resolution_uses_supplied_pipeline(self, stub_pipeline):
        before = make_image("water_leakage", 7101, "flow")
        after = make_image("water_leakage", 7102, "flow")
        resp = verify_resolution(
            before, after, incident_id="INC-2", vision_pipeline=stub_pipeline
        )
        assert stub_pipeline.classifier.calls == ["Image", "Image"]
        assert resp.status in {"resolved", "partial", "unverifiable", "conflicting"}