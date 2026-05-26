## Context

The combobox widget (`static/js/combobox.js`) currently renders two kinds of non-selectable helper rows in the dropdown:
1. A conditional "— Limpiar todos —" row (visible only when `selected.length > 0`)
2. A fallback "Todos seleccionados" message (visible only when all options are selected and there is no search term)

Both rows are excluded from keyboard navigation by the `li:not(.italic)` selector in the keydown handler (line 189).

The user wants a **permanent first option** in each combobox that serves as a "select all" / "no filter" action. Clicking it clears the selection, meaning "don't apply this filter". The existing conditional "Limpiar todos" and "Todos seleccionados" rows become redundant and should be removed.

## Goals / Non-Goals

- Goals:
  - Always show a "no filter" option as the first row in each combobox dropdown
  - Label it contextually: "— TODOS LOS SECTORES —" for area, "— TODAS LAS UBICACIONES —" for location
  - Clicking it clears all pills for that combobox and updates the counter
  - Increase dropdown height for better visibility
  - Remove now-redundant UI rows

- Non-Goals:
  - Adding a literal "select every individual option" mode (the intent is to **clear** the filter, not select every whitelist value)
  - Changing the API or backend filter logic (empty selection already means "no filter")
  - Adding combobox types beyond `area` and `location`

## Decisions

- **Label source**: Read `container.dataset.combobox` at init time (already available on the element) to determine the per-field label. This avoids adding new `data-*` attributes to templates.
- **Always visible**: The "no filter" row renders regardless of selection state. When `selected.length === 0` and the user clicks it, it's a no-op (already clear) but still provides clear affordance.
- **Keyboard exclusion**: Mark the "no filter" row with the `italic` class so the existing `li:not(.italic)` selector in the keydown handler naturally skips it. No changes needed to keyboard logic.
- **Height**: `max-h-[480px]` gives approximately 13 visible rows at the current `py-2` padding, comfortably fitting 8+ selectable rows plus the "no filter" row and a search-filtered list.
- **Removal of "Limpiar todos"**: The "no filter" option subsumes this row's functionality. Keeping both would be confusing (two ways to do the same thing).
- **Removal of "Todos seleccionados"**: This fallback message is no longer needed. When the user has all options selected, they can still see and click the "no filter" option to clear them. After removal, the dropdown for "all selected, no search" state will show only the "no filter" row instead of the previous "Todos seleccionados" message.
- **Search text clearing**: When the user clicks the "no filter" option, `textInput.value` MUST be reset to `""`. Otherwise, after clearing pills the stale search text would filter the next dropdown open, contradicting the "show me everything" intent of clicking "no filter". The current "Limpiar todos" handler does NOT clear the search text — this is a behavioral improvement.

## Risks / Trade-offs

- **Loss of "Limpiar todos" for muscle-memory users**: Users accustomed to seeing "Limpiar todos" only when items are selected will see a different label. The new per-field labels are more descriptive and are always visible, so this is a net UX improvement.
- **"No filter" being clickable when already empty**: This is harmless (clears an already-empty array) and provides consistent affordance. No special state tracking needed.
- **"No filter" row during search**: The "no filter" row MUST be rendered as the first `<li>` even when the user is typing a search term. This is consistent with how the current "Limpiar todos" row works (it appears regardless of search state) and ensures the user can always reach the "clear filter" action from any dropdown state.

## Open Questions

- None. The requirement is clear: per-field "no filter" labels as specified by the user, always visible as the first dropdown option.