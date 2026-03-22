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

### Option 1: Foundry hosted (recommended)

Deploy to [Azure AI Foundry Agent Service](https://learn.microsoft.com/en-us/azure/foundry/agents/overview) — GA since March 2026. Foundry manages the agent runtime (scaling, observability, security). You only pay for model tokens.

```bash
azd up
```

This provisions AI Foundry with Agent Service enabled (Cosmos DB for thread storage, AI Search for vector store, Storage Account for files) and deploys the agent container.

**What Foundry hosted gives you:**
- Automatic scaling — no Container Apps to manage
- Built-in observability (tracing, evaluations)
- Enterprise security (VNet, Entra ID, RBAC)
- 1400+ Logic Apps tool integrations
- MCP authentication
- Private networking (zero public egress)

### Option 2: Container Apps (self-hosted)

If you prefer to manage the runtime yourself:

```bash
# Via azd
azd up -- -var="deployment_mode=container_apps"

# Via Terraform directly
cd infra
terraform apply -var="deployment_mode=container_apps"
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

See [infra/README.md](../infra/README.md) for Terraform details.

| | Foundry hosted (default) | Container Apps |
|--|--------------------------|----------------|
| Runtime | Managed by Foundry | Self-managed |
| Scaling | Automatic | Manual / KEDA |
| Cost | Token-only | ~$10-92/month + tokens |
| Agent Service | Yes (Cosmos DB, AI Search) | Optional |
| VNet | Built-in (Standard setup) | Via `enable_private_networking` |
