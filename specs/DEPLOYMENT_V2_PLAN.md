# Deployment Plan: AI-CRM v2.0 with Authentication

This document outlines the plan to deploy the new version of the AI-CRM application, which includes the full user authentication and subscription tier system.

## 1. Objectives
- Successfully deploy the AI-CRM v2.0 to the production environment at `https://crm.zae.life`.
- Ensure the new authentication system is functioning correctly.
- Verify that all existing features are still working as expected.

## 2. Pre-Deployment Checklist
- [ ] All code changes have been reviewed and merged to the `main` branch.
- [ ] All unit and integration tests are passing.
- [ ] The production environment has been configured with the necessary secrets (e.g., `DATABASE_URL`, `SECRET_KEY`).
- [ ] A backup of the production database has been taken.

## 3. Deployment Strategy
The deployment will be performed using the alternative Docker Compose strategy, as the Terraform environment is not available.

### 3.1. Build and Push Docker Images
- **Action:** Build the production-ready Docker images for the `frontend` and `backend` services.
- **Action:** Push the new images to a container registry (e.g., Docker Hub, GitHub Container Registry).

### 3.2. Deploy to Production Server
- **Action:** SSH into the production server.
- **Action:** Pull the latest Docker images.
- **Action:** Stop the currently running application.
- **Action:** Start the new version of the application using `docker-compose.prod.yml`.

## 4. Post-Deployment Verification
- **Action:** Verify that the application is accessible at `https://crm.zae.life`.
- **Action:** Perform the end-to-end tests outlined in `TEST_PLAN.md`.
- **Action:** Monitor the application logs for any errors.

## 5. Rollback Plan
In the event of a critical issue, the rollback plan is as follows:
- Re-deploy the previous version of the Docker images.
- Restore the database from the backup.
