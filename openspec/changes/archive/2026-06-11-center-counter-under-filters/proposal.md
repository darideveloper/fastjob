## Why

With the addition of the "Subactividad" filter, the company-finder section on the landing page contains four columns in a horizontal flex layout on desktop (`md` and above). In intermediate screen sizes (especially between 768px and 1024px), this causes the filters to shrink excessively and results in layout overflow and visual clipping. Separating the filters and placing the counter above them, while ordering the filters logically (Ubicación, Sector/Área, Subactividad), ensures a clean, responsive layout across all viewports.

## What Changes

- **Landing Page Layout Update**:
  - Reorganize the company-finder container in `templates/home.html`.
  - Group the three combobox filters into a 3-column layout on desktop (`md` and above) and 1-column on mobile, ordered as: Ubicación, Sector / Área, Subactividad.
  - Position the company counter box in a row directly above the filters, centered horizontally on all screen sizes.
  - Update margins and padding to ensure a balanced vertical hierarchy inside the card.
- **Dashboard Layout Update**:
  - Reorganize the filters widget in `templates/dashboard/index.html` to align with this design, reordering the filters vertically as: Ubicación, Sector / Área, Subactividad.
  - Place the counter badge above the filters and centered to maintain visual consistency.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `landing`: Modify the layout requirements of the public company-finder section to place the counter above the filters, center it, and order the filters: Ubicación, Sector / Área, Subactividad.
- `dashboard`: Modify the placement of the company counter badge to be placed above the filters/form and centered, and order the filters: Ubicación, Sector / Área, Subactividad.

## Impact

- `templates/home.html`: Layout classes and structure of the company-finder section.
- `templates/dashboard/index.html`: Layout classes and structure of the filter form.
