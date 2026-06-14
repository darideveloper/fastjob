## 1. Terms Template Updates

- [x] 1.1 Update Section 1 (Información General del Titular) of `templates/legal/terms.html` to add the warning requiring users to abstain from using the site if they do not accept the terms.
- [x] 1.2 Update Section 5 (Datos Personales y Advertencia de Seguridad) of `templates/legal/terms.html` to add the missing data protection clauses (voluntariness, consequence of non-authorization, information expansion email link, detailed automated database storage, and purpose limitation).
- [x] 1.3 Update Section 7 (Uso de Cookies) of `templates/legal/terms.html` to add specific cookie properties list items (anonymous association, user recognition, cross-provider reading exclusion, browser settings warnings).
- [x] 1.4 Update Section 7 (Clasificación) of `templates/legal/terms.html` to expand the cookie classifications with full AEPD Spanish definitions.
- [x] 1.5 Update Section 7 (Eliminación) of `templates/legal/terms.html` to add the individual browser cookie deletion introductory text and the AEPD guidance link.
- [x] 1.6 Update Section 7 (Consentimiento) of `templates/legal/terms.html` to add the detailed cookie banner layers list (first, second, third layer and default denial).
- [x] 1.7 Update Section 8 (Redes Sociales) of `templates/legal/terms.html` to add the explicit profile data consent clause for Instagram.
- [x] 1.8 Update Section 9 (Normativa Legal) of `templates/legal/terms.html` to add the LSSI-CE 34/2002 updateability and modification clauses.

## 2. Testing & Verification

- [x] 2.1 Update test cases in `apps/core/tests/test_views.py` (or other legal view tests) to assert the presence of new specific legal clauses in the terms view response.
- [x] 2.2 Run the test suite via `pytest` to verify all footer link and legal views tests pass.
