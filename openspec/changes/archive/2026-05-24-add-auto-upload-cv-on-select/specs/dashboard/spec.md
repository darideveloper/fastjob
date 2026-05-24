# dashboard Spec Delta — add-auto-upload-cv-on-select

## MODIFIED Requirements

### Requirement: File-input control is replaced by a styled label
The "Subir CV" form's `<input type="file">` SHALL be hidden visually (`class="sr-only"` while remaining keyboard-accessible) and presented through a styled `<label>` that visually matches the rest of the design system (brand button styling). The label's visible text SHALL read `Subir CV (PDF)` to communicate that selecting a file performs the upload (there is no separate submit button — see "CV upload begins automatically on file selection"). A sibling `<span data-filename>` SHALL display the currently selected filename in Spanish (`Sin archivo seleccionado` when empty, otherwise the selected filename). The native browser-rendered `Choose File / No file chosen` text MUST NOT appear anywhere on the page. The form MUST NOT contain any `<button type="submit">`.

#### Scenario: Initial state shows the Spanish placeholder
- **GIVEN** a logged-in user opens the dashboard
- **WHEN** the page first renders
- **THEN** the file-input control's visible label reads `Subir CV (PDF)` and is the only visible control in the upload form
- **AND** the sibling filename span reads exactly `Sin archivo seleccionado`
- **AND** the rendered HTML contains no occurrence of the strings `Choose File` or `No file chosen` (verified via locale-independent test)
- **AND** the rendered HTML contains no `<button type="submit">` inside the upload form
- **AND** the rendered HTML contains no `<input type="text" name="name">` inside the upload form

#### Scenario: After selecting a file, the filename appears
- **GIVEN** the dashboard is rendered and the user clicks the styled label
- **WHEN** the user picks `mi-cv.pdf` in the OS file picker
- **THEN** the filename span updates to `mi-cv.pdf`
- **AND** the underlying `<input type="file">` retains the selected file

### Requirement: Unified form-control styling on dashboard inputs
Every `<input>`, `<select>`, and `<textarea>` on `templates/dashboard/index.html` and `templates/dashboard/delete_account.html` SHALL share the same visual treatment: `bg-white border border-brand-muted rounded-lg px-3 py-2 text-brand-ink focus:outline-none focus:ring-2 focus:ring-brand-ring focus:border-brand`. The combobox widgets (`data-combobox="area"` / `"location"`) MUST adopt the same focused appearance via their existing JavaScript controller (no behavior change to the controller itself).

#### Scenario: All dashboard inputs share the same focus ring
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they Tab through every form field, including the combobox widgets and any input on the delete-account page
- **THEN** each focused field renders an outline using `brand.ring` and a `brand.DEFAULT` border color
- **AND** no field exhibits a different focus color or border treatment

## ADDED Requirements

### Requirement: CV upload begins automatically on file selection
Selecting a file via the `#cv-file-input` element on `/dashboard/` SHALL begin the upload immediately, without any further user action. The form MUST NOT expose a submit button. Client-side validation (extension `.pdf` case-insensitive, size ≤ 10 MB) SHALL run before any network request, and on failure SHALL surface an inline Spanish error in a sibling `<p data-upload-status>` element, reset `input.value = ""` so the same file can be re-picked, and not contact the server. On a valid selection, the page SHALL POST `multipart/form-data` (containing `cv_file` and `csrfmiddlewaretoken`) to the existing `{% url 'upload_cv' %}` endpoint with header `X-Requested-With: XMLHttpRequest`, display the status message `Subiendo…`, and disable the upload label while the request is in flight. On HTTP `200`, the page SHALL fully reload so the server re-renders the CV list, the "Activo" highlight, and Django flash messages from the canonical view. On a non-`2xx` response, the JSON `error` string SHALL be displayed inline in red, the label re-enabled, and `input.value` reset so the user can retry. The `upload_cv` view SHALL continue to accept ordinary (non-AJAX) form posts and respond with the existing redirect + flash-message behavior, so the feature degrades gracefully when JavaScript is disabled.

#### Scenario: Valid PDF triggers upload without an extra click
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they pick `mi-cv.pdf` (≤ 10 MB) in the OS file picker
- **THEN** no submit button click is required
- **AND** the inline status region reads `Subiendo…` while the request is in flight
- **AND** the browser issues exactly one POST to `/dashboard/subir-cv/` with header `X-Requested-With: XMLHttpRequest` containing `cv_file` and `csrfmiddlewaretoken`
- **AND** on `200 {"ok": true}` the page reloads, the new CV appears in "Tus CVs" marked as active, and the green Django success toast `CV subido correctamente.` is shown

#### Scenario: Wrong file type is rejected client-side with no network request
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they pick a `.txt` file in the OS file picker
- **THEN** the inline status region shows `Solo se permiten archivos PDF.` in red
- **AND** no network request is issued
- **AND** the file input value is cleared so the user can immediately pick another file (including the same one again)

#### Scenario: Oversize PDF is rejected client-side with no network request
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they pick a PDF larger than 10 MB
- **THEN** the inline status region shows `El archivo no puede superar los 10 MB.` in red
- **AND** no network request is issued
- **AND** the file input value is cleared

#### Scenario: Server-side validation failure surfaces inline
- **GIVEN** a logged-in user on `/dashboard/` whose client-side checks pass
- **WHEN** the AJAX request returns `400 {"ok": false, "error": "Por favor selecciona un archivo PDF."}`
- **THEN** the inline status region displays exactly that Spanish error in red
- **AND** the upload label is re-enabled
- **AND** the file input value is cleared so the user can retry
- **AND** the page does NOT reload

#### Scenario: Non-AJAX submission still works (no-JS fallback)
- **GIVEN** a client without JavaScript (or any client omitting the `X-Requested-With` header)
- **WHEN** they POST a valid PDF to `/dashboard/subir-cv/` with a valid CSRF token
- **THEN** the response is a `302` redirect to `/dashboard/`
- **AND** the next page render includes the Django success flash message `CV subido correctamente.`
- **AND** the new CV is created and set as the user's active CV
