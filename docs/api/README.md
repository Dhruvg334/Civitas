# Civitas API documentation

Documentation for the `apps/api` backend and the database layer.

## Start here

- **[`INTEGRATION.md`](INTEGRATION.md)** — integration playbook for the
  agent workflow, frontend, and ML service. The 8-step golden-scenario
  recipe, plus troubleshooting and the common envelope.

## Reference

- **[`STATE_MACHINE.md`](STATE_MACHINE.md)** — incident + work-order
  transition graphs, application-level invariants (no FK on
  `assigned_work_order_id`, re-clarification rules, reviewer gates).
- **[`HANDOFF_NOTES.md`](HANDOFF_NOTES.md)** — known limitations, adapter
  choices, secret handling, what's deliberately not in this codebase.

## In the API folder

- [`apps/api/README.md`](../../apps/api/README.md) — backend dev setup,
  env vars, run + test commands.
- [`apps/api/OPENAPI.md`](../../apps/api/OPENAPI.md) — full route
  reference with curl examples for every endpoint.
