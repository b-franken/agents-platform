subscription_id           = "00000000-0000-0000-0000-000000000000"
project_name              = "agents"
location                  = "swedencentral"
model_name                = "gpt-4.1"
model_version             = "2025-04-14"
enable_private_networking = false
acr_sku                   = "Basic"

tags = {
  environment = "poc"
  managed_by  = "terraform"
}
