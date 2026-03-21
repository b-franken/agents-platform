output "project_endpoint" {
  description = "AI Foundry project endpoint — use as AZURE_AI_PROJECT_ENDPOINT in .env"
  value       = local.project_endpoint
}

output "openai_endpoint" {
  description = "Azure OpenAI endpoint — alternative value for AZURE_AI_PROJECT_ENDPOINT in .env"
  value       = "https://${local.ai_foundry_name}.openai.azure.com/"
}

output "acr_login_server" {
  description = "Container Registry login server URL"
  value       = module.acr.resource.login_server
}

output "container_app_url" {
  description = "Container App public URL"
  value       = module.container_app.fqdn_url
}

output "container_app_identity" {
  description = "Container App managed identity principal ID — for additional RBAC assignments"
  value       = module.container_app.identity[0].principal_id
}

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.this.name
}
