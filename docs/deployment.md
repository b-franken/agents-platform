# Deployment

## Local development

```bash
# CLI mode
uv run --package router-agent python -m router.main

# DevUI (browser-based)
uv run devui --port 8080

# Docker Compose (includes observability dashboard)
docker compose up
```

## Azure deployment

### Option 1: Azure Developer CLI (recommended)

```bash
azd up
```

This runs Terraform and deploys the container in one command. See [azure.yaml](../azure.yaml) for configuration.

### Option 2: Terraform + manual deploy

```bash
cd infra

# POC (public endpoints, ~10/month)
terraform apply -var-file=environments/poc.tfvars

# Enterprise (private endpoints, VNet, ~92/month)
terraform apply -var-file=environments/enterprise.tfvars
```

Then build and push the Docker image:

```bash
ACR=$(terraform output -raw acr_login_server)
az acr login --name $ACR
docker build -t $ACR/agent-platform:latest ..
docker push $ACR/agent-platform:latest
```

### Option 3: Azure Functions (serverless)

```bash
cd deployment/azurefunctions
func start  # local testing
func azure functionapp publish <app-name>
```

Provides durable HTTP endpoints:
- `POST /api/workflow/run` — start conversation
- `GET /api/workflow/status/{id}` — check status
- `POST /api/workflow/respond/...` — human-in-the-loop responses

## Infrastructure

See [infra/README.md](../infra/README.md) for Terraform details. Two environment configurations:

| | POC | Enterprise |
|--|-----|-----------|
| Endpoints | Public | Private |
| ACR SKU | Basic | Premium |
| VNet | No | Yes |
| Estimated cost | ~10/month | ~92/month |
