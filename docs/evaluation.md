# Workflow evaluation

The offline harness compares a single prompt contract, a structured mega-prompt contract, and the Civitas multi-step contract across 25 privacy-safe synthetic cases covering all five MVP categories. Its saved output is deterministic contract coverage, not a live-model quality claim. Run `py -3.12 -m civitas_evaluation.run_workflow_eval --mode offline`.
