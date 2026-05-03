## ADDED Requirements

### Requirement: Integrated Search UI with Live Counter
The search filters on the Landing and Dashboard MUST be rendered as searchable dropdowns with the match counter placed in close visual proximity.
- The `combobox.js` widget MUST be used for both "Area" and "Location" inputs.
- The company counter MUST update automatically (debounced) when a filter selection changes.
- In the Landing Hero, the counter MUST be positioned "next to" the filter inputs (e.g., in the same horizontal row or immediate vicinity) to emphasize the interactive nature of the search.

#### Scenario: Selection update triggers counter
- **GIVEN** a user on the landing page.
- **WHEN** the user selects "Software" from the Sector dropdown.
- **THEN** the company counter MUST update to reflect only companies in the "Software" sector.

### Requirement: Restricted Admin User Filters
The Django Admin for the `User` model MUST restrict filter selections to the managed taxonomy.
- The `area_filter` and `location_filter` fields in `UserAdmin` MUST use dropdown (Select) widgets.
- Staff users MUST NOT be able to enter free-text values into these fields.

#### Scenario: Staff edits user filters
- **GIVEN** a staff user in the Django Admin editing a User.
- **WHEN** the staff user opens the "FastJob" fieldset.
- **THEN** they MUST see dropdown menus for "Area filter" and "Location filter" populated from the managed taxonomy.
