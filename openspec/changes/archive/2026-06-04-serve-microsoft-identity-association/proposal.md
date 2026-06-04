# Serve Microsoft Identity Association JSON

## Context
FastJob uses Microsoft OAuth for user authentication and sending emails. To validate application ownership and domain association for Microsoft login, a specific JSON file must be served at the `/.well-known/microsoft-identity-association.json` endpoint.

## Proposed Change
Add a Django view to serve the `microsoft-identity-association.json` file. The JSON payload contains the Microsoft `applicationId` associated with the FastJob application. This view will be routed to `/.well-known/microsoft-identity-association.json` in the main URL configuration.

## Architectural Reasoning
Serving the file via a Django view (returning a `JsonResponse`) is a clean, self-contained approach that does not require modifications to the proxy (Nginx/Traefik) or the deployment infrastructure (Coolify). It ensures the file is available consistently across all environments (local, staging, production) directly from the application code without maintaining a static file.
