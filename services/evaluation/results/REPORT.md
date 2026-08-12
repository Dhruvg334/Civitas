# Civitas Phase 11/12 - ML capability evaluation (Member 2)

_Generated: 2026-08-11T14:01:12.886031+00:00 by `python run_all.py` from `services/evaluation`, [worktree commit]._

## The evidence chain

```
Frozen Dataset  ->  Final Models  ->  Untouched Test Set  ->  Saved Predictions  ->  Metrics  ->  Failure Cases
           (test_data/, sha256   (production editions,    (seeds 2000+, frozen,    (results/*_predictions.json,   (results/*_metrics.json,  (results/failures.json,
            manifest)             no retraining, no tuning) never regenerated)       every row saved)               recomputed every run)       FAILURES.md)
```

**Golden-demo separation:** the golden water-leak scenario (results/golden/) validates composition end-to-end. Its outputs are explicitly **not** presented as model-performance evidence; all accuracy numbers below come only from the independent frozen test set.

## Reproduce everything

```bash
# one documented command, from services/evaluation:
python run_all.py            # reads frozen test_data/ once, rewrites results/
python run_all.py check      # verifies the test set manifest hash before any metric
```

Regenerating the test set is refused once results exist (`regenerate-testset` subcommand fails loudly) so the untouched set can never be silently replaced after looking at metrics.

## 1. Dataset and labels

Full manifest: `test_data/manifest.json` (sha256 of every file). Summary:

| dataset | size | labels | source / provenance | split |
|---|---|---|---|---|
| vision | 50 images (5 x 10) | 5 Civitas MVP categories | synthetic procedural scenes (civitas_vision.benchmark), seeds 2000-2049 disjoint from train (<=16/class) and dev (>=1000) | final test set, frozen |
| media quality | 14 cases | usable / blurred-file-tiny-dark-bright-ambiguous-unsupported-missing-video-no-media | synthetic + hand-authored binaries | final test set, frozen |
| duplicates | 15 pairs | 6 same-incident, 5 clearly different, 4 hard negatives | hand-authored record pairs (text/gps/time/category) | final test set, frozen |
| clusters | 4 scenarios / 16 reports | expected incident membership | hand-authored multi-report scenarios | final test set, frozen |
| severity | 12 incidents | low/medium/high/critical | hand-authored from documented rule table | final test set, frozen |
| priority | 12 incidents | low/medium/high/critical (+ expected signals) | hand-authored from documented 10-signal semantics | final test set, frozen |
| resolution | 16 before/after pairs | resolved/partial/unverifiable/conflicting | hand-authored evidence records | final test set, frozen |

**Synthetic-status disclosure:** every image in this evaluation is procedurally generated; no real-world citizen or municipal imagery is used or claimed. Duplicate/cluster/severity/priority/resolution labels are hand-authored records. Severity and priority labels derive from the same documented rule tables the models implement - agreement therefore proves faithful, regression-safe implementation, **not** external calibration against real-world outcomes (which do not exist yet).

## 2. Final models and frozen thresholds

| component | model edition | thresholds (frozen) |
|---|---|---|
| vision-classifier | vision-knn-v1 | k=3, softmax_temperature=2.0, ood_uncertainty_floor=2.0 |
| media-quality-gate | vision-knn-v1 + civitas-ml media resolution | max_blur_score=0.001 (variance of Laplacian), min_width_px=64, min_luminance=0.02, max_luminance=0.98, low_vision_confidence=0.4 |
| duplicate-detection | duplicates-engine-v1 | duplicate_threshold=0.70 (ScoringConfig, frozen), max_reasonable_distance_m=2000.0, max_reasonable_delta_h=72.0 |
| incident-clustering | duplicates-engine-v1 | duplicate_threshold=0.70 (edge criterion, frozen) |
| severity-model | severity-model-v1 | bands=critical>=80, high>=60, medium>=35 |
| priority-model | priority-model-v2 | bands=critical>=80, high>=60, medium>=40 |
| resolution-verification | resolution-model-v1 | standing_water_evidence_min=0.20, coverage_growth_conflict_ratio=1.10 |

