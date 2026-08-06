from civitas_ml.contracts import DuplicateResult, VisionResult


def test_ml_contracts() -> None:
    vision = VisionResult(media_quality="limited")
    duplicate = DuplicateResult(is_duplicate=False, score=0.12)
    assert vision.observable_evidence == []
    assert duplicate.matched_incident_id is None
