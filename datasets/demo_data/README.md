# demo_data — real-world media corpus (open-licensed + local)

A small, fully documented corpus of **real** citizen-style photos and videos,
used to exercise Civitas' vision stack on the media people actually upload
(real-world track, see `ml-layer.md` Phase 13). The old synthetic-trained
classifier collapsed on this corpus; the zero-shot CLIP classifier
(`vision-clip-v2`) classifies it correctly.

## Layout

| Path | Contents |
|---|---|
| `images/` | 17 real photos + 2 out-of-distribution controls (`ood_control`) across the MVP categories, plus 6 locally provided photos covering the v2 real-media categories (`drainage_damage`, `other_infrastructure_damage`, `no_incident`, `pest_infestation`) |
| `videos/` | 8 real videos: flooded street, dripping bucket, leaking roof, ceiling infiltration (35 s clip with a ~5 s dark intro), plus 3 locally provided videos (pest on wall, wall damage, water accumulation) |
| `results/` | `real_world_report.md` + `real_world_predictions.json` — the honest probe outputs (verdict, confidence, OOD ratio, rejections) |
| `manifest.json` | provenance for every file: source page, license, sha256, expected category |

## Licenses and provenance

Every Wikimedia file is a Commons upload under a permissive license
(CC0 / CC BY / CC BY-SA / public domain) with the exact source page, license
and sha256 recorded in `manifest.json`. The `Real_*` files are **locally
provided** demo media with no recorded license — their manifest entries say
so explicitly; they must not be redistributed. Please keep the manifest in
sync with the files.

## How to reproduce the numbers

```bash
pip install -e "ml/vision[nn]"     # transformers + torch + CLIP download
python -m civitas_evaluation.real_world_probe
```

Expected result (measured on the Wikimedia subset, see `results/real_world_report.md`):

- 17/17 real photos classified correctly
- 7/8 real videos classified correctly
- 2/2 out-of-distribution controls flagged (OOD ratio >= 2.0)
- 1 known limitation: `Real_Video2.mp4` (wall/plaster damage) is called
  `water_leakage` at low confidence (0.12 margin) — recorded as
  misclassified in the report, not hidden

The probe selects `vision-clip-v2` (CLIP); without the model it degrades to
the deterministic k-NN and reports the degraded version.

## Ground truth

The `expected_category` in `manifest.json` was curated by the demo authors
from the Wikimedia file titles/descriptions (e.g. "A pothole in Dilova
Street in Kyiv"). It is a human judgment on open-licensed media — recorded
as evidence for the probe, not as a production label set.
