# Demo media corpus

This directory defines the real-media demonstration corpus used to exercise Civitas vision behavior on citizen-style photographs and short videos. Binary media is kept outside Git; the manifest, provenance, hashes, expected categories, and generated result reports remain versioned.

## Layout

| Path | Contents |
|---|---|
| `images/` | Open-licensed and locally supplied civic-incident photographs plus out-of-distribution controls |
| `videos/` | Short civic-condition videos used by the real-media probe |
| `results/` | Real-world probe predictions and human-readable report |
| `manifest.json` | Source page, license, SHA-256, expected category and remote key metadata |

## Provenance

Wikimedia assets retain their Commons source page and license (`CC0`, `CC BY`, `CC BY-SA`, or public domain) in the manifest. Locally supplied `Real_*` media is marked as non-redistributable where no public license is recorded.

## Restoring media

```bash
python scripts/fetch_demo_media.py
```

Open media is downloaded from its recorded source and verified against the manifest SHA-256. Locally supplied media is resolved through `CIVITAS_DEMO_MEDIA_BASE_URL` and the manifest `remote_key`.

## Real-media probe

```bash
pip install -e "ml/vision[nn]"
python -m civitas_evaluation.real_world_probe
```

The probe uses the CLIP vision path when the neural-model extra is available and records classification, confidence margin, OOD ratio, and rejected/uncertain cases in `results/`.

## Ground truth

`expected_category` values are human-curated from the media source/title/description and are recorded as probe labels rather than production ground truth. This keeps real-media behavior distinct from synthetic regression datasets and from live operational decisions.
