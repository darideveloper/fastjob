## ADDED Requirements

### Requirement: Filter option labels display in uppercase on Landing page
The company-finder filter widgets on the public landing page SHALL display all option labels —
both inside the dropdown list and inside the selected-value pills — in UPPERCASE. The underlying
option values sent to the API (for matching and counting) MUST remain unchanged (lowercase, as
stored in the database). The visual transformation MUST be achieved via CSS (`text-transform:
uppercase`) so that form submission values and whitelist validation are unaffected.

#### Scenario: Dropdown option labels appear in uppercase
- **GIVEN** the database contains areas `{"tecnología", "diseño"}`
- **WHEN** an anonymous visitor opens the Sector dropdown on the landing page
- **THEN** the dropdown list renders the labels as `TECNOLOGÍA` and `DISEÑO`
- **AND** the API count request still sends the lowercase values `tecnología` and `diseño`

#### Scenario: Selected pill labels appear in uppercase
- **GIVEN** the visitor has selected `"tecnología"` from the Sector dropdown
- **WHEN** the selection is confirmed
- **THEN** the pill inside the combobox input renders the text `TECNOLOGÍA`
- **AND** the hidden form input value for that selection remains `tecnología`
