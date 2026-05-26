## 1. Implementation
- [x] 1.1 In `static/js/combobox.js`, refactor `initCombobox` to read `container.dataset.combobox` to determine the "no filter" label (`"— TODOS LOS SECTORES —"` for `area`, `"— TODAS LAS UBICACIONES —"` for `location`, with a generic fallback `"— Todos —"` for unknown types).
- [x] 1.2 In `showDropdown`, replace the conditional `if (selected.length > 0)` block that renders "— Limpiar todos —" with an always-rendered first `<li>` that displays the per-field "no filter" label. On click, it sets `selected = []`, clears `textInput.value = ''`, calls `updatePills()`, and closes the dropdown. Style it with `italic` class (to exclude it from keyboard navigation) and a distinct visual treatment (e.g. `text-brand-dark font-semibold border-b border-gray-100`).
- [x] 1.3 In `showDropdown`, remove the `else if (!filtered.length && !term && selected.length === options.length)` block that renders "Todos seleccionados" (this state is now reachable via the "no filter" option).
- [x] 1.4 Change the dropdown `max-h-96` class to `max-h-[480px]` on the `<ul>` element created in `initCombobox`.
- [x] 1.5 Verify the scoped CSS rules in `templates/dashboard/index.html` (lines 7-8) apply `text-transform: uppercase` correctly to the new "no filter" row; since the `<li>` selector `[data-combobox] ul > li` already applies `text-transform: uppercase` to all dropdown items, no CSS change should be needed on either template. On the landing page (`templates/home.html`), there is no scoped CSS for `<li>` uppercase — the combobox applies it inline per `<li>` via `li.style.textTransform = 'uppercase'`. The "no filter" `<li>` must also set `li.style.textTransform = 'uppercase'` to be consistent.
- [ ] 1.6 (Manual) Verify on landing page and dashboard: (a) "no filter" is always first row, (b) clicking clears all pills, (c) keyboard skips it, (d) counter updates, (e) no hidden inputs on form submit when active.

## 2. Verification
- [x] 2.1 Run `pytest` — 116/117 pass (pre-existing unrelated failure).
- [ ] 2.2 (Manual) Verify landing page area dropdown shows "— TODOS LOS SECTORES —" and location shows "— TODAS LAS UBICACIONES —".
- [ ] 2.3 (Manual) Verify dashboard both comboboxes show per-field labels and clicking clears pills + updates counter.
- [ ] 2.4 (Manual) Verify keyboard nav skips the "no filter" row (`li:not(.italic)`).