## ADDED Requirements
### Requirement: CV PDF Attachments
The mailing engine MUST attach the user's active CV as a PDF file directly to the outgoing email message for both Google and Microsoft providers. The attachment MUST be correctly encoded (base64) and specify the `application/pdf` content type. The system MUST gracefully handle file read errors if the physical file is missing from storage.

#### Scenario: Gmail sends email with PDF attachment
- **GIVEN** a user has an active CV file
- **WHEN** `_send_via_gmail` is called
- **THEN** the message payload is formatted as a `multipart/mixed` MIME message
- **AND** it contains an `application/pdf` attachment part with the correct filename.

#### Scenario: Microsoft Graph sends email with PDF attachment
- **GIVEN** a user has an active CV file
- **WHEN** `_send_via_microsoft` is called
- **THEN** the JSON payload contains an `attachments` array
- **AND** the array includes an item of type `#microsoft.graph.fileAttachment` containing the base64-encoded PDF content.

#### Scenario: Missing physical CV file pauses campaign
- **GIVEN** a user's active CV record points to a file that does not exist in storage
- **WHEN** `send_cv_email` is called
- **THEN** a `FileNotFoundError` or `OSError` is caught
- **AND** the user's campaign is paused (`is_campaign_active = False`)
- **AND** an exception is raised so the Celery worker marks the log as failed.