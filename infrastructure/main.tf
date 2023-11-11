terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.62.1"
    }
  }
  backend "azurerm" {
    key              = "terraform.tfstate"
    use_azuread_auth = true
  }

  required_version = ">= 1.1.0"
}

provider "azurerm" {
  features {}
  storage_use_azuread = true
}

module "ml" {
  source = "./modules/ml"

  api-key                = var.api-key
  cleaned-container-name = var.cleaned-container-name
  fetched-container-name = var.fetched-container-name
  project-name           = var.project-name
  resource-group-name    = var.resource-group-name
}

output "workspace-name" {
  value = module.ml.ml-workspace-name
}