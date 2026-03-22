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

output "deployment_mode" {
  description = "Active deployment mode"
  value       = var.deployment_mode
}

output "container_app_url" {
  description = "Container App public URL (only when deployment_mode = container_apps)"
  value       = var.deployment_mode == "container_apps" ? module.container_app[0].fqdn_url : null
}

output "container_app_identity" {
  description = "Container App managed identity principal ID (only when deployment_mode = container_apps)"
  value       = var.deployment_mode == "container_apps" ? module.container_app[0].identity[0].principal_id : null
}

output "agent_service_enabled" {
  description = "Whether Foundry Agent Service is enabled"
  value       = var.enable_agent_service
}

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.this.name
}
