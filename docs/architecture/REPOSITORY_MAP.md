# Repository Map

```text
apps/web             Product interfaces
apps/api             Public API and operational boundary
services/workflow    Agent orchestration
services/knowledge   Policy/playbook grounding
services/evaluation  Baseline and workflow evaluation
services/ml          Stable ML inference interfaces
ml/*                 Model-specific implementation and experiments
database/*           Migrations and deterministic seed data
schemas/*            Cross-module contracts
prompts/*            Versioned production prompts
tests/e2e            Integrated acceptance tests
```
