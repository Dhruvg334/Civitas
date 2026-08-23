"""Tests for the deterministic precise-description templates (real-media track).

The contract under test: descriptions are template-generated from the
detected (primary, secondary) pair — never an LLM caption and never
asserting evidence that was not detected. Every description returns a
`basis` that records the template provenance.
"""

from civitas_vision.descriptions import build_precise_description


class TestExactTemplates:
    def test_wall_damage_template(self):
        text, basis = build_precise_description("other_infrastructure_damage", None)
        assert "wall/plaster" in text
        assert "does not clearly belong to the five core Civitas categories" in text
        assert "template for" in basis[0]

    def test_open_drain_subcategory_template(self):
        text, basis = build_precise_description("drainage_damage", "Open/unsafe drain")
        assert "open drainage cavity" in text
        assert "Open/unsafe drain" in basis[0]

    def test_no_incident_template(self):
        text, _ = build_precise_description("no_incident", None)
        assert "No pothole, flooding, garbage overflow" in text

    def test_description_never_asserts_undetected_facts(self):
        text, _ = build_precise_description("water_leakage", None)
        assert "not a verified visual fact" in text


class TestFallbacks:
    def test_unknown_combination_uses_category_fallback(self):
        text, basis = build_precise_description("fallen_tree", "Unusual subcategory")
        assert "fallen tree or large branch" in text
        assert any("template fallback" in b for b in basis)

    def test_unknown_category_uses_generic_wording(self):
        text, basis = build_precise_description("made_up_category", None)
        assert text.startswith("Detected: made_up_category")
        assert any("generic fallback wording" in b for b in basis)

    def test_missing_primary_returns_empty(self):
        text, basis = build_precise_description(None, None)
        assert text == ""
        assert "no primary category detected" in basis[0]
