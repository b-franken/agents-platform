variable "subscription_id" {
  type        = string
  description = "Azure subscription ID."
}

variable "project_name" {
  type        = string
  description = "Project name (3-7 chars, lowercase). Used as base_name for AVM naming."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,5}[a-z0-9]$", var.project_name))
    error_message = "Must be 3-7 lowercase alphanumeric characters, starting and ending with a letter or number."
  }
}

variable "location" {
  type        = string
  default     = "swedencentral"
  description = "Azure region. Must support the Responses API — see https://aka.ms/aoai/responsesapi/availability."
}

variable "model_name" {
  type    = string
  default = "gpt-4.1"
}

variable "model_version" {
  type    = string
  default = "2025-04-14"
}

variable "enable_private_networking" {
  type        = bool
  default     = false
  description = "Enable VNet, private endpoints, and private DNS zones."
}

variable "acr_sku" {
  type        = string
  default     = "Basic"
  description = "ACR SKU. Must be Premium when enable_private_networking is true."

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

variable "model_capacity" {
  type        = number
  default     = 10
  description = "Token-per-minute capacity (in thousands) for model deployments."
}

variable "container_image" {
  type        = string
  default     = "mcr.microsoft.com/k8se/quickstart:latest"
  description = "Container image for the agent platform. Use the default for initial deploy, then set to your ACR image."
}

variable "tags" {
  type    = map(string)
  default = {}
}
