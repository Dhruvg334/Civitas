# Shared Schemas

This folder is the cross-module contract boundary. JSON Schema files are canonical until generated language-specific types are introduced.

Breaking changes require:
1. a versioned schema change,
2. contract tests in every affected module,
3. migration notes,
4. explicit integration review.
