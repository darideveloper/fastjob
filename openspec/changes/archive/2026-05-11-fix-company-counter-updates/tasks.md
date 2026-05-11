# Tasks

## 1. Implementation
- [x] 1.1 Harden `companies_count_view` in `apps/companies/views.py` by adding `.strip()` to both allowed options and input values.
- [x] 1.2 Update `static/js/combobox.js` to create hidden inputs regardless of the `name` attribute being present.
- [x] 1.3 Add `data-name="area"` and `data-name="location"` to filter containers in `templates/home.html`.

## 2. Verification
- [x] 2.1 Verify Landing Page counter updates from 577k to a lower number when a sector is selected using Playwright.
- [x] 2.2 Verify Landing Page counter updates correctly with multiple sectors.
- [x] 2.3 Verify Dashboard counter updates correctly.