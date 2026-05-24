# Change: Auto-upload CV the moment a file is selected

## Why
The current "Subir CV" form on `/dashboard/` is a two-step interaction: the user clicks the styled label to open the file picker, picks a PDF, and then must also click a second "Subir CV" submit button. This extra click is friction that adds no value — once the user has picked a file the intent is unambiguous. Removing the submit button and uploading immediately on `change` shortens the path from "I want to add a CV" to "the CV is active" by one full click and one full server round-trip / page reload that the user has to wait for explicitly.

The optional "Nombre" text input that today accompanies the form will also be removed: very few users fill it (the model accepts an empty `name` and `CV.__str__` already falls back to the filename), and keeping it would either delay the auto-upload (waiting for the user to type) or quietly drop their input (uploading before they finish typing). Removing it eliminates that ambiguity.

## What Changes
- **Template** (`templates/dashboard/index.html` lines 162–195):
  - Remove the `<input type="text" name="name" ...>` field (the optional CV-name input).
  - Remove the `<button type="submit">Subir CV</button>`.
  - Repurpose the styled `<label for="cv-file-input">` as the only control. Update its visible text to read `Subir CV (PDF)` (since it now triggers both selection *and* upload).
  - Add a small inline status region (e.g. `<p data-upload-status>`) directly under the picker, hidden by default. It surfaces "Subiendo…", success confirmation, or error text.
  - Replace the inline `<script>` (lines 177–189) with one that listens for `change` on `#cv-file-input`, runs client-side validation (extension `.pdf`, size ≤ 10 MB), POSTs via `fetch()` with the existing CSRF token and an `X-Requested-With: XMLHttpRequest` header, reloads the page on success, and surfaces inline errors on failure while resetting `input.value = ""` so the user can retry.
- **View** (`apps/dashboard/views.py` lines 53–79, `upload_cv`):
  - Branch on `request.headers.get("x-requested-with") == "XMLHttpRequest"`.
  - For AJAX: return `JsonResponse({"ok": True})` on success and `JsonResponse({"ok": False, "error": "<spanish msg>"}, status=400)` for each validation failure — reusing the existing Spanish strings.
  - For non-AJAX: keep the current `messages.* + redirect("dashboard")` behavior intact as a no-JS fallback (the endpoint must still accept ordinary form posts so progressive enhancement holds).
  - Drop the `label = (request.POST.get("name") or "").strip()[:200]` line and pass `name=""` to `CV.objects.create(...)` (the model tolerates this).
- **No model, URL, or migration changes.**
- **Tests**: add coverage for the new JSON branch of `upload_cv` (AJAX success, AJAX wrong-type, AJAX too-big) and confirm the non-AJAX fallback still issues a redirect with a flash message.

## Impact
- **Affected specs**: `dashboard`
  - MODIFIED: `File-input control is replaced by a styled label` — submit button removed, label text changes, filename span repurposed for status.
  - MODIFIED: `Unified form-control styling on dashboard inputs` — the existing scenario references "the CV-name input"; that wording must be removed since the input no longer exists.
  - ADDED: `CV upload begins automatically on file selection` — new behavior contract for client-side validation, the `fetch()` upload, the success reload, and inline error surfacing.
- **Affected code**:
  - `templates/dashboard/index.html`
  - `apps/dashboard/views.py`
  - `apps/dashboard/tests/` (new test cases for the JSON branch)
- **No breaking changes**: the endpoint URL (`/dashboard/subir-cv/`, name `upload_cv`) is unchanged, the validation rules are unchanged, and a plain non-AJAX POST still works exactly as today (preserving the no-JS fallback).
- **Risk**: low. CSRF is preserved by including the existing `{% csrf_token %}` and forwarding `csrfmiddlewaretoken` in the FormData. Server-side validation remains authoritative; client-side checks are a UX optimization only.
