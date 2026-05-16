## 1. Implementation

- [x] 1.1 In `apps/mailing/models.py`, inside `EmailTemplate.render()`, change `company_name=company_name` to `company_name=company_name.upper()` in the `SafeDict` constructor (line ~133).

## 2. Tests

- [x] 2.1 In `apps/mailing/tests/test_template_render.py`, update `test_known_placeholders_resolve_to_values` to assert `"hi ACME"` and `"u: http://u"` (body unchanged because it uses `{unsubscribe_url}`, not `{company_name}`).
- [x] 2.2 Add `test_company_name_is_uppercased_in_subject` — calls `render(company_name="Acme Corp", ...)` with a subject containing `{company_name}` and asserts the returned subject contains `"ACME CORP"`.
- [x] 2.3 Add `test_company_name_is_uppercased_in_body` — same but checks the HTML body placeholder.
- [x] 2.4 Add `test_company_name_uppercase_is_idempotent` — passes an already-uppercase name and asserts no change.

## 3. Validation

- [x] 3.1 Run `pytest apps/mailing/tests/test_template_render.py -v` — all tests must pass.
- [x] 3.2 Run `openspec validate uppercase-company-name-in-emails --strict` — zero issues.
