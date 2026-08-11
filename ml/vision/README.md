# Civitas Computer Vision Pipeline (Phase 3)

Real CV/ML media intelligence for citizen uploads (images and short videos):

    image/video
       |  quality check (sharpness, exposure, resolution, saturation)
       v
    blur / unusable media?   -> rejected frames reported, never classified
       v
    frame selection if video (key frames by sharpness + exposure)
       v
    useful visual evidence -> classical features -> k-NN classification
                              (softmax confidence) -> measurement-based
                              evidence rules
       v
    {
      "primary_category": "water_leakage",
      "secondary_categories": ["..."],
      "observable_evidence": ["water flowing across road", "standing water"],
      "confidence": 0.91
    }

## Modules

| Module | Responsibility |
|---|---|
| `civitas_vision.quality` | Laplacian-variance blur gate, exposure/saturation/resolution checks |
| `civitas_vision.frames` | Video frame extraction (OpenCV optional) + deterministic key-frame selection |
| `civitas_vision.features` | 18 classical pixel measurements (edges, color, blobs, texture) |
| `civitas_vision.classifier` | k-NN (k=3) over z-scored features, softmax confidence, frame-vote merge |
| `civitas_vision.evidence` | Observable-evidence strings derived from measurements and thresholds |
| `civitas_vision.detector` | `VisualIntelligencePipeline`: media -> structured result with basis |
| `civitas_vision.benchmark` | Synthetic deterministic scene generator + evaluation report |

Output contracts live in `civitas_vision.contracts` (`VisualClassificationResult`
is the stable product shape; every result also carries `basis`, `quality` and
`probability_vector` for review).

## Why this is genuinely CV/ML, not an LLM caption

- Classification and confidence come from **real pixel measurements** (Laplacian
  variance, edge orientation ratios, blue/green dominance, dark low-texture
  share, bright-peak geometry) computed with numpy on every frame.
- The classifier is **trainable and evaluated**: a held-out split of the
  deterministic synthetic benchmark reports accuracy, macro-F1, per-class
  precision/recall/F1 and a confusion matrix
  (`civitas_vision.benchmark.run_evaluation`).
- Evidence strings are **rule outputs over measurements** with explicit
  thresholds (calibrated on the corpus, recorded in `evidence.EVIDENCE_RULES`).
- Quality handling is measured: blur verdicts cite the variance-of-Laplacian
  number, and video key-frame selection ranks frames by sharpness/exposure.

## Recorded limitations (deliberately not hidden)

- Training/benchmark data is **synthetic and procedural** — no real-phone
  photo corpus exists yet. All metrics are quoted against that corpus; the
  harness accepts a real corpus when the ingestion pipeline lands.
- Thresholds (blur gate, evidence rules) are calibrated on synthetic in/out
  distributions with margins; they are calibration candidates for real data.
- Evidence rules favor specificity over coverage (e.g., tree-trunk evidence
  fires only when canopy green is pronounced); missing evidence is reported as
  an empty list, never fabricated.

## Run

```bash
pip install -e "./ml/vision[dev]"
pytest ml/vision
python -c "from civitas_vision.benchmark import run_evaluation; r = run_evaluation(); print(r.accuracy, r.macro_f1)"
```