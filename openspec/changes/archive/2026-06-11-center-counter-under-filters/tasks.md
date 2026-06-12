## 1. Landing Page Layout Update

- [x] 1.1 Modify the HTML structure in `templates/home.html` to separate the Sector, Location, and Subactividad filter inputs from the company counter.
- [x] 1.2 Group the three filter inputs into a responsive CSS Grid (`grid grid-cols-1 md:grid-cols-3 gap-4 w-full`) that spans the full width of the card, ordered as: Ubicación, Sector / Área, Subactividad.
- [x] 1.3 Create a new centered row directly above the filters and place the company counter box there, ensuring it remains within the `[data-filter-widget]` element and is centered horizontally on all viewport sizes.

## 2. Dashboard Layout Update

- [x] 2.1 Remove the company counter badge from the header section in `templates/dashboard/index.html`.
- [x] 2.2 Add the counter badge above the filter inputs inside the filter form, centered horizontally using a flex centering container (`flex justify-center mb-4`).
- [x] 2.3 Verify the counter container retains the `[data-company-counter]` attribute and stays inside the `[data-filter-widget]` container.

## 3. Verification

- [x] 3.1 Load the landing page and verify the counter updates correctly when selecting locations, areas, or subactivities.
- [x] 3.2 Load the dashboard and verify the counter updates dynamically above the filter inputs.
- [x] 3.3 Capture screenshots using Playwright CLI to verify no visual clipping/overflow on intermediate viewports.
