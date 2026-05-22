## MODIFIED Requirements

### Requirement: Integrated Search UI with Live Counter

The search filters on the Landing and Dashboard MUST be rendered as searchable dropdowns with the match counter placed in close visual proximity.

- The `combobox.js` widget MUST be used for both "Area" and "Location" inputs.
- The company counter MUST update automatically (debounced) when a filter selection changes.
- In the Landing Hero, the counter MUST be positioned "next to" the filter inputs (e.g., in the same horizontal row or immediate vicinity) to emphasize the interactive nature of the search.
- The widget MUST treat a non-OK HTTP response (e.g. `429`, `5xx`) from the option-list endpoint as a failure: it MUST check the response status before parsing the body and MUST NOT initialise the dropdowns with empty option lists on failure.
- The widget MUST NOT memoise a failed option-list fetch; a subsequent trigger MUST be able to retry the request.
- On an option-list fetch failure the widget MUST surface a visible, recoverable error (a message plus a retry control) within the filter UI, on both the Landing page and the Dashboard.

#### Scenario: Selection update triggers counter

- **GIVEN** a user on the landing page.
- **WHEN** the user selects "Software" from the Sector dropdown.
- **THEN** the company counter MUST update to reflect only companies in the "Software" sector.

#### Scenario: Option-list fetch failure is visible and retryable

- **GIVEN** the option-list endpoint returns a non-OK response (e.g. `429 Too Many Requests`) when the filter UI loads
- **WHEN** `combobox.js` initialises the Area and Location widgets
- **THEN** the widgets do NOT render as silently empty, non-functional dropdowns
- **AND** a visible error message with a retry control is shown in the filter UI
- **AND** activating the retry control re-requests the option list

#### Scenario: Retry after a transient failure recovers the widget

- **GIVEN** the first option-list fetch failed and the widget is showing the error state
- **WHEN** the option-list endpoint subsequently returns a successful response and the user activates the retry control
- **THEN** the widget re-fetches, populates both dropdowns, and becomes fully functional
- **AND** no page reload is required
