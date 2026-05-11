# Proposal: Fix Company Counter Updates

## Why
The company counter is currently broken in both the Landing Page and the Dashboard because:
1. The Landing Page template is missing the metadata (`data-name`) required to initialize the filter logic.
2. The JavaScript logic conditionally skips creating hidden inputs when no form name is provided, which prevents the counter from finding the selection state.
3. The API has strict case-sensitivity and whitespace validation that can cause valid taxonomy matches to fail.

## What Changes
- Update `static/js/combobox.js` to always track state via hidden inputs.
- Add missing `data-name` attributes to `templates/home.html`.
- Harden `companies_count_view` in `apps/companies/views.py` with better string stripping.

## Objective
Ensure the company counter updates correctly in both the Landing Page and the Dashboard. The current implementation fails primarily because the Landing Page template is missing metadata required by the JavaScript logic, and the JavaScript logic conditionally skips creating the elements that the counter logic depends on.

## Scope
1.  **Frontend (JS)**: Update `static/js/combobox.js` to always persist selected values in hidden inputs, regardless of whether a form `name` is provided. This ensures the counter logic can always find the current selection state in the DOM.
2.  **Template**: Add `data-name` attributes to the filter containers in `templates/home.html` to align with the Dashboard and ensure the JS initialization is consistent.
3.  **Backend (API)**: Harden the `companies_count_view` in `apps/companies/views.py` to be resilient against trailing whitespace in both the user input and the allowed options list.

## Design
The `combobox.js` script currently wraps the "pills" and hidden inputs inside a logic block that requires `data-name` to be present. We will decouple the creation of these hidden inputs from the requirement of having a form-submission name. This allows `scheduleCount` to reliably query `input[type=hidden]` to build its count request.

On the backend, while the validation is already case-insensitive, we will add `.strip()` to the allowed options set creation to prevent mismatches caused by accidental leading/trailing spaces in the database taxonomy.