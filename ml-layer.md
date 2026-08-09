# Civitas ML Layer — Progress Notes

Branch: `ml-layer`. This file tracks the 12-phase plan and verification state;
repo work is committed with phase messages.

## Phase plan (1–12)

**Geospatial foundations (this repo's `geospatial/`)**
- [x] 1. Feature-engineering module — seed COMPLETE:
     - `geospatial/src/civitas_geo/feature_engineering.py` (evidence-only vector, no decisions)
     - `geospatial/tests/test_feature_engineering.py` (20 tests; package total 58 passing)
     - Exported from `civitas_geo.__init__`, wired into `ml/demo_end_to_end.py` (step 2b)
     - Verified: `ruff check`, `mypy src`, `pytest` — all passing
     - Commit `ce4af51` "Phase 1/12 complete"
- [ ] 2. Norms/comparison hooks: similar-pattern incidents (landmark-kind + category), spatial density ring features
- [ ] 3. Endpoint routing: calibrated nearest-station/zone assignment + assignment confidence (human review for ambiguous)

**Transactional density (production DB)**
- [ ] 4. Near-neighbour aggregates derived from the incident table (reports per cell history)
- [ ] 5. Support polygons: schools/waterlines/no-fly per-authority adjacency (validated against corpus before use)
- [ ] 6. Threshold calibration on the crawl corpus: `raw` fields -> training features, decision thresholds, evidence basis

**Fusion & arbitration**
- [ ] 7. Cross-modality arbitration (GPS vs text vs image geocodes) with source credibility
- [ ] 8. Human-in-the-loop: review queue by fusion-failure/mis-match, feedback loop into weights
- [ ] 9. Severity "under-1-year" temporal sensitivity (seasonality candidate)

**Upstream dependent work**
- [ ] 10. Data/evidence ingestion (transcript/translation) to archive
- [ ] 11. Shared artifact store: crawled pages, embeddings, model params
- [ ] 12. Public archives consumable by Authority as evidence

## Completed work summary

Commits on this branch: prior `7cd21fe` added duplicates + reasoning + demo. `ce4af51`
completes Phase 1. Featured fixes: raw-typing widened to include `str` (traffic level,
canonical category); ruff `F401` + mypy `dict` invariance fixes.

## Verification commands run (Phase 1)

```bash
cd geospatial
python -m pytest tests            # 58 passed
python -m ruff check src tests    # clean
python -m mypy src                # clean (10 files)
cd ..
python ml/demo_end_to_end.py      # full trace incl. feature vector (step 2b)
```

## Open items / known limitations

- Feature thresholds (freshness τ, density caps, RBF σ) are seeded constants,
  intentionally uncalibrated — Phase 6 calibrates on the crawl corpus.
- `population_density_proxy` counts landmark kinds, not residents; not fit for
  absolute density claims.
- Nearest-station routing and support polygons need the real DB
  (`CIVITAS_POSTGIS_DSN`) — memory mode returns explicit `mode="memory"`.