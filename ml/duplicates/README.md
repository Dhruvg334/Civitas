# Duplicate Detection Engine

Determines whether multiple civic reports refer to the same real-world
incident by combining **embeddings, GPS, timestamps, landmarks and
clustering** — the duplicate intelligence layer used between report intake
and severity assessment.

## Signals

| Signal | Source | Shape |
|---|---|---|
| `text_similarity` | text embeddings (deterministic hashing TF fallback or provider) | cosine in [0,1] |
| `image_similarity` | CLIP-compatible image embeddings (provider-supplied) | cosine in [0,1] or None |
| `gps_similarity` | great-circle distance, RBF decay (σ=150 m) | [0,1] + metres |
| `time_similarity` | UTC-normalized delta, RBF decay (σ=24 h) | [0,1] + hours |
| `category_agreement` | citizen/vision category (canonicalized, alias-aware) | 0 or 1 |
| `landmark_similarity` | landmark set overlap around both reports | [0,1] |

## Scoring and decision

- Composite score = weighted sum of signals (default weights in
  `ScoringConfig`, explicitly redistributed when image embeddings are missing).
- `duplicate_threshold` (default 0.70) decides pairs; an exceptional-evidence
  override accepts pairs with strong spatial or language agreement that
  arrive within 24 h.
- **Consequential merges are gated**: pairs with conflicting canonical
  categories and weak text agreement are NOT auto-merged — they surface on a
  human review queue (`requires_review=true`). Near-threshold pairs are also
  flagged instead of silently accepted. This protects operations from
  collapsing distinct incidents that happen to be co-located.
- Every decision carries `feature_contributions` and a human-readable
  `decision_basis`, matching the stable `DuplicateResult` contract shape in
  `services/ml` (plus the additive `requires_review` flag).

## Clustering

Union-find connected components over scored pairs form `IncidentCluster`s.

- Representative report = most evidence (media count, description length,
  embeddings, landmarks).
- `span_m` records the maximum GPS spread inside a cluster.
- Spatial prefiltering (`spatial_clusters` PostGIS query or in-memory radius
  reducer) keeps pairwise scoring at civic scale.

## Embeddings

Provider-agnostic: `HashNgramEmbedder` runs anywhere deterministically and is
used for tests and offline; production plugs in
`sentence-transformers`/CLIP through `ProviderEmbedder`. Image embeddings
arrive precomputed on `ReportLike.image_embedding`; missing images never
masquerade as low similarity.

## Merge into operations

- A cluster becomes one incident; all member reports are linked as evidence.
- `find_duplicate_of` supports real-time intake: match a new report against
  open incidents before creating anything new.
- Confirmed clusters feed `ml/risk` repeated-report pressure features and
  work-order deduplication.

## Run

```bash
pip install -e "./ml/duplicates[dev]" -e "./geospatial[dev]"
pytest ml/duplicates
```

## Benchmark (synthetic)

`python datasets/generators/generate_duplicates.py` reproduces the labeled
dataset and reports engine metrics. Current run (seed 2026): **precision
41.6 %, recall 95.0 %** on automatically merged pairs, and **100 % of true
duplicate pairs are either auto-merged or flagged for human review**. The
residual auto-precision loss comes from deliberately hard cases: co-located
distinct incidents at the same landmark hotspot with near-identical wording
and 12 % mislabeled categories — exactly the cases the review queue exists
for. Image embeddings (absent in offline mode) resolve most of them.

## Known limitations

- Text embedding fallback is a hashing bag-of-ngrams: no synonym resolution.
  Together with strong GPS/landmark signals this is adequate for duplicate
  gating but weaker than contextual embeddings for paraphrase-heavy text.
- Landmark `radius_m` containment values are defaults, not measured.
- Cluster cohesion uses pairwise composite edges, not density-based
  clustering; two nearby-but-distinct incidents can join if text agrees
  strongly. Review the `scope for further calibration` flags before acting.