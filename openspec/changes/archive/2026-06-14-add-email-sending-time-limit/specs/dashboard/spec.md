## ADDED Requirements

### Requirement: Time Window Pause Feedbacks in Dashboard
The dashboard index view SHALL query the `SystemSettings` singleton and inject its values into the template context. The dashboard template MUST display the configured start and end times in the warning banner when `campaign_pause_reason` is `"time_window"`.

#### Scenario: Time window banner rendering
- **GIVEN** a user with `campaign_pause_reason = "time_window"`
- **WHEN** the user views their dashboard
- **THEN** they see an alert banner explaining that the campaign is paused for off-hours
- **AND** the banner displays the start and end times of the active sending window.

### Requirement: Manual Campaign Toggle Off-Hours Check
The `toggle_campaign` view SHALL verify whether the current local time is inside the sending window when starting a campaign. If it is outside active hours, the campaign MUST be set to `is_campaign_active = False` with `campaign_pause_reason = "time_window"`, and a success message indicating scheduling MUST be shown. If a stop action is received when in a `"time_window"` pause state, the view MUST set `is_campaign_active = False` and clear the `campaign_pause_reason` field.

#### Scenario: Manually starting campaign during off-hours
- **GIVEN** a user with a valid CV, connected provider, and remaining credits
- **AND** the current local time is outside the configured sending hours window
- **WHEN** the user clicks "Start Campaign"
- **THEN** the campaign is saved with `is_campaign_active = False`
- **AND** `campaign_pause_reason = "time_window"`
- **AND** a success message explains that the campaign is scheduled for on-hours
- **AND** no pause notification email is sent.

#### Scenario: Manually stopping campaign during off-hours pause
- **GIVEN** a user with `campaign_pause_reason = "time_window"`
- **WHEN** the user clicks "Pausar Campaña"
- **THEN** the campaign is saved with `is_campaign_active = False`
- **AND** `campaign_pause_reason = ""`
- **AND** a success message explains that the campaign has been paused.

### Requirement: Active Campaign Hour Visibility
The dashboard index view SHALL query the `SystemSettings` singleton and inject its values into the template context. When `is_campaign_active` is `True`, the dashboard MUST display the configured start and end times of the active sending window in the header/toggle area to inform the user when their emails will be delivered.

#### Scenario: Active campaign hours display
- **GIVEN** a user with an active campaign (`is_campaign_active = True`)
- **WHEN** the user views their dashboard
- **THEN** they see the configured active sending window start and end times in the header.


