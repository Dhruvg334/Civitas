# demo_data — real-world media corpus (open-licensed)

A small, fully documented corpus of **real** citizen-style photos and videos,
used to exercise Civitas' vision stack on the media people actually upload
(real-world track, see `ml-layer.md` Phase 13). The old synthetic-trained
classifier collapsed on this corpus; the zero-shot CLIP classifier
(`vision-clip-v1`) classifies it correctly.

## Layout

| Path | Contents |
|---|---|
| `images/` | 17 real photos + 2 out-of-distribution controls (`ood_control`), 5 MVP categories |
| `videos/` | 4 usable real videos (flooded street, dripping bucket, leaking roof) + 1 intentionally unusable one (`ceiling_infiltration.webm`, dark/blurry) |
| `results/` | `real_world_report.md` + `real_world_predictions.json` — the honest probe outputs (verdict, confidence, OOD ratio, rejections) |
| `manifest.json` | provenance for every file: source page, license, sha256, expected category |

## Licenses and provenance

Every file is a Wikimedia Commons upload under a permissive license
(CC0 / CC BY / CC BY-SA / public domain). The exact source page, author
attribution link, license and sha256 checksum per file are recorded in
`manifest.json` — please keep that manifest in sync with the files.

## How to reproduce the numbers

```bash
pip install -e "ml/vision[nn]"     # transformers + torch + CLIP download
python -m civitas_evaluation.real_world_probe
```

Expected result (measured on this corpus, see `results/real_world_report.md`):

- 17/17 real photos classified correctly
- 4/4 usable videos classified correctly
- 2/2 out-of-distribution controls flagged (OOD ratio >= 2.0)
- 1/1 unusable video honestly rejected (no forced category)

The probe selects `vision-clip-v1` (CLIP); without the model it degrades to
the deterministic k-NN and reports the degraded version.

## Ground truth

The `expected_category` in `manifest.json` was curated by the demo authors
from the Wikimedia file titles/descriptions (e.g. "A pothole in Dilova
Street in Kyiv"). It is a human judgment on open-licensed media — recorded
as evidence for the probe, not as a production label set.
