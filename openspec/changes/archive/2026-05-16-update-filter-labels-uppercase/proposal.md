# Change: Display filter option labels in uppercase across all filter widgets

## Why
Filter options (sector/área and location) are stored lowercase in the database for normalisation
purposes. Displaying them in lowercase in the UI looks inconsistent with the overall visual design.
Showing them in UPPERCASE improves visual hierarchy and makes the filter labels feel more polished
without any data-model or backend changes.

## What Changes
- The Dashboard filter widget renders pill labels and dropdown option items in uppercase via
  `text-transform: uppercase` CSS rules injected into `templates/dashboard/index.html`.
- The change is purely presentational: form values submitted to the backend and used for whitelist
  validation remain lowercase (the hidden `<input>` values are unaffected by CSS).
- Scoped to the Dashboard only via `{% block extra_head %}` — the Landing page combobox is not
  affected.

## Impact
- Affected specs: `dashboard`
- Affected code: `templates/dashboard/index.html` (`{% block extra_head %}` with scoped CSS
  selectors `[data-combobox] .flex-wrap > div` and `[data-combobox] ul > li`)
- No backend, model, API, or test changes required.
- No breaking changes.
