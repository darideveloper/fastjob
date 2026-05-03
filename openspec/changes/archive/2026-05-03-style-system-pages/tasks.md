# Tasks: Style System Pages

## [Phase 1] Theming Foundation
- [x] Refactor `templates/base.html` to centralize Tailwind theme configuration (colors and fonts).
  - **Validation**: Inspect `/` and `/accounts/login/` to ensure no visual regression.
- [x] Create `templates/404.html` and `templates/500.html`.
  - **Validation**: In `DEBUG=False` mode, visit a non-existent URL and trigger a dummy exception to verify styling.

## [Phase 2] Auth System Pages
- [x] Create `templates/account/logout.html`.
  - **Validation**: Click "Salir" in the navbar and verify the confirmation page is styled.
- [x] Create `templates/socialaccount/signup.html`.
  - **Validation**: Verify that social signup flow (when email is missing) shows styled card.
- [x] Create `templates/socialaccount/authentication_error.html`, `login_cancelled.html`, and `connections.html`.
  - **Validation**: Manually trigger error/cancel flows in social login to verify.

## [Phase 3] Cleanup & Verification
- [x] Final visual audit of all system pages.
- [x] Verify mobile responsiveness of all new pages.
  - **Validation**: Use browser devtools to check at 320px width.
