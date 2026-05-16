# accounts delta

## ADDED Requirements

### Requirement: Unified auth-card chrome across login, logout, and socialaccount screens
The templates `account/login.html`, `account/logout.html`, `socialaccount/authentication_error.html`, `socialaccount/login_cancelled.html`, `socialaccount/connections.html`, and `socialaccount/signup.html` SHALL each render their primary content inside a single centered card on the `brand.bg` page background. The card SHALL use the shared chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`), MUST be horizontally centered (`mx-auto`), and MUST cap its width at `max-w-md` on viewports `< lg` and `max-w-lg` at `lg` and above. The FastJob logo (the same `<picture>` asset used by `base.html`'s navbar) SHALL appear above the card title, rendered with `class="h-12 w-auto"` so the rendered height anchors layout and width follows the asset's intrinsic 2.72 : 1 ratio.

`account/login.html` already provides the card chrome (`border-gray-100`); the apply stage migrates the border class to `border-brand-muted` and inserts the logo `<picture>` above the existing `<h1>Bienvenido a FastJob</h1>`.

#### Scenario: Login page uses the unified card chrome
- **GIVEN** an anonymous visitor on `/accounts/login/`
- **WHEN** the page is rendered
- **THEN** the OAuth provider chooser is contained within a single centered card whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, `shadow-sm`
- **AND** the FastJob logo `<picture>` is rendered above the card title with `class="h-12 w-auto"`
- **AND** the card is centered horizontally and limited to `max-w-md` at viewport 375 px

#### Scenario: All listed templates share the same chrome
- **WHEN** each of `/accounts/login/`, `/accounts/logout/`, `/accounts/3rdparty/`, and the allauth error/cancelled pages is rendered
- **THEN** each contains a centered card with the same chrome class set (`bg-white border border-brand-muted rounded-2xl shadow-sm`)
- **AND** each renders the FastJob logo above its title

### Requirement: OAuth provider buttons preserve vendor branding
On `account/login.html`, the "Continuar con Google" and "Continuar con Microsoft" buttons MUST NOT be re-skinned in `brand.*` palette colors. Google's button SHALL preserve its existing white-fill / vendor-color-icon / slate-text treatment (matching Google's identity guidelines). Microsoft's button SHALL preserve its existing white-fill / vendor-color-icon / slate-text treatment (matching Microsoft's identity guidelines). The button labels MUST remain exactly `Continuar con Google` and `Continuar con Microsoft` (the existing Spanish copy at `account/login.html:22,33`); they MUST NOT be re-translated to "Sign in with…". Both buttons MUST still meet the WCAG AA contrast and the 44-px touch-target invariant.

#### Scenario: Vendor buttons are not skinned in brand colors
- **WHEN** `/accounts/login/` is rendered
- **THEN** neither the Google nor the Microsoft button has its `background-color` resolved to `brand.DEFAULT`, `brand.dark`, or `brand.cyan`
- **AND** each button renders its vendor-correct color icon (Google "G" in vendor colors; Microsoft squares in vendor colors)
- **AND** each button's label is exactly `Continuar con Google` or `Continuar con Microsoft`
- **AND** each button has computed dimensions ≥ 44 × 44 px at viewport 375 px

### Requirement: Auth error states use brand palette (not semantic red)
The `socialaccount/authentication_error.html` and `socialaccount/login_cancelled.html` templates SHALL convey their state using a Cobalt-leaning icon (`text-brand-dark`) and a slate body (`text-brand-ink`) rather than red. A single primary-fill CTA labelled `Volver a iniciar sesión` SHALL link back to `/accounts/login/`. Semantic red is reserved for destructive intent (e.g. delete account); auth flow errors are framed as recoverable, not destructive.

#### Scenario: Auth-error template renders without semantic red
- **WHEN** `socialaccount/authentication_error.html` is rendered
- **THEN** no element on the page has a computed color or background-color matching the project's semantic red tokens (`bg-red-50`, `bg-red-600`, `text-red-700`, etc.)
- **AND** the page's icon resolves to `brand.dark`
- **AND** a single primary-fill CTA labelled `Volver a iniciar sesión` points to `/accounts/login/`