None of these were changed during evaluation; no parameter search, no retraining on test data.

## 3. Headline metrics

| component | n | headline metrics |
|---|---|---|
| vision-classifier | 50 | accuracy=1.0, macro_f1=1.0, misclassified=0.0 |
| media-quality-gate | 14 | correct_quality_verdicts=10.0, correct_quality_rate=1.0, unusable_cases_without_forced_category=10.0, ambiguous_low_confidence_flagged=1.0, gate_rejections_of_blur_tiny_dark_bright=6.0 |
| duplicate-detection | 15 | decisive_pairs=11.0, review_escalated=4.0, review_escalated_hard=2.0, precision=0.6667, recall=1.0 |
| incident-clustering | 4 | scenarios_fully_correct=2.0, scenario_accuracy=0.5, same_incident_pairs_merged=7.0, different_incident_pairs_separated=8.0 |
| severity-model | 12 | accuracy=1.0, cohen_kappa=1.0, critical_recall=1.0, explanation_consistency_violations=0.0, factor_citations=49.0 |
| priority-model | 12 | accuracy=1.0, cohen_kappa=1.0, critical_case_recall=1.0, critical_labeled=3.0, critical_caught=3.0 |
| resolution-verification | 16 | accuracy=0.875, cohen_kappa=0.8333, partial_recall=1.0, partial_accuracy=1.0, unverifiable_recall=1.0 |

Per-component details, class-wise precision/recall/F1 and confusion matrices follow.

### `vision-classifier`

- test set: test_data/vision (50 images, seeds 2000-2049, disjoint from train/dev)
- model: vision-knn-v1
- metrics: {
  "accuracy": 1.0,
  "macro_f1": 1.0,
  "misclassified": 0.0
}

| class | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|
| pothole_road_damage | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| water_leakage | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| garbage_overflow | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| broken_streetlight | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| fallen_tree | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| unusable | 0 | 0 | 0 | - | - | - |

Confusion matrix (rows = true, columns = predicted):

| true \ pred | pothole_road_damage | water_leakage | garbage_overflow | broken_streetlight | fallen_tree | unusable |
|---|---|---|---|---|---|---|
| pothole_road_damage | 10 | 0 | 0 | 0 | 0 | 0 |
| water_leakage | 0 | 10 | 0 | 0 | 0 | 0 |
| garbage_overflow | 0 | 0 | 10 | 0 | 0 | 0 |
| broken_streetlight | 0 | 0 | 0 | 10 | 0 | 0 |
| fallen_tree | 0 | 0 | 0 | 0 | 10 | 0 |
| unusable | 0 | 0 | 0 | 0 | 0 | 0 |

- every image passed the quality gate (media_usable=True) and received a category
- confidence = top-1/top-2 vote-share margin; ood_ratio flags out-of-manifold inputs

### `media-quality-gate`

- test set: test_data/media_quality (14 cases: valid/blurred/tiny/dark/bright/ambiguous/unsupported/missing/video/no-media)
- model: vision-knn-v1 + civitas-ml media resolution
- metrics: {
  "correct_quality_verdicts": 10.0,
  "correct_quality_rate": 1.0,
  "unusable_cases_without_forced_category": 10.0,
  "ambiguous_low_confidence_flagged": 1.0,
  "gate_rejections_of_blur_tiny_dark_bright": 6.0,
  "valid_images_classified": 3.0
}

- unsupported bytes / missing file / video-without-path / no-media are rejected at the service layer with structured codes (media_unreadable, media_not_found, media_invalid_kind) and never force a category
- the ambiguous 50/50 blend is a derived input (committed train-prototype mix, documented in the manifest); it must be flagged low-confidence, not asserted

### `duplicate-detection`

- test set: test_data/duplicates (15 labelled pairs: 6 positive, 5 negative, 4 hard-negative)
- model: duplicates-engine-v1
- metrics: {
  "decisive_pairs": 11.0,
  "review_escalated": 4.0,
  "review_escalated_hard": 2.0,
  "precision": 0.6667,
  "recall": 1.0,
  "f1": 0.8,
  "accuracy": 0.8182,
  "false_merge_rate": 0.2857,
  "false_split_rate": 0.0,
  "false_merges": 2.0,
  "false_splits": 0.0
}

- escalated pairs are decisions withheld for human review (near-threshold or conflicting evidence), never counted as wrong
- false-merge rate = fraction of genuinely-different pairs merged; false-split rate = fraction of same-incident pairs kept apart

### `incident-clustering`

- test set: test_data/clusters (4 scenarios, 16 labelled reports)
- model: duplicates-engine-v1 (clustering stage)
- metrics: {
  "scenarios_fully_correct": 2.0,
  "scenario_accuracy": 0.5,
  "same_incident_pairs_merged": 7.0,
  "different_incident_pairs_separated": 8.0
}

- report-level pair accuracy separates 'merges that must happen' from 'merges that must not happen'

### `severity-model`

- test set: test_data/severity (12 hand-authored cases; labels computed from the documented rule table)
- model: severity-model-v1
- metrics: {
  "accuracy": 1.0,
  "cohen_kappa": 1.0,
  "critical_recall": 1.0,
  "explanation_consistency_violations": 0.0,
  "factor_citations": 49.0
}

| class | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|
| low | 0 | 0 | 0 | - | - | - |
| medium | 7 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| high | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| critical | 2 | 0 | 0 | 1.0 | 1.0 | 1.0 |

Confusion matrix (rows = true, columns = predicted):

| true \ pred | low | medium | high | critical |
|---|---|---|---|---|
| low | 0 | 0 | 0 | 0 |
| medium | 0 | 7 | 0 | 0 |
| high | 0 | 0 | 3 | 0 |
| critical | 0 | 0 | 0 | 2 |

- labels are computed from the documented severity rule table at test-set generation (constants drift-guarded); agreement therefore proves faithful implementation + regression safety, not external calibration (no real-world severity labels exist - recorded limitation)
- explanation consistency: every cited factor must match a feature present in the input
- known limitation: category base points (min 35 for streetlight) make the low band unreachable - the minimum achievable score is 41 (medium); critical needs >= 107 rule points under the squash curve 100*(1-exp(-points/66))

### `priority-model`

- test set: test_data/priority (12 hand-authored cases; labels computed from the documented weight table)
- model: priority-model-v2
- metrics: {
  "accuracy": 1.0,
  "cohen_kappa": 1.0,
  "critical_case_recall": 1.0,
  "critical_labeled": 3.0,
  "critical_caught": 3.0,
  "explanation_consistency_violations": 0.0,
  "engineering_faithfulness_violations": 0.0,
  "expected_reasons_missing": 0.0
}

| class | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|
| low | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| medium | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| high | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| critical | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |

Confusion matrix (rows = true, columns = predicted):

| true \ pred | low | medium | high | critical |
|---|---|---|---|---|
| low | 3 | 0 | 0 | 0 |
| medium | 0 | 3 | 0 | 0 |
| high | 0 | 0 | 3 | 0 |
| critical | 0 | 0 | 0 | 3 |

- critical-case recall is the fraction of labelled-critical incidents the model marks critical - the urgent-attention capability
- explanation consistency: a cited reason (e.g. 'school nearby') requires the corresponding engineered signal to be nonzero in the input features
- engineering faithfulness: each expectation was derived from the documented signal mappings (<=300m school -> 1.0, reports -> 1-exp(-(n-1)/2), etc.) and compared against the model's engineered vector; deviations are evidence failures

