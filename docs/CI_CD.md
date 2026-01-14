# Azure DevOps CI for FastAPI Docker Image

This repository includes `azure-pipelines.yml` to build and push a Docker image of the FastAPI service to Azure Container Registry (ACR), following industry-standard practices.

## What it does
- Builds the Docker image using the `Dockerfile` at repo root.
- Tags the image with:
  - Short commit SHA (e.g., `abc1234`)
  - Build number (e.g., `20260113.1`)
  - `latest` (only on `main` branch or when building a Git tag)
- Pushes to your ACR registry.

## Prerequisites
1. Azure Container Registry (ACR) created (e.g., `myregistry.azurecr.io`).
2. Azure DevOps Service Connection with access to ACR:
   - Project Settings → Service connections → New service connection → Docker Registry → Azure Container Registry
   - Name it `acr-service-connection` (or update YAML to match your name).
3. Ensure Azure DevOps agents can access your ACR (default for Azure-hosted agents when using the service connection).

## Configure variables
Edit the top of `azure-pipelines.yml` to match your environment:
- `dockerRegistryServiceConnection`: Your ACR service connection name.
- `registryLoginServer`: Your ACR login server (e.g., `myregistry.azurecr.io`).
- `imageRepository`: Repository name for the image (e.g., `fideas-fast-api`).

Optional paths:
- `dockerfilePath`: Defaults to `Dockerfile`.
- `buildContext`: Defaults to `.` (repo root).

## Triggers
- Runs on pushes to `main`.
- Runs for any Git tag (`refs/tags/*`).
- PR validations for PRs into `main`.

## Resulting images
Images will be pushed to ACR under:
- `myregistry.azurecr.io/fideas-fast-api:<short-sha>`
- `myregistry.azurecr.io/fideas-fast-api:<build-number>`
- `myregistry.azurecr.io/fideas-fast-api:latest` (only for `main` branch or tags)

## Local testing (optional)
```bash
# Build locally (from repo root)
docker build -t fideas-fast-api:dev -f Dockerfile .

# Run locally
docker run --rm -p 8000:8000 fideas-fast-api:dev
```

## Common issues
- Service connection errors: verify the service principal has `AcrPush` permission on the ACR.
- Image pull failures for `latest`: ensure a build of `main` or a tag ran successfully first.
- Large build context: `.dockerignore` is provided to speed up builds by excluding unnecessary files.

## Consumption example
```bash
# After pipeline push, pull by SHA or latest
docker pull myregistry.azurecr.io/fideas-fast-api:latest
```
