# Change: Blur combobox input after selecting a filter option

## Why

When the user selects a filter option (area or location) from the dropdown, the dropdown closes (`dropdown.style.display = 'none'`) but the text input retains focus due to `e.preventDefault()` in the `mousedown` handler. The user sees a blinking cursor with no visible options — it is unclear whether they can type to filter further or need to click again to re-open the dropdown. This ambiguity hurts usability on both the landing page and the dashboard.

## What Changes

- **`static/js/combobox.js`**: In both `mousedown` handlers (the "clear all" row and individual option rows), call `setTimeout(function() { textInput.blur(); }, 0)` after processing the selection. This removes focus from the input, which immediately hides the dropdown (via the existing `blur` → `setTimeout` → `display: none` chain) and makes the cursor disappear. The `setTimeout` is necessary because calling `e.preventDefault()` on the mousedown event instructs the browser to retain focus on the currently active element; deferring the blur allows the native event cycle to complete first. When the user clicks the control again, the existing `focus` handler re-opens the dropdown with fresh, up-to-date options.
- No changes to templates, backend, or CSS. The entire fix is a simple addition in two event handlers within `combobox.js`.

## Impact

- Affected specs: `landing`, `dashboard` (both reference the shared combobox widget behavior)
- Affected code: `static/js/combobox.js` only
- **Conflict note**: The parallel change `add-cascading-filter-options` also modifies `combobox.js`. If both proposals are active simultaneously, they must be applied sequentially or merged.
- No breaking changes: existing keyboard navigation (ArrowDown/Up, Enter, Escape) and mouse interaction continue to work; the only difference is that focus is released after a selection, which restores on the next click.
