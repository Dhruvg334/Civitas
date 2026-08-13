# Pre-frontend implementation status

## Runtime composition

- [x] Production workflow composition factory exists.
- [ ] Application runtime is initialized in every production deployment configuration.
- [ ] Reusable test runtime fixture is available.
- [x] PostgreSQL saver lifecycle is owned by FastAPI lifespan when configured.
- [ ] PostgreSQL saver setup and shutdown are integration-tested.
- [x] SQLite execution skips PostgreSQL initialization.
- [x] Workflow metadata supplies a stable thread identifier.

## Workflow API, persistence, and golden slice

- [x] Start/status/clarification/review routes and runtime service exist.
- [ ] Narrow edit and reroute schemas are implemented and tested.
- [ ] Backend persistence adapters and citizen communication persistence are complete.
- [x] Golden FastAPI start-to-review-to-approval integration test passes.
- [ ] Runtime failure and idempotency matrix is complete.

## Evaluation

- [x] Offline 25-case deterministic contract corpus and runner exist.
- [ ] Real one-call baselines, real workflow evaluator, and complete metric suite exist.
- [ ] Versioned offline result artifacts and comparison report are generated.
- [ ] Optional live provider evaluation mode exists.

## Verification

- [ ] All required package suites, changed-package type checks, and diff checks have been rerun after completion.
