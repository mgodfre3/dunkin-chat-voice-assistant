# Decision: Voice Choice & System Prompt Update

**Author:** Fenster (Backend Dev)
**Date:** 2025-07-24
**Status:** Applied

## Context
Brian reported the demo voice kept changing and wanted a consistent, friendly, calm voice for the drive-thru experience. He also wanted the assistant to always repeat the full order (including total) before closing, and to use the phrase "Thank you! Please pull around to the next window."

## Changes

### 1. Default voice: "alloy" → "coral"
- **File:** `app/backend/app.py` line 58
- **Reason:** "coral" is warm, friendly, and calm — ideal for a drive-thru. The env var `AZURE_OPENAI_REALTIME_VOICE_CHOICE` still allows override.
- Available voices: alloy, ash, ballad, coral, echo, sage, shimmer, verse.

### 2. System prompt closing instruction updated
- **File:** `app/backend/app.py` line 71
- **Old:** `"Always reiterate the order total due when wrapping up and close with 'Have a great day!'."`
- **New:** `"When the guest is done ordering, always use the 'get_order' tool to read back every item, size, and quantity along with the subtotal, tax, and final total. After confirming the order, close with: 'Thank you! Please pull around to the next window.'"`
- **Reason:** Ensures the order recap is explicit (item, size, quantity, subtotal, tax, total) and uses the drive-thru-appropriate closing phrase.

## Validation
- Ruff: All checks passed
- Tests: All 56 tests passed
- No behavioral regressions
