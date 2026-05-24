# Tasks

## 1. Backend: dual-mode upload_cv view
- [x] 1.1 In `apps/dashboard/views.py`, add `JsonResponse` to the existing `django.http` import.
- [x] 1.2 In `upload_cv`, compute `is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"` at the top of the function.
- [x] 1.3 Replace each `messages.error(...) + redirect("dashboard")` validation branch (missing file, non-PDF, >10 MB) with a helper that returns `JsonResponse({"ok": False, "error": <msg>}, status=400)` when `is_ajax`, else the existing redirect-with-flash behavior. Reuse the exact Spanish strings.
- [x] 1.4 Drop the `label = (request.POST.get("name") or "").strip()[:200]` line; call `CV.objects.create(user=user, file=cv_file, name="")`.
- [x] 1.5 On the success path, return `JsonResponse({"ok": True})` when `is_ajax`, else the existing `messages.success + redirect("dashboard")`.

## 2. Backend: tests
- [x] 2.1 Add a test that POSTs a valid PDF to `/dashboard/subir-cv/` with `HTTP_X_REQUESTED_WITH="XMLHttpRequest"` and asserts `200` + `{"ok": true}` + a new `CV` row is created and set active.
- [x] 2.2 Add a test that POSTs no file as AJAX and asserts `400` + `{"ok": false, "error": "Por favor selecciona un archivo PDF."}`.
- [x] 2.3 Add a test that POSTs a `.txt` file as AJAX and asserts `400` + the "Solo se permiten archivos PDF." message.
- [x] 2.4 Add a test that POSTs an oversize file as AJAX and asserts `400` + the 10 MB message.
- [x] 2.5 Add a regression test that the non-AJAX path (no `X-Requested-With` header) still returns a 302 redirect to `/dashboard/` with a flash message — covering both success and one error case.

## 3. Template: form simplification
- [x] 3.1 In `templates/dashboard/index.html`, remove the `<input type="text" name="name" ...>` (the optional CV-name input around line 164).
- [x] 3.2 Remove the `<button type="submit">Subir CV</button>` block.
- [x] 3.3 Update the styled `<label for="cv-file-input">` visible text from `Seleccionar archivo` to `Subir CV (PDF)`.
- [x] 3.4 Keep `{% csrf_token %}`, the hidden `<input type="file" required>`, and the `<span data-filename>` element.
- [x] 3.5 Add a `<p data-upload-status hidden>` directly below the picker row, styled for both neutral ("Subiendo…") and error (red) states.

## 4. Template: auto-upload script
- [x] 4.1 Replace the existing inline `<script>` (filename-display only) with one that listens for `change` on `#cv-file-input`.
- [x] 4.2 On `change`, perform client-side validation: file must end in `.pdf` (case-insensitive) and `file.size <= 10 * 1024 * 1024`. On failure, write the matching Spanish error to `[data-upload-status]`, reset `input.value = ""`, and return without making a request.
- [x] 4.3 On valid file, set `[data-upload-status]` to `Subiendo…`, disable the styled label (e.g. add `pointer-events-none opacity-50`), build a `FormData` with `cv_file` and `csrfmiddlewaretoken`, and POST to `{% url 'upload_cv' %}` with header `X-Requested-With: XMLHttpRequest`.
- [x] 4.4 On `response.ok`, call `window.location.reload()` so the CV list, "Activo" highlight, and Django flash message re-render via the existing server path.
- [x] 4.5 On non-ok response, parse `data.error`, display it in red inside `[data-upload-status]`, re-enable the label, and reset `input.value = ""` so the user can retry with another file.

## 5. Spec & validation
- [x] 5.1 Confirm the delta file at `openspec/changes/add-auto-upload-cv-on-select/specs/dashboard/spec.md` matches final implementation choices.
- [x] 5.2 Run `openspec validate add-auto-upload-cv-on-select --strict` and resolve any reported issues.

## 6. Manual verification
- [x] 6.1 `python manage.py runserver`, log in, open `/dashboard/`, pick a valid PDF — verify the page reloads, the new CV appears as active, and the success toast shows.
- [x] 6.2 Pick a `.txt` file — verify the inline red error appears immediately with no network request and the picker is ready to retry.
- [x] 6.3 Pick a >10 MB PDF — verify the inline 10 MB error appears and no upload starts.
- [x] 6.4 Disable JS in DevTools and POST to the endpoint via curl/a manual form — verify the redirect + flash path still works (no-JS regression).
- [x] 6.5 Inspect the upload request in DevTools Network tab — confirm `csrfmiddlewaretoken` is present in the form data and the response is `200 {"ok": true}`.
