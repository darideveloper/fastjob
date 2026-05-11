# dashboard Specification

## MODIFIED Requirements

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, immediately above or below the filter form, showing the number of companies that match the currently-selected filter values. The counter MUST update whenever either dropdown value changes, MUST display only an integer (no company names, emails, or row data), and MUST source its number from the public count endpoint (so engine and counter cannot drift). The counter element (`[data-company-counter]`) MUST be a child of the widget container (`[data-filter-widget]`) so the client-side script can locate and update it correctly.

#### Scenario: Counter updates when filters change
- **GIVEN** the dashboard counter currently reads `42` for `area=""` and `location=""`
- **WHEN** the user selects `area="Tecnología"` from the dropdown
- **THEN** the counter re-fetches and displays the new count for `area="Tecnología"` within roughly one debounce window (~250 ms after selection)