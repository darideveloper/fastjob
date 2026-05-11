# Allow Multiple Filters for Campaigns

## Why
Currently, a user can only select a single Area and a single Location to filter companies for their mailing campaign. This is too restrictive for users who want to target multiple sectors or cities without manual intervention.

## What Changes
- Update the `User` model to use `ManyToManyField` for `area_filters` and `location_filters`.
- Provide data migrations to preserve existing single-filter selections.
- Update the dashboard view to accept and save multiple values.
- Update the public company matching queries to use `__in` logic.
- Update the caching mechanism to handle lists of filters.
- Update the frontend combobox component to support a multi-select "pill" UI.
- Update the mailing engine to use the new multi-select fields.
- Update Django Admin to use `filter_horizontal` for the new fields.

## Summary
Broaden the reach of campaigns by allowing multiple simultaneous filter selections.

## Scope
- Update the `User` model to use `ManyToManyField` for `area_filters` and `location_filters`.
- Provide data migrations to preserve existing single-filter selections.
- Update the dashboard view to accept and save multiple values.
- Update the public company matching queries to use `__in` logic.
- Update the caching mechanism to handle lists of filters.
- Update the frontend combobox component to support a multi-select "pill" UI.
- Update the mailing engine to use the new multi-select fields.
- Update Django Admin to use `filter_horizontal` for the new fields.

## Out of Scope
- This change does not alter the overall slow-drip logic or rate limits.
- We are not adding any new taxonomies, just allowing multiple selections of existing ones.

## Dependencies
- Modifying `combobox.js` will require ensuring both the Landing Page and the Dashboard maintain their current functionality while adding multi-select visually.
