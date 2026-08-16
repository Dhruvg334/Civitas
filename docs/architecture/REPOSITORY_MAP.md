# Repository Map

```text
apps/
├── web/                     Next.js citizen + municipal product interface
└── api/                     FastAPI operational boundary

services/
├── workflow/                LangGraph graph, LLM provider abstraction, runtime tools
├── knowledge/               Policy/playbook retrieval and grounding validation
├── evaluation/              Baseline + workflow evaluation runners and artifacts
├── ml/                      Unified ML inference contract
├── operations/              Operational service boundary
├── policies/                Policy service boundary
└── storage/                 Storage service boundary

ml/
├── vision/                  Image/video classification and evidence
├── duplicates/              Similarity and incident clustering
├── risk/                    Severity and priority
├── resolution/              Before/after verification
└── training/                Reproducible model utilities/experiments

geospatial/                  PostGIS/geospatial package
database/                    Migrations + deterministic seed data
schemas/                     Shared JSON contracts
prompts/                     Versioned baseline/agent prompts
datasets/                    Evaluation/demo manifests and labels
scripts/                     Media restore, provider smoke, workflow smoke utilities
docs/                        Public architecture/API/runtime/deployment documentation
tests/e2e/                   Integrated acceptance coverage
```

## Dependency direction

- `apps/web` consumes public API contracts; it does not import backend internals.
- `apps/api` composes operational services and exposes authenticated boundaries.
- `services/workflow` depends on typed tools/adapters rather than database implementation details.
- `services/ml` composes model packages behind one stable analysis contract.
- `services/knowledge` retrieves policy evidence without performing routing itself.
- `schemas` and Pydantic contracts define the shared wire surfaces.
- database persistence and LangGraph checkpoint persistence remain separate concerns.
