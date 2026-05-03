# Change: Harden Filter Taxonomy and Managed UI Dropdowns

## Why
The current filter system in both the client dashboard and landing page relies on distinct values pulled dynamically from the `Company` table. This approach has several drawbacks:
1. **Data Integrity**: Typos or inconsistent casing in imported company data create duplicate or messy dropdown options.
2. **Admin Control**: There is no central way for administrators to curate the list of Sectors (Areas) and Locations.
3. **UX Inconsistency**: The Django Admin for User filters remains plain-text, allowing invalid values to be persisted.
4. **Visual Layout**: The company counter is currently detached from the filter inputs on the landing page, making the UI feel less cohesive.

## What
This proposal transitions the project to a **Managed Taxonomy** model.
1. **New Models**: Introduce `Area` and `Location` models in `apps.companies` to hold the curated list of available options.
2. **Schema Migration**: Convert `Company` and `User` filter fields from `CharField` to `ForeignKey`.
3. **Admin UI**: Add admin interfaces for managing the new taxonomy and update the `User` admin to use dropdowns.
4. **Frontend Refinement**: Adjust the Landing and Dashboard layouts to place the counter next to the filters and ensure the combobox widget is robust.
5. **Security**: Maintain rate-limiting and strictly validate all filter submissions against the managed taxonomy.

## Impact
- **Data Integrity**: All filters will strictly adhere to the admin-defined taxonomy.
- **Improved UX**: Staff can manage filters using dropdowns in the admin, and end-users get a more polished, integrated UI.
- **Scalability**: New sectors or locations can be added by an admin without needing to modify `Company` rows first.
- **Migration Effort**: Requires a data migration to populate the new models from existing `Company` data and update all existing references.
