"""Unit tests for hybrid BM25 + dense retrieval and jurisdictional boundary resolution."""

from civitas_knowledge.hybrid_retrieval import (
    PolicyDocument,
    hybrid_policy_search,
)
from civitas_knowledge.jurisdiction import resolve_jurisdiction


def test_hybrid_policy_search():
    corpus = [
        PolicyDocument(
            doc_id="POL-WAT-01",
            title="Municipal Water Main Rupture SOP",
            content="Standard operating protocol for burst potable water distribution pipelines. Requires emergency isolation valve shutdown.",
            category="water_leakage",
            department="water_supply",
            sla_hours=4,
            mandatory_equipment=["Sleeve Clamp", "Excavator", "Submersible Dewatering Pump"],
        ),
        PolicyDocument(
            doc_id="POL-ROAD-02",
            title="Asphalt Pothole & Cavity Repair Protocol",
            content="Hot mix asphalt compaction guidelines for vehicular roadways and pedestrian crossings.",
            category="pothole_road_damage",
            department="road_maintenance",
            sla_hours=24,
            mandatory_equipment=["Vibratory Roller", "Bitumen Emulsion Sprayer"],
        ),
        PolicyDocument(
            doc_id="POL-ELEC-03",
            title="High Voltage Luminaire & Streetlight Fault SOP",
            content="Electrical safety standards for repairing damaged streetlighting poles and underground cable shorts.",
            category="broken_streetlight",
            department="electrical_engineering",
            sla_hours=12,
            mandatory_equipment=["Insulated Gloves", "Hydraulic Bucket Truck", "Multimeter"],
        ),
    ]

    results = hybrid_policy_search("water main burst pipeline flooding", corpus, top_k=2)
    assert len(results) >= 1
    top_hit = results[0]
    assert top_hit.doc.doc_id == "POL-WAT-01"
    assert top_hit.rrf_score > 0.0
    assert "water" in top_hit.matched_terms or "burst" in top_hit.matched_terms


def test_jurisdiction_national_highway():
    j = resolve_jurisdiction(28.6139, 77.2090, road_classification="national_highway_expressway", landmark_context="Near NH-48 KM 24 Marker")
    assert j.jurisdiction == "NATIONAL_HIGHWAY_AUTHORITY"
    assert j.statutory_sla_hours == 12
    assert j.is_municipal_responsibility is False
    assert "NHAI" in j.governing_agency


def test_jurisdiction_state_pwd():
    j = resolve_jurisdiction(19.0760, 72.8777, road_classification="state_highway_pwd", landmark_context="SH-10 Junction")
    assert j.jurisdiction == "STATE_PUBLIC_WORKS"
    assert j.statutory_sla_hours == 24
    assert j.is_municipal_responsibility is False


def test_jurisdiction_municipal_default():
    j = resolve_jurisdiction(20.29614, 85.82451, road_classification="ward_street", landmark_context="Near DAV School Gate")
    assert j.jurisdiction == "MUNICIPAL_CORPORATION"
    assert j.is_municipal_responsibility is True
    assert j.statutory_sla_hours == 24
