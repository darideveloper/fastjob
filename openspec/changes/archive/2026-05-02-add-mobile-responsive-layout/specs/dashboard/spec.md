# dashboard Specification Delta

## ADDED Requirements

### Requirement: Activity table is horizontally scrollable on small viewports
The recent-activity table in `templates/dashboard/index.html` SHALL render at a fixed minimum width such that the existing `overflow-x-auto` wrapper engages on viewports below 640 px. Cell content (company email, template name, date, status badge) MUST NOT wrap mid-word, and status badges (`Enviado`, `Fallido`) MUST NOT clip to truncated forms (e.g. `Enviad…`, `Fallid…`).

#### Scenario: Activity table horizontal-scrolls at 320 px with seeded data
- **GIVEN** a logged-in user with at least three `MailingLog` rows (one each for sent and failed statuses) at viewport 320 × 800
- **WHEN** the dashboard page is rendered
- **THEN** the `<table>` element's `scrollWidth` is at least 640 px
- **AND** the wrapping `<div class="overflow-x-auto">` exposes a horizontal scrollbar (or scroll affordance)
- **AND** every status badge renders its full label (`Enviado` or `Fallido`) without text clipping

#### Scenario: Activity table at 768 px renders without horizontal scroll
- **GIVEN** the same seeded data at viewport 768 × 1024
- **WHEN** the dashboard page is rendered
- **THEN** the activity table fits without horizontal overflow inside its column
- **AND** no cell wraps to multiple lines

### Requirement: CV-list rows stack vertically on small viewports
Each item in the "Tus CVs" list (`<li>` rows containing the CV title, date, and per-row actions "Activo" / "Usar" / "Eliminar") SHALL stack the actions below the title on viewports below 640 px (`sm`), and SHALL render them side-by-side at `sm` and above. Long CV names MUST NOT push the actions off-screen at 320 px.

#### Scenario: Long CV name on a 320 px viewport stacks the actions below
- **GIVEN** a logged-in user with a CV named "Mi CV Senior Backend Developer Full Stack" at viewport 320 × 800
- **WHEN** the dashboard page is rendered
- **THEN** the title `<p>` and the actions `<div>` render on separate lines
- **AND** every action button is fully visible within the viewport (no element has `getBoundingClientRect().right > 320`)

#### Scenario: Same row at 768 px renders side-by-side
- **GIVEN** the same CV at viewport 768 × 1024
- **WHEN** the dashboard page is rendered
- **THEN** the title and the actions `<div>` are on the same line
- **AND** the visual layout is byte-equivalent to today's

### Requirement: Credit-card stat link row wraps gracefully
The link row inside the "Créditos disponibles" stat card (containing the "Comprar más →" link and the "Facturación" billing-portal form) SHALL use `flex-wrap`, so its contents wrap onto a second line rather than overflowing the card on cramped widths or with longer translations.

#### Scenario: Link row wraps to two lines when the card is narrowed
- **GIVEN** the dashboard rendered with the credit-card stat card constrained to 240 px width
- **WHEN** the row is laid out
- **THEN** the "Comprar más →" link and the "Facturación" button render on two lines
- **AND** neither element extends past the card's right padding

### Requirement: File-input control is replaced by a styled label
The "Subir CV" form's `<input type="file">` SHALL be hidden visually (`class="sr-only"` while remaining keyboard-accessible) and presented through a styled `<label>` that visually matches the rest of the design system (brand button styling). The currently selected filename MUST be shown in Spanish (`Sin archivo seleccionado` when empty, otherwise the selected filename) in a sibling `<span>` updated by an inline `change` listener. The native browser-rendered `Choose File / No file chosen` text MUST NOT appear anywhere on the page.

#### Scenario: Initial state shows the Spanish placeholder
- **GIVEN** a logged-in user opens the dashboard
- **WHEN** the page first renders
- **THEN** the file-input control's visible label is the styled brand label
- **AND** the sibling filename span reads exactly `Sin archivo seleccionado`
- **AND** the rendered HTML contains no occurrence of the strings `Choose File` or `No file chosen` (verified via locale-independent test)

#### Scenario: After selecting a file, the filename appears
- **GIVEN** the dashboard is rendered and the user clicks the styled label
- **WHEN** the user picks `mi-cv.pdf` in the OS file picker
- **THEN** the filename span updates to `mi-cv.pdf`
- **AND** the underlying `<input type="file">` retains the selected file (so form submission proceeds normally)

### Requirement: Delete-account form stacks the destructive action below the back link on small viewports
On `templates/dashboard/delete_account.html`, the button row currently rendering "← Volver" on the left and the red "Eliminar permanentemente" button on the right SHALL stack the destructive button below the back link on viewports below 640 px (`flex-col-reverse sm:flex-row`). This both fixes the 2-line wrap of the destructive button at 320 px and reduces the chance of accidental destructive taps on mobile.

#### Scenario: Buttons stack with the destructive action below at 320 px
- **GIVEN** a logged-in user at viewport 320 × 800
- **WHEN** they navigate to `/dashboard/eliminar-cuenta/`
- **THEN** the "← Volver" link renders above the "Eliminar permanentemente" button
- **AND** both render on a single line each (no internal wrap)

#### Scenario: Buttons render side-by-side at 640 px
- **GIVEN** viewport 640 × 800
- **WHEN** the delete-account page is rendered
- **THEN** "← Volver" is on the left and "Eliminar permanentemente" is on the right
- **AND** the layout is byte-equivalent to today's
