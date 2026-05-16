# Change: Uppercase company name in outgoing email templates

## Why
Company names rendered inside CV-campaign emails currently appear in mixed case, matching whatever casing is stored in the database. Rendering them in uppercase makes subject lines and salutations visually consistent and more impactful, reinforcing a professional brand tone throughout every sent email.

## What Changes
- `EmailTemplate.render()` in `apps/mailing/models.py` will call `.upper()` on the `company_name` argument before inserting it into the `SafeDict` context, so every `{company_name}` placeholder resolves to an uppercased string.
- The transformation is applied in Python — no template markup is modified; stored template bodies remain unchanged.
- The admin preview (sample context in `apps/mailing/admin.py`) is unaffected because it passes a hardcoded string whose casing is irrelevant to the preview's purpose.

## Impact
- **Affected specs**: `mailing`
- **Affected code**: `apps/mailing/models.py` (single line, `render()` method); `apps/mailing/tests/test_template_render.py` (existing test fixtures use `"Acme"` — assertions must reflect the uppercased output `"ACME"`)
- **No breaking changes**: stored templates and the DB schema are untouched; all existing `{company_name}` placeholders continue to resolve, now to uppercased values.
