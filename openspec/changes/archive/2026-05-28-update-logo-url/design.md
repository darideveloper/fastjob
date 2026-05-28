# Design: Update Company Logo URL

This document outlines the architectural reasoning and implementation strategy for updating the company logo URL across the FastJob platform.

## Current State
The company logo for emails is currently hardcoded with a default value pointing to `https://raw.githubusercontent.com/daridev/fastjob/main/static/images/fastjob-logo.png`. This value is used in:
1. `SystemSettings` model default.
2. Initial migration (`0014`) for `SystemSettings`.
3. Multiple test cases across different apps (`mailing`, `payments`, `accounts`, `dashboard`) that assert the presence of this specific URL in rendered emails.

## Proposed Change
Transition all references to the new official URL: `https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png`.

## Implementation Strategy

### 1. Model and Migration
- Update the `default` and `verbose_name` in `apps/mailing/models.py`. The `verbose_name` will be aligned to `"URL del logo en emails"` as per the base specification, replacing the current `"URL del logo de email"`.
- Create a new migration in `apps/mailing/`. This migration will:
  - Update the `default` on the field and its `verbose_name`.
  - Run a `RunPython` operation to update the existing `SystemSettings` singleton record (ID=1) if it currently has the old URL.

### 2. Test Alignment
Tests in FastJob often verify that emails are correctly branded by checking for the logo URL. These tests must be updated to avoid regression failures. All identified test files will be updated to use the new URL.

### 3. Verification
Run `pytest` on all affected modules to ensure the change is correctly propagated and branding is still functional.

## Trade-offs
- **Hardcoding vs. Configuration**: While `SystemSettings` allows admin overrides, the system still relies on a sane default. Hardcoding the default in the model is standard Django practice, but it requires code changes to update. Given the logo changes rarely, this is acceptable.
- **Data Migration**: We must ensure existing installations receive the new URL. A simple model change only affects *new* records. Since `SystemSettings` is a singleton created by migration `0014`, we must explicitly update that record.
