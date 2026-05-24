# mailing Spec Delta — refresh-landing-shell-and-cv-attachment-copy

## ADDED Requirements

### Requirement: Legacy CV-link error pages use attachment-era neutral copy
The two templates rendered by the legacy `cv_download` view (`templates/mailing/cv_not_found.html` and `templates/mailing/cv_revoked.html`) SHALL use copy that does NOT reference the prior link-based delivery flow, and the strings `enlace de descarga`, `enlaces de descarga`, `Descarga revocada`, and `La descarga ya no está disponible` MUST NOT appear in the rendered HTML of these two templates after this change. The `cv_download` view, its URL route (`/cv/<uuid:token>/`), and the `MailingLog.cv_download_token` field remain in place so historical email links from the pre-attachment era keep resolving to a graceful, neutral page — the page can still say "este enlace ya no está disponible", it just must not characterise the prior flow as a "descarga".

This requirement complements (but does not replace) the existing
`Email-landing card layout (cv_not_found / cv_revoked / unsubscribe pages)`
requirement in `openspec/specs/mailing/spec.md`, which still governs the
visual chrome (card layout, logo placement, max-width caps). Only the
**copy** changes here, not the chrome.

#### Scenario: cv_not_found.html copy contains no link-era wording
- **WHEN** any client requests `GET /cv/<unknown-or-invalid-token>/`
- **AND** Django renders `templates/mailing/cv_not_found.html`
- **THEN** the rendered HTML body does NOT contain the case-insensitive
  substring `enlace de descarga`
- **AND** the subtitle paragraph reads `Este enlace ya no está disponible o ha expirado.`
- **AND** the page still extends `base.html` and preserves the card
  chrome required by the existing email-landing layout requirement

#### Scenario: cv_revoked.html copy contains no link-era wording
- **WHEN** any client follows a `MailingLog` link whose recipient has
  unsubscribed (per the existing `cv_download` blacklist-gate requirement
  in `openspec/specs/mailing/spec.md`)
- **AND** Django renders `templates/mailing/cv_revoked.html`
- **THEN** the `<title>` element reads `Enlace revocado — FastJob`
  (replacing the prior `Descarga revocada — FastJob`)
- **AND** the rendered HTML body does NOT contain the case-insensitive
  substrings `Descarga revocada` or `La descarga ya no está disponible`
- **AND** the subtitle paragraph reads
  `Este enlace ya no está disponible porque el destinatario ha cancelado la suscripción.`
- **AND** the existing blacklist behaviour (governed by the `cv_download`
  blacklist-gate requirement in `openspec/specs/mailing/spec.md`) is
  unchanged — only the visible copy on the rendered page differs
