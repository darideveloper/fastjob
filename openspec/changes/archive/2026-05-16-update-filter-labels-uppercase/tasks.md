## 1. Implementation

- [x] 1.1 In `templates/dashboard/index.html` add a `{% block extra_head %}` block with scoped CSS:
       `[data-combobox] .flex-wrap > div { text-transform: uppercase; }` (targets pills).
- [x] 1.2 In `templates/dashboard/index.html` add to the same block:
       `[data-combobox] ul > li { text-transform: uppercase; }` (targets dropdown option items).

## 2. Validation

- [ ] 2.1 Manually verify the Dashboard (`/dashboard/`) — open the Sector and Location dropdowns
       and confirm options render in UPPERCASE; select one and confirm the pill label is UPPERCASE.
- [ ] 2.2 Confirm that submitting the dashboard filter form still saves correctly (form hidden
       input values remain lowercase, server accepts them against the whitelist).
- [ ] 2.3 Confirm the search/filter-within-dropdown still works (type a lowercase term, matching
       options still appear — case-insensitive matching in `showDropdown` is unaffected by CSS).
