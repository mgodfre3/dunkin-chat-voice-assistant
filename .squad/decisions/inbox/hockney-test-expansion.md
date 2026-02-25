# Decision: Test Expansion — Coverage Priorities

**Date:** 2025-07-10
**Author:** Hockney (Tester)
**Status:** Implemented

## Context
Brian requested expanded test coverage across backend and frontend.

## Decision
- Added unit tests for all pure/utility functions (`_get_bool_env`, `_is_extra_item`, `_infer_category`)
- Added Pydantic model serialization tests (ensures API contract stability)
- Added search tool tests with mocked Azure Search client (validates formatting + error handling)
- Expanded order state tests to cover remove operations, concurrent sessions, display formatting
- Expanded extras rules tests to cover mixed order scenarios
- Added frontend tests for `LoadingSpinner`, `GroundingFile`, and `calculateOrderSummary` edge cases

## Impact
- Backend: 9 → 56 tests
- Frontend: 4 → 13 tests
- No production code changes required
