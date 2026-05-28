## 1. Implementation

- [x] 1.1 Add `setTimeout(function() { textInput.blur(); }, 0)` inside the `clearLi` `mousedown` handler in `static/js/combobox.js` (after `updatePills()` and `dropdown.style.display = 'none'`)
- [x] 1.2 Add `setTimeout(function() { textInput.blur(); }, 0)` inside the option `li` `mousedown` handler in `static/js/combobox.js` (after `addValue(opt)` and `dropdown.style.display = 'none'`)
- [x] 1.3 Verify the `search-suggestion.js` click handler is unaffected (it calls `FastJobFilter.addValue()` directly, not via mousedown — no change needed)
- [x] 1.4 Verify the keyboard Enter handler is unaffected (it dispatches a synthetic `mousedown`, which will now also trigger `blur()` — correct behavior)

## 2. Verification

- [x] 2.1 Open the landing page, click an area filter, select an option → confirm the dropdown closes AND the cursor disappears
- [x] 2.2 Click the filter control again → confirm the dropdown re-opens with all available options (minus the selected one)
- [x] 2.3 Repeat the same test on the dashboard page
- [x] 2.4 Click the "clear all" (`— TODOS LOS SECTORES —`) row → confirm cursor disappears and dropdown closes
- [x] 2.5 Use keyboard navigation (Tab to focus, ArrowDown to highlight, Enter to select) → confirm cursor disappears after selection
- [x] 2.6 Click a search-suggestion (animated suggestion) → confirm it still fills both filters and the counter updates without issues
- [x] 2.7 Verify no regression: `npm run lint` or `python manage.py check` passes (adjust command to match project's actual lint tool)
