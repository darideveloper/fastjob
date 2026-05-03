# Requirements: Infrastructure

## ADDED Requirements

### Requirement: Private Storage Backend
- All user-uploaded files MUST be stored in a private-access storage bucket.

#### Scenario: Private File Upload
- Given a user uploading a CV or Company Excel
- When the file is saved to the system
- Then the file must be stored in the private S3 storage with `private` ACL
- And no public URL should be available for the file

### Requirement: Admin Secure Access
- Administrative access to private files SHALL be facilitated via signed URLs.

#### Scenario: Admin Access to Files
- Given an authenticated admin user
- When the admin requests a file URL
- Then the system must generate a time-limited signed URL
- And the admin must be able to view/download the file
