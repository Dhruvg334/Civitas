# Failure analysis (Phase 11/12)

6 failures, 4 unacceptable. 

## dup-fp-0 [DANGEROUS] - duplicate-detection

- test case: dup-hard-similar-text-different-location
- input: similar-text-different-location pair (hard=True)
- expected: not a duplicate (0)
- actual: merged (1), composite 0.41
- model: duplicates-engine-v1
- feature evidence: text_similarity=1.0; category_agreement=1.0; time_similarity=0.9983; composite similarity 0.41 (threshold 0.70); text cosine 1.00; gps distance 1323 m (similarity 0.00); time delta 1.0 h (similarity 1.00); category agreement 1; landmark overlap 0.00; incident density 0.00; image embedding unavailable; weight redistributed; exceptional-evidence override (spatial or language agreement)
- likely reason: composite 0.41 crossed the 0.70 threshold; dominant contributions: text_similarity=1.0, category_agreement=1.0
- acceptable: no
- future improvement: strengthen the conflicting-category gate on spatial overlap or add an image-evidence signal for ambiguous overlaps

## dup-fp-1 [DANGEROUS] - duplicate-detection

- test case: dup-hard-same-location-different-category
- input: same-location-different-category pair (hard=True)
- expected: not a duplicate (0)
- actual: merged (1), composite 0.85
- model: duplicates-engine-v1
- feature evidence: category_agreement=1.0; landmark_similarity=1.0; time_similarity=0.9983; composite similarity 0.85 (threshold 0.70); text cosine 0.57; gps distance 22 m (similarity 0.98); time delta 1.0 h (similarity 1.00); category agreement 1; landmark overlap 1.00; incident density 0.00; image embedding unavailable; weight redistributed
- likely reason: composite 0.85 crossed the 0.70 threshold; dominant contributions: category_agreement=1.0, landmark_similarity=1.0
- acceptable: no
- future improvement: strengthen the conflicting-category gate on spatial overlap or add an image-evidence signal for ambiguous overlaps

## cluster-1 [DANGEROUS] - incident-clustering

- test case: cl-nearby-incidents
- input: scenario with expected cluster assignment
- expected: merged_correctly=False, separated_correctly=True, both True
- actual: {"CB-1": "CL-001", "CB-2": "CL-002", "CB-3": "CL-003", "CB-4": "CL-004"}
- model: duplicates-engine-v1
- feature evidence: [{"cluster_id": "CL-001", "report_ids": ["CB-1"], "span_m": 0.0}, {"cluster_id": "CL-002", "report_ids": ["CB-2"], "span_m": 0.0}, {"cluster_id": "CL-003", "report_ids": ["CB-3"], "span_m": 0.0}, {"cluster_id": "CL-004", "report_ids": ["CB-4"], "span_m": 0.0}]
- likely reason: the 0.70 composite threshold on text+spatial features could not resolve this scenario's ambiguity
- acceptable: no
- future improvement: a sector/street prior or an image-evidence signal would separate same-format-text different-location cases without raising the threshold

## cluster-3 [DANGEROUS] - incident-clustering

- test case: cl-same-location-different-category
- input: scenario with expected cluster assignment
- expected: merged_correctly=True, separated_correctly=False, both True
- actual: {"CD-1": "CL-001", "CD-2": "CL-001", "CD-3": "CL-001", "CD-4": "CL-001"}
- model: duplicates-engine-v1
- feature evidence: [{"cluster_id": "CL-001", "report_ids": ["CD-1", "CD-2", "CD-3", "CD-4"], "span_m": 66.7}]
- likely reason: the 0.70 composite threshold on text+spatial features could not resolve this scenario's ambiguity
- acceptable: no
- future improvement: a sector/street prior or an image-evidence signal would separate same-format-text different-location cases without raising the threshold

## res-13 [acceptable] - resolution-verification

- test case: res-13
- input: expected conflicting
- expected: conflicting
- actual: unverifiable (confidence 0.00)
- model: resolution-model-v1
- feature evidence: resolution-model-v1: before vs after evidence comparison; signals: active water flow, standing-water coverage, category hazard markers
- likely reason: evidence thresholds decided differently on this case
- acceptable: yes
- future improvement: tune the standing-water minimum / growth-conflict ratio on hard cases, then re-run the frozen set

## res-15 [acceptable] - resolution-verification

- test case: res-15
- input: expected conflicting
- expected: conflicting
- actual: resolved (confidence 0.67)
- model: resolution-model-v1
- feature evidence: resolution-model-v1: before vs after evidence comparison; signals: active water flow, standing-water coverage, category hazard markers
- likely reason: evidence thresholds decided differently on this case
- acceptable: yes
- future improvement: tune the standing-water minimum / growth-conflict ratio on hard cases, then re-run the frozen set
