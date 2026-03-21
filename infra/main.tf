# ─── Naming ──────────────────────────────────────────────────

module "naming" {
  source  = "Azure/naming/azurerm"
  version = "0.4.2"

  suffix = [var.project_name]
}

# ─── Resource Group ──────────────────────────────────────────

resource "azurerm_resource_group" "this" {
  name     = module.naming.resource_group.name_unique
  location = var.location
  tags     = var.tags
}

# ─── Locals ──────────────────────────────────────────────────

locals {
  ai_foundry_name  = module.ai_foundry.ai_foundry_name
  project_name     = "${var.project_name}-project"
  project_endpoint = "https://${local.ai_foundry_name}.services.ai.azure.com/api/projects/${local.project_name}"
  placeholder_image = "mcr.microsoft.com/k8se/quickstart:latest"
}

# ─── AI Foundry + Project + Model ────────────────────────────

module "ai_foundry" {
  source  = "Azure/avm-ptn-aiml-ai-foundry/azurerm"
  version = "0.10.1"

  base_name                  = var.project_name
  location                   = azurerm_resource_group.this.location
  resource_group_resource_id = azurerm_resource_group.this.id

  ai_foundry = {
    create_ai_agent_service = false
    name                    = module.naming.cognitive_account.name_unique
  }

  ai_model_deployments = {
    "gpt-41" = {
      name = var.model_name
      model = {
        format  = "OpenAI"
        name    = var.model_name
        version = var.model_version
      }
      scale = {
        type     = "GlobalStandard"
        capacity = var.model_capacity
      }
    }
    "gpt-41-mini" = {
      name = "gpt-4.1-mini"
      model = {
        format  = "OpenAI"
        name    = "gpt-4.1-mini"
        version = "2025-04-14"
      }
      scale = {
        type     = "GlobalStandard"
        capacity = var.model_capacity
      }
    }
  }

  ai_projects = {
    main = {
      name                       = local.project_name
      description                = "Main AI project"
      display_name               = "${var.project_name} Project"
      create_project_connections = false
    }
  }

  create_byor              = false
  create_private_endpoints = var.enable_private_networking

  private_endpoint_subnet_resource_id = (
    var.enable_private_networking
    ? module.vnet[0].subnets["snet-endpoints"].resource_id
    : null
  )

  tags = var.tags
}

# ─── RBAC ────────────────────────────────────────────────────

data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "deployer_ai_developer" {
  scope                = module.ai_foundry.resource_id
  role_definition_name = "Azure AI Developer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "container_app_openai_user" {
  scope                = module.ai_foundry.resource_id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = module.container_app.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "container_app_acr_pull" {
  scope                = module.acr.resource_id
  role_definition_name = "AcrPull"
  principal_id         = module.container_app.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

# ─── Container Registry ─────────────────────────────────────

module "acr" {
  source  = "Azure/avm-res-containerregistry-registry/azurerm"
  version = "0.5.1"

  name                    = module.naming.container_registry.name_unique
  resource_group_name     = azurerm_resource_group.this.name
  location                = azurerm_resource_group.this.location
  sku                     = var.acr_sku
  zone_redundancy_enabled = var.acr_sku == "Premium"

  private_endpoints = var.enable_private_networking ? {
    pe = {
      subnet_resource_id = module.vnet[0].subnets["snet-endpoints"].resource_id
    }
  } : {}

  tags = var.tags
}

# ─── Log Analytics (required by Container App Environment) ───

module "log_analytics" {
  source  = "Azure/avm-res-operationalinsights-workspace/azurerm"
  version = "0.5.1"

  name                = module.naming.log_analytics_workspace.name_unique
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location

  log_analytics_workspace_retention_in_days = 30
  log_analytics_workspace_sku               = "PerGB2018"

  tags = var.tags
}

# ─── Container App Environment ───────────────────────────────

module "container_env" {
  source = "Azure/avm-res-app-managedenvironment/azurerm"

  name                = module.naming.container_app_environment.name_unique
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location

  log_analytics_workspace = {
    resource_id = module.log_analytics.resource_id
  }

  infrastructure_subnet_id = (
    var.enable_private_networking
    ? module.vnet[0].subnets["snet-agents"].resource_id
    : null
  )

  zone_redundancy_enabled = var.enable_private_networking
}

# ─── Container App ───────────────────────────────────────────

module "container_app" {
  source = "Azure/avm-res-app-containerapp/azurerm"

  name                                  = "agent-platform"
  resource_group_name                   = azurerm_resource_group.this.name
  resource_group_id                     = azurerm_resource_group.this.id
  location                              = azurerm_resource_group.this.location
  container_app_environment_resource_id = module.container_env.resource_id
  revision_mode = "Single"

  managed_identities = {
    system_assigned = true
  }

  template = {
    containers = [
      {
        name   = "agent-platform"
        image  = var.container_image
        cpu    = 0.5
        memory = "1Gi"
        env = [
          {
            name  = "AZURE_AI_PROJECT_ENDPOINT"
            value = local.project_endpoint
          },
          {
            name  = "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"
            value = var.model_name
          },
        ]
      }
    ]
  }

  ingress = {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8080
    traffic_weight = [{
      latest_revision = true
      percentage      = 100
    }]
  }

  registries = var.container_image != local.placeholder_image ? [{
    server   = module.acr.resource.login_server
    identity = "system"
  }] : []

  tags = var.tags
}

# ─── VNet (enterprise only) ─────────────────────────────────

module "vnet" {
  count  = var.enable_private_networking ? 1 : 0
  source = "Azure/avm-res-network-virtualnetwork/azurerm"

  name          = module.naming.virtual_network.name_unique
  parent_id     = azurerm_resource_group.this.id
  location      = azurerm_resource_group.this.location
  address_space = ["10.0.0.0/16"]

  subnets = {
    "snet-agents" = {
      name             = "snet-agents"
      address_prefixes = ["10.0.1.0/24"]
      delegation = [{
        name = "Microsoft.App.environments"
        service_delegation = {
          name = "Microsoft.App/environments"
        }
      }]
    }
    "snet-endpoints" = {
      name             = "snet-endpoints"
      address_prefixes = ["10.0.2.0/24"]
    }
  }

  tags = var.tags
}

# ─── Private DNS Zones (enterprise only) ─────────────────────

module "private_dns" {
  count  = var.enable_private_networking ? 1 : 0
  source = "Azure/avm-ptn-network-private-link-private-dns-zones/azurerm"

  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location

  virtual_network_link_default_virtual_networks = {
    vnet = {
      vnet_resource_id = module.vnet[0].resource_id
    }
  }

  tags = var.tags
}
