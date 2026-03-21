# Uncomment to use Azure Storage as remote state backend.
# Create the storage account first:
#   az storage account create -n <name> -g <rg> --sku Standard_LRS
#   az storage container create -n tfstate --account-name <name>
#
# terraform {
#   backend "azurerm" {
#     resource_group_name  = "rg-terraform-state"
#     storage_account_name = "stterraformstate"
#     container_name       = "tfstate"
#     key                  = "agents-platform.tfstate"
#   }
# }
