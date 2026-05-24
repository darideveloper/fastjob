## ADDED Requirements

### Requirement: CV Deletion Blocked During Active Campaign

The `delete_cv` view and the dashboard template SHALL prevent a user from deleting any CV while their campaign is active. This is a server-side guard with a template-level visual hint for defence in depth.

#### Scenario: Server rejects deletion when campaign is active

- **GIVEN** a logged-in user whose `is_campaign_active` is `True`
- **WHEN** they submit `POST /dashboard/cv/<cv_id>/eliminar/` for any of their CVs
- **THEN** the view returns a redirect to the dashboard with an error flash message reading `"Para eliminar un CV, primero pausa tu campaña."`
- **AND** the CV row is NOT deleted from the database
- **AND** the S3 file is NOT removed
- **AND** `user.is_campaign_active` remains `True`
- **AND** `user.active_cv` is unchanged

#### Scenario: Server allows deletion when campaign is paused

- **GIVEN** a logged-in user whose `is_campaign_active` is `False`
- **WHEN** they submit `POST /dashboard/cv/<cv_id>/eliminar/`
- **THEN** the CV is deleted (row + S3 file per `pre_delete` signal)
- **AND** the existing fallback logic applies (switch `active_cv` to the most recent remaining CV, or pause if none)

#### Scenario: Delete button hidden in template when campaign is active

- **GIVEN** a logged-in user whose `is_campaign_active` is `True`
- **WHEN** the dashboard page is rendered
- **THEN** no "Eliminar" button is visible on any CV row in "Tus CVs"

#### Scenario: Delete button visible when campaign is paused

- **GIVEN** a logged-in user whose `is_campaign_active` is `False`
- **WHEN** the dashboard page is rendered
- **THEN** every CV row shows an "Eliminar" button (including the active CV, since deletion is always allowed when the campaign is paused — the existing fallback logic handles `active_cv` reassignment)