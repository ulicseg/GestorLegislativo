# Testing Rules

## DO
- Write the smallest test that proves the change.
- Cover regressions for bug fixes.
- Prefer deterministic tests over brittle end-to-end checks when possible.

## DO NOT
- Do not add tests that merely restate the implementation.
- Do not skip verification for auth, data, or deployment-sensitive changes.

## Quality Gates
A testing change is valid only if:
- The targeted behavior is exercised directly.
- The test failure would clearly indicate a real regression.