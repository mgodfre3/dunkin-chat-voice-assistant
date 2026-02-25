# Backend Cleanup — Python 3.11+ Modernization

**Author:** Fenster (Backend Dev)
**Date:** 2025-07-18

## Decision
Modernized all backend Python files to use Python 3.11+ idioms and resolved all ruff lint violations.

## Key Changes
- **Type annotations:** `Optional[X]` → `X | None`, `List[X]` → `list[X]`, `Callable` from `collections.abc`
- **`super()` call:** Simplified `super(OrderState, cls)` → `super()` in singleton `__new__`
- **`isinstance` check:** Replaced `type(x) == str` with `isinstance(x, str)` in rtmt.py
- **Import hygiene:** Fixed sorting (I001), removed unused imports (F401), removed duplicate imports (F811) in azurespeech.py
- **Logging consistency:** Replaced bare `print()` calls in rtmt.py with `logger.warning()`/`logger.info()`
- **`__all__` exports:** Added to models.py, order_state.py, rtmt.py, tools.py
- **Redundant comments:** Removed large block comments in tools.py that duplicated tool schema descriptions
- **`get_order` signature:** Normalized to `(args, session_id)` matching the rtmt.py calling convention

## Impact
- Zero ruff errors (was 29)
- All 56 tests pass
- No behavioral changes
