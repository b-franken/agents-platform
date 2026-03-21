# Infrastructure

Terraform configuration for the agent platform. Uses [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/) (AVM).

## Resources

| Resource | AVM Module |
|----------|-----------|
| AI Foundry + project + model | `avm-ptn-aiml-ai-foundry` |
| Container Registry | `avm-res-containerregistry-registry` |
| Container App Environment | `avm-res-app-managedenvironment` |
| Container App | `avm-res-app-containerapp` |
| VNet (enterprise) | `avm-res-network-virtualnetwork` |
| Private DNS (enterprise) | `avm-ptn-network-private-link-private-dns-zones` |

## Two environments

| | POC | Enterprise |
|--|-----|-----------|
| Endpoints | Public | Private |
| ACR SKU | Basic | Premium |
| VNet | No | Yes |
| Cost | ~10/mnd | ~92/mnd |

## Usage

```bash
# Prerequisites
az login
terraform init

# POC deployment
terraform plan  -var-file=environments/poc.tfvars
terraform apply -var-file=environments/poc.tfvars

# Enterprise deployment
terraform plan  -var-file=environments/enterprise.tfvars
terraform apply -var-file=environments/enterprise.tfvars

# Get outputs for .env
terraform output project_endpoint
terraform output acr_login_server
```

## After deployment

1. Copy `terraform output project_endpoint` to `.env` as `AZURE_AI_PROJECT_ENDPOINT`
2. Build and push Docker image:
   ```bash
   ACR=$(terraform output -raw acr_login_server)
   az acr login --name $ACR
   docker build -t $ACR/agent-platform:latest ..
   docker push $ACR/agent-platform:latest
   ```
3. The Container App auto-pulls the image
