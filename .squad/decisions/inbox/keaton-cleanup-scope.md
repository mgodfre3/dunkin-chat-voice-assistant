### 2026-02-25T14:32:52Z: Codebase cleanup scope
**By:** Keaton (Lead)
**What:** Full codebase evaluation for cleanup, modernization, and dead code removal.
**Why:** Brian requested full codebase evaluation for cleanup and modernization.

---

## BACKEND CLEANUP

### Dead / Prototype Files
| File | Issue | Lines | Risk |
|------|-------|-------|------|
| `app/backend/azurespeech.py` | Never imported by `app.py`. Class writes temp files to cwd (`./uploaded_audio.wav`, `./response_audio.wav`). Re-calls `logging.basicConfig()` at module level, conflicting with app's config. | all | Low — unused code |
| `app/backend/azure_speech_gpt4o_mini.py` | Standalone `__main__` prototype. Not imported anywhere. Uses global mutable state, busy-wait loop (`while not exit_program: pass`). | all | Low — unused code |

**Recommendation:** Archive or remove both files. If the AzureSpeech REST fallback path is ever re-enabled, it should be rewritten. The frontend `useAzureSpeech.tsx` hook exists as a stub that calls `/azurespeech/speech-to-text` but that route is never mounted in `app.py`.

### `app/backend/rtmt.py` — Code quality
| Line(s) | Issue | Fix |
|----------|-------|-----|
| 31 | `type(self.text) == str` — use `isinstance(self.text, str)` | ruff UP rule, PEP 8 |
| 12 | Noisy comment `# Import the order state singleton` | Remove |
| 184 | f-string in logging: `logging.error(f"Error ...")` | Use `logger.error("...: %s", e)` |
| 257, 271 | `print()` calls for error/close messages | Replace with `logger.warning()` / `logger.info()` |
| 179–183 | Reverse-indexed `for` loop with `IndexError` catch is fragile | Use list comprehension: `[o for o in output if o["type"] != "function_call"]` |
| 20–48 | `ToolResult`, `Tool`, `RTToolCall` classes with manual `__init__` | Convert to `@dataclass` for less boilerplate |
| 147–150 | Hardcoded tool-name check `if item["name"] in ["update_order", "get_order"]` to decide whether to pass `session_id` | Fragile if new session-aware tools are added; consider a tool registry flag |

### `app/backend/tools.py` — Minor issues
| Line(s) | Issue | Fix |
|----------|-------|-----|
| 89 | Quad-quote `""""` — invalid docstring, it's a string literal + empty string | Change to `"""` or convert to `#` comment block |
| 89–97, 191–199, 281–289 | Block "docstrings" are free-standing string literals, not actual docstrings | Move into function docstrings or convert to `#` comments |
| 189–190 | Extra blank line | Remove |
| 330 | Trailing blank line | Remove |

### `app/backend/order_state.py` — Modernization
| Line(s) | Issue | Fix |
|----------|-------|-----|
| 33, 46, 78, 81, 86, 89, 95 | f-strings in `logger.info(f"...")` | Use lazy `%s` formatting: `logger.info("Session created with ID %s", session_id)` |
| 19–25 | Singleton via `__new__` override | Works but unusual; module-level instance already suffices. Low priority. |
| Session dict structure | `sessions[id]` stores untyped dicts with string keys | Consider a `SessionData` dataclass for type safety |

### `app/backend/models.py` — Type modernization
| Line | Issue | Fix |
|------|-------|-----|
| 2 | `from typing import List` — Python 3.11+ target | Use `list[OrderItem]` directly (PEP 585). Ruff UP rule will flag this. |
| 4, 12 | `finalTotal` uses camelCase | ⚠️ API contract with frontend `types.ts` — coordinate if changing. Low priority, alias possible. |

### `app/backend/requirements.txt` — Dependency concerns
| Issue | Detail |
|-------|--------|
| BOM/encoding corruption | Line 1 starts with garbled characters (BOM bytes). Re-save as UTF-8 without BOM. |
| `azure-cognitive-services-speech==1.38.0` | Only used by dead files (`azurespeech.py`, `azure_speech_gpt4o_mini.py`). Remove if those files are archived. |
| `rich==13.9.4` | Only used by `setup_intvect.py`, not the main app. Consider moving to a dev/scripts requirements file. |
| `azure-storage-blob==12.24.0` | Only used by `setup_intvect.py`. Same consideration. |
| `cffi==1.17.1` | Transitive dependency — should not be directly pinned. |

### `app/backend/setup_intvect.py` — Script quality
| Line(s) | Issue |
|----------|-------|
| 219, 222 | Duplicate `logger = logging.getLogger("voicerag")` assignment |
| 229 | `exit()` should be `sys.exit()` |
| Multiple | f-strings in logger calls |
| 62, 187 | Very long function signatures — consider a config dataclass |

---

## FRONTEND CLEANUP

### Dead Components (no active imports)
| File | Status |
|------|--------|
| `app/frontend/src/components/ui/grounding-file.tsx` | Not imported by any active component |
| `app/frontend/src/components/ui/grounding-file-view.tsx` | Not imported by any active component |
| `app/frontend/src/components/ui/grounding-files.tsx` | Not imported by any active component |
| `app/frontend/src/components/ui/history-panel.tsx` | Not imported by any active component. Also has a 1-second `setInterval` timer and uses array index as React key. |
| `app/frontend/src/components/ui/ImageDialog.tsx` | Import is commented out in `App.tsx:15` |

**Recommendation:** Remove these files or move to a `_deprecated/` folder. Also remove the `GroundingFile` and `HistoryItem` types from `types.ts` if they have no other consumers.

### `app/frontend/src/App.tsx` — Decomposition needed
| Issue | Detail |
|-------|--------|
| Component too large | `CoffeeApp` is ~340 lines with embedded sub-components. |
| Inline sub-components | `BrandHero`, `HeroHighlightCard`, `SessionTokenBanner`, `DonutArt`, `CoffeeArt`, `formatToken` are all in App.tsx — extract to `components/` files. |
| Commented-out code | Line 15: `// import ImageDialog ...`; Lines 402–403: commented JSX block. Remove. |
| Static data in component file | `heroHighlights` and `heroCallouts` arrays should be in a data file or constants module. |
| Duplicate order-update handlers | The `onReceivedExtensionMiddleTierToolResponse` callback (lines 130–138) and the `azureSpeech.onReceivedToolResponse` callback (lines 184–191) contain identical logic. Extract to shared handler. |

### `app/frontend/src/hooks/useAudioRecorder.tsx` — Bug risk
| Line | Issue |
|------|-------|
| 13 | `let buffer = new Uint8Array()` is module-scoped, not React-lifecycle-aware. Will persist across component unmount/remount. **Should be a `useRef`**. |

### `app/frontend/src/hooks/useAzureSpeech.tsx` — Weak typing
| Line(s) | Issue |
|----------|-------|
| 4–8 | Parameters interface uses `any` for all callback types. Should use proper types from `types.ts`. |
| 10 | `onReceivedToolResponse` is destructured in the interface but never referenced in the hook body. |
| 11, 38–40 | `startSession()` and `inputAudioBufferClear()` are empty stubs — document as intentional or implement. |

### `app/frontend/src/hooks/useRealtime.tsx` — Security note
| Line | Issue |
|------|-------|
| 61 | When `useDirectAoaiApi` is true, API key is embedded in the WebSocket URL query string. This is a dev-only feature but should be clearly flagged or removed for production. |

### `app/frontend/package.json` — Dependency audit
| Package | Status |
|---------|--------|
| `react-draggable@^4.4.6` | **Dead dependency** — not imported anywhere in the codebase. Remove. |
| `react-icons@^5.3.0` | Likely unused — `lucide-react` is the active icon library. Verify no imports, then remove. |
| `axios@^1.7.9` | Only used in `useAzureSpeech.tsx` for a single POST call. Could replace with native `fetch`. Low priority. |
| `darkreader@^4.9.96` | Runtime dark-mode injection. Functional but unconventional for a Tailwind app. Consider native Tailwind `dark:` classes long-term. |
| `vitest@^1.6.0`, `@vitest/coverage-v8@^1.6.0` | Stable 2.x available. Upgrade when convenient. |

### `app/frontend/vite.config.ts`
| Line(s) | Issue |
|----------|-------|
| 15–19 | `manualChunks` splits every `node_modules` package into its own chunk — creates excessive HTTP requests. Consider grouping related packages (e.g., all Radix, all i18next). |
| 48–49 | Test coverage `include` is limited to only 2 component files. Expand as more tests are added. |

---

## SHARED / INFRASTRUCTURE

### `app/Dockerfile`
- No `.dockerignore` found in the `app/` directory. The build context likely includes `__pycache__`, `.env`, `node_modules`, etc. Add a `.dockerignore`.
- The frontend build outputs to `../backend/static` and is then copied with `COPY --from=build-stage /backend/static /app/static` — this path mapping works but is fragile and not immediately obvious.

### `pyproject.toml`
- Only contains `[tool.ruff]` config. No `[project]` metadata or build system. Fine for now, but adding `[project]` metadata would be a modernization step.

### `CONTRIBUTING.md`
- References `pwsh ./scripts/start.ps1` and `.env-sample` files. Verify these exist and are current. Good as-is.

---

## TESTING GAPS

### Backend (2 test files, narrow coverage)
| Covered | Missing |
|---------|---------|
| `order_state.py` (order add/remove, session tokens) | `rtmt.py` — no WebSocket middleware tests |
| `tools.py` extras-blocking logic | `tools.py` search function (mock SearchClient) |
| | `app.py` — no app factory / configuration tests |
| | `tools.py` `attach_tools_rtmt()` wiring |

### Frontend (2 test files, narrow coverage)
| Covered | Missing |
|---------|---------|
| `order-summary.tsx` | `useRealtime` hook |
| `status-message.tsx` | `useAudioRecorder` / `useAudioPlayer` hooks |
| | Context providers (auth, theme, dummy-data, azure-speech) |
| | `App.tsx` integration / mount test |

---

## DO NOT CHANGE (working patterns to preserve)

1. **`rtmt.py` WebSocket proxy architecture** — The middle-tier forwarding pattern with server-side tool interception is well-designed. Do not restructure.
2. **`tools.py` search fallback logic** (lines 158–173) — The retry with minimal field projection on schema mismatch is a robust defensive pattern.
3. **`order_state.py` singleton + session model** — Correct for aiohttp's single-thread event loop. No concurrency issues.
4. **`app.py` credential resolution** (lines 41–51) — Clean API key → managed identity fallback chain.
5. **Frontend audio pipeline** (`useAudioPlayer` → `Player`, `useAudioRecorder` → `Recorder`) — Low-level Web Audio API handling that works correctly.
6. **Greeting-then-mic flow** (`App.tsx` lines 111–180) — Complex but necessary for good UX, including the 5-second safety timeout. Preserve the ref-based state machine.
7. **`order_state.py` round-trip token design** — Session token + incrementing round-trip index is a clean idempotency/ordering pattern.

---

## PRIORITY RANKING

### P0 — Safe, high-value (assign first)
1. ~~Remove dead frontend components~~ (grounding-file*, history-panel, ImageDialog) — zero references in active code
2. Remove commented-out code in `App.tsx` (lines 15, 402–403)
3. Fix `requirements.txt` BOM encoding
4. Remove unused `react-draggable` dependency from `package.json`
5. Fix `type() == str` → `isinstance()` in `rtmt.py:31`
6. Replace `print()` with `logger` in `rtmt.py:257,271`
7. Fix quad-quote `""""` in `tools.py:89`

### P1 — Moderate value, low risk (next sprint)
1. Extract `BrandHero`, `SessionTokenBanner`, SVG art from `App.tsx` into separate component files
2. Convert `ToolResult`, `Tool`, `RTToolCall` to `@dataclass`
3. Modernize `from typing import List` → `list[]` in `models.py`
4. Fix `useAudioRecorder.tsx` buffer variable to use `useRef` (potential bug)
5. Audit and remove unused `react-icons` and `axios` if confirmed dead
6. Replace f-strings in all `logger.*()` calls with lazy `%s` formatting (backend-wide)
7. Add `.dockerignore` to `app/` directory

### P2 — Nice-to-have, coordinate carefully (backlog)
1. Archive `azurespeech.py` and `azure_speech_gpt4o_mini.py` (confirm with Brian)
2. Upgrade Vitest to 2.x
3. Split `requirements.txt` into app vs. dev/scripts dependencies
4. Expand test coverage to `rtmt.py`, `useRealtime`, context providers
5. Evaluate `darkreader` vs. native Tailwind dark mode
6. Add `[project]` metadata to `pyproject.toml`
7. Group vendor chunks in `vite.config.ts` `manualChunks`
