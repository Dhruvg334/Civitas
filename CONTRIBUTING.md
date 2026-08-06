# Contributing to Civitas

## Branches
Create feature branches from `develop`. Use names such as:
- `feature/workflow-structured-extraction`
- `feature/ml-duplicate-baseline`
- `feature/api-report-ingestion`

Open pull requests into `develop`. Release changes move from `develop` to `main` after integrated validation.

## Folder boundaries
Work inside the module folders assigned for the task. Shared contracts in `schemas/` require explicit review before merge.

## Pull-request completion
Every pull request must include:
- concise scope,
- changed interfaces,
- commands run,
- concrete test inputs and expected results,
- failure cases,
- known limitations,
- integration notes.

## Security and data
Never commit secrets, private citizen data, large datasets, unredacted uploads, or generated model artifacts.
