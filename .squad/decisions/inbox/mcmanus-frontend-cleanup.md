# Decision: Frontend Code Quality Cleanup

**Author:** McManus (Frontend Dev)
**Date:** 2025-07-15
**Scope:** app/frontend/src/

## Summary

Performed a code quality cleanup pass across the React/TypeScript frontend. No visual or behavioral changes — strictly internal code hygiene.

## Key Decisions

1. **Removed duplicate ThemeProvider in index.tsx** — RootApp already provides ThemeProvider, so the outer wrapper in index.tsx was redundant. The inner (RootApp) provider is the one components actually consume.

2. **Eliminated all `any` types** — useAzureSpeech.tsx had 4 `any`-typed callback params. Replaced with proper types from types.ts and matching inline types. App.tsx callback signatures updated to match.

3. **Static data as module constants** — menu-panel.tsx used useEffect+useState to load a statically imported JSON file. Converted to a module-level `const` since the data never changes at runtime.

4. **Fixed grounding-files.tsx ref bug** — `isAnimating` (a useRef) was used as a boolean in a className expression instead of `isAnimating.current`. This caused `overflow-hidden` to always apply. Fixed to use `.current`.

5. **Modernized React patterns** — Replaced `React.FC<Props>` with direct function component signature; replaced unused `useState` with `useMemo` for computed-once values.

## Files Changed

- `src/index.tsx` — Removed duplicate ThemeProvider
- `src/App.tsx` — Dead code removal, type fixes, useMemo
- `src/hooks/useAzureSpeech.tsx` — Eliminated `any` types
- `src/context/dummy-data-context.tsx` — Modern imports
- `src/components/ui/menu-panel.tsx` — Simplified static data loading
- `src/components/ui/grounding-files.tsx` — Fixed ref bug
- `src/components/ui/history-panel.tsx` — Moved memo() to module scope
- `src/components/ui/__tests__/calculate-order-summary.test.tsx` — Removed unused import
