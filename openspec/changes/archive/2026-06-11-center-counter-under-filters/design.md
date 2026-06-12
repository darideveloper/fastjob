## Context

The addition of the third "Subactividad" filter to the landing page and dashboard has squished the layout on intermediate viewports. By separating the filters and the live counter into distinct vertical stacks, we prevent horizontal overflow and allow each filter box to utilize a flexible layout width.

## Goals / Non-Goals

**Goals:**
- Update `templates/home.html` layout to group the Sector, Location, and Subactividad inputs into a responsive CSS Grid (`grid grid-cols-1 md:grid-cols-3 gap-4 w-full`), and place the counter box centered below them.
- Update `templates/dashboard/index.html` layout to remove the counter badge from the header and place it centered (wrapped in a `flex justify-center mt-4` container) below the form/submit button.
- Maintain full functionality of the `combobox.js` and `search-suggestion.js` scripts (requires keeping both the inputs and counter elements inside the `[data-filter-widget]` parent).

**Non-Goals:**
- Altering the backend API endpoints or how filter counts are computed.
- Changing the JavaScript selection or count logic.

## Decisions

### Decision 1: Group landing page filters and split counter into a new row
- **Option A**: Keep horizontal flex layout but adjust widths and flex-wrap. *Rejected* because the counter card looks squished and wraps awkwardly.
- **Option B**: Put filters in a responsive 3-column CSS Grid (`grid-cols-1 md:grid-cols-3`) and place the counter in a centered row below. *Selected* because it utilizes the card width fully for inputs on desktop, avoids uneven wrapping, and keeps the counter clearly visible and centered.

### Decision 2: Reposition dashboard counter below the update button
- **Option A**: Keep the badge next to the heading. *Rejected* as it clashes with the centering goal and doesn't align visually.
- **Option B**: Move the badge under the "Actualizar búsqueda" button and center it using a flex centering container (`flex justify-center mt-4`). *Selected* for clean presentation and consistency.

## Risks / Trade-offs

- **[Risk]**: The JavaScript counter lookup (`widget.querySelector('[data-company-counter]')`) might break if the elements are moved.
  - **Mitigation**: Ensure that the counter elements remain descendants of the elements having the `data-filter-widget` attribute.