### `resolution-verification`

- test set: test_data/resolution (16 labelled before/after cases, 4 per outcome)
- model: resolution-model-v1
- metrics: {
  "accuracy": 0.875,
  "cohen_kappa": 0.8333,
  "partial_recall": 1.0,
  "partial_accuracy": 1.0,
  "unverifiable_recall": 1.0,
  "unverifiable_detected": 4.0,
  "unverifiable_labeled": 4.0,
  "unverifiable_never_marked_resolved": 4.0,
  "conflicting_precision": 1.0
}

| class | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|
| resolved | 4 | 1 | 0 | 0.8 | 1.0 | 0.8889 |
| partial | 4 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| unverifiable | 4 | 1 | 0 | 0.8 | 1.0 | 0.8889 |
| conflicting | 2 | 0 | 2 | 1.0 | 0.5 | 0.6667 |

Confusion matrix (rows = true, columns = predicted):

| true \ pred | resolved | partial | unverifiable | conflicting |
|---|---|---|---|---|
| resolved | 4 | 0 | 0 | 0 |
| partial | 0 | 4 | 0 | 0 |
| unverifiable | 0 | 0 | 4 | 0 |
| conflicting | 1 | 0 | 1 | 2 |

- the safety guard is explicit in the metrics: unverifiable evidence must never be marked fully resolved
- partial is only correct when standing water (or equivalent) remains after the flow is gone

## 4. Failure analysis

Total structured failures recorded: **6**. Dangerously unacceptable: **4**.

| failure_id | component | case | expected | actual | reason | improvement |
|---|---|---|---|---|---|---|
| dup-fp-0 | duplicate-detection | dup-hard-similar-text-different-location | not a duplicate (0) | merged (1), composite 0.41 | composite 0.41 crossed the 0.70 threshold; dominant contributions: text_similari | strengthen the conflicting-category gate on spatial overlap or add an  |
| dup-fp-1 | duplicate-detection | dup-hard-same-location-different-category | not a duplicate (0) | merged (1), composite 0.85 | composite 0.85 crossed the 0.70 threshold; dominant contributions: category_agre | strengthen the conflicting-category gate on spatial overlap or add an  |
| cluster-1 | incident-clustering | cl-nearby-incidents | merged_correctly=False, separated_correctly=True, both True | {"CB-1": "CL-001", "CB-2": "CL-002", "CB-3": "CL-003", "CB-4": "CL-004"} | the 0.70 composite threshold on text+spatial features could not resolve this sce | a sector/street prior or an image-evidence signal would separate same- |
| cluster-3 | incident-clustering | cl-same-location-different-category | merged_correctly=True, separated_correctly=False, both True | {"CD-1": "CL-001", "CD-2": "CL-001", "CD-3": "CL-001", "CD-4": "CL-001"} | the 0.70 composite threshold on text+spatial features could not resolve this sce | a sector/street prior or an image-evidence signal would separate same- |

Full rows (including acceptable failures, feature evidence and inputs): `results/failures.json` and `FAILURES.md`.

## 5. Golden scenario (composition, NOT model evidence)

- `golden-water-leak`: 5 steps saved to `results/golden/evidence_trail.json` (vision, embeddings, duplicate scores, cluster, severity, priority, before/after resolution).
- `model_evidence=false` is stored in the artifact itself: demo numbers are never presented as accuracy.

## 6. Recorded limitations

- The frozen component benchmark uses procedural synthetic media for reproducibility. A separate real-world media probe is maintained under datasets/demo_data/results; neither should be treated as universal field performance.
- Severity/priority labels come from the documented rule tables (faithfulness evidence, not external calibration).
- The ambiguous-blend test input is a pixel mix of two committed training-prototype scenes (derived, not a training example; provenance in the manifest).
- Duplicate/cluster labels are semantic (same physical incident), authored on text/gps/time/category records without real photos.
