## Context

The user requested that the legal pages (specifically `/terminos/` and `/terms/`) align completely with the Spanish legal text provided by the compliance consultant (excluding the consultant metadata header). Currently, several required clauses regarding user consent, data retention, detailed AEPD cookie definitions, and Instagram page disclosures are missing or simplified in the last iteration of `templates/legal/terms.html`.

## Goals / Non-Goals

**Goals:**
- Update `templates/legal/terms.html` to include all missing legal blocks and detailed clauses.
- Expand cookie definitions to feature the full AEPD Spanish definitions.
- Incorporate explicit cookie banner layer rules (first, second, third layer and default denial).
- Add Instagram user profile data processing details.
- Update test cases to verify the presence of key new legal text blocks.

**Non-Goals:**
- Modify `templates/legal/privacy.html` (already verified as compliant).
- Implement functional cookie consent banner JavaScript or backend storage for cookie preferences.
- Modify URL routing or views.
- Add the consultant metadata header ("basquekide - Consultoría de Servicios Normativos", etc.) to the templates (as requested by the user).

## Decisions

### Decision 1: Inline HTML updates for terms.html
- **Choice**: Directly update the template text blocks in `templates/legal/terms.html`.
- **Rationale**: Simple, zero-overhead, and keeps it consistent with the existing static page structure.

### Decision 2: Update assertions in tests
- **Choice**: Update `apps/core/tests/test_views.py` (or other legal view tests) with assertions looking for key specific substrings of the new legal blocks.
- **Rationale**: Prevents regression and ensures that the correct compliance text remains present.

## Risks / Trade-offs

- **[Risk]**: Formatting issues or broken layout in terms page due to injected blocks.
  - *Mitigation*: Ensure all injected paragraphs use Tailwind's `prose` classes (`mt-2`, `list-disc`, etc.) matching the current styles in `terms.html`.
- **[Risk]**: Overlooking key sentences in Spanish.
  - *Mitigation*: Verify block-by-block matching against the user's provided document.
