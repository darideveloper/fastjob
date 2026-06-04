## ADDED Requirements

### Requirement: Microsoft Identity Association
The system MUST serve the Microsoft identity association JSON file at the `/.well-known/microsoft-identity-association.json` endpoint. This file validates the application's domain ownership for Microsoft OAuth integrations. The endpoint MUST return a JSON response with the `application/json` content type containing the FastJob Microsoft `applicationId` in the `associatedApplications` array.

#### Scenario: Validating Microsoft Identity Association endpoint
- **GIVEN** an anonymous client
- **WHEN** the client issues a `GET` request to `/.well-known/microsoft-identity-association.json`
- **THEN** the response status code is `200 OK`
- **AND** the `Content-Type` header is `application/json`
- **AND** the response body contains `{"associatedApplications": [{"applicationId": "3853b95b-027f-4c59-94e4-d697b2a603a9"}]}`
