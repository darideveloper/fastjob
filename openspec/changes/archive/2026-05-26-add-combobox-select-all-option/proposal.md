# Change: Add "Select All" (No Filter) Option to Combobox Dropdowns

## Why
Users cannot quickly clear a filter combobox to see all companies. They must either click "Limpiar todos" (which only appears after selecting something) or manually remove pills one by one. Adding a permanent first option that means "no filter" makes the UX clearer: each combobox always shows a "— TODOS LOS SECTORES —" / "— TODAS LAS UBICACIONES —" row that, when clicked, clears the selection for that field — effectively disabling that filter. The current "Limpiar todos" row is conditional and ambiguous; replacing it with per-field "no filter" options that are always visible makes the intent explicit.

## What Changes
- Replace the conditional "— Limpiar todos —" clear-all row in `combobox.js` with two per-field "no filter" first options that are **always visible** regardless of selection state:
  - Area combobox: **"— TODOS LOS SECTORES —"**
  - Location combobox: **"— TODAS LAS UBICACIONES —"**
- Increase dropdown max-height from `max-h-96` (384 px) to `max-h-[480px]` (480 px) to accommodate more visible rows.
- Remove the "Todos seleccionados" fallback message (now unnecessary since the "no filter" option alway provides an actionable row).
- The existing `data-combobox` attribute on each container element determines which label to display.

## Impact
- Affected specs: `landing`, `dashboard`
- Affected code: `static/js/combobox.js` (primary), `templates/dashboard/index.html` (minor: scoped CSS), `templates/home.html` (no change needed)
- No API changes; no backend changes; no database migrations.