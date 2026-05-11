# Fix Dashboard Company Counter Placement

## Description
This change fixes a bug where the company counter on the client dashboard (`/dashboard/`) does not update when filters are changed or loaded. The root cause is a structural mismatch in the HTML template `templates/dashboard/index.html` where the `data-company-counter` element was placed outside of the `data-filter-widget` container. The `combobox.js` script expects the counter to be a child of `data-filter-widget` to update it dynamically. Moving the `data-filter-widget` attribute to the parent `<div>` encompassing both the form and the counter header resolves the issue without requiring changes to the JavaScript logic.

## Capabilities Changed
- `dashboard`