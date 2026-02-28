# Enterprise Deployment Guide (Azure)

## Containerization
The solution is split into two containers:
1. **Backend (FastAPI + Playwright)**: Handled by `Dockerfile.backend`. Exposes port 8000.
2. **Frontend (Next.js)**: Build using standard Next.js standalone output. Exposes port 3001.

## Azure Infrastructure Setup (Bicep/Terraform target)

**1. Azure Container Registry (ACR)**
* Host Docker images for both backend and frontend.

**2. Azure Cosmos DB (PostgreSQL / NoSQL)**
* Replace the local SQLite database defined in `quantum_qe_core/telemetry.py` with the Cosmos DB connection string in your Azure Vault.

**3. Azure Container Apps (ACA)**
* We recommend ACA as it provides a serverless microservice environment that scales to zero (to save costs) and can seamlessly scale up during heavy parallel QE agent execution.
* **Backend App**: Give it adequate memory to run headless Chromium instances natively (4GB+ RAM recommended per replica).
* **Frontend App**: Standard lightweight configuration (0.5 CPU, 1GB RAM).

**4. Azure API Management (APIM) / Front Door**
* Used to route traffic securely to the Web Interface.
* Implements rate limiting and Web Application Firewall (WAF) to prevent abuse.

## Continuous Integration
Setup a GitHub Action or Azure DevOps pipeline that:
1. Triggers on `main` branch push.
2. Builds Docker Images.
3. Pushes to ACR.
4. Triggers an Azure Container App Revision update.
