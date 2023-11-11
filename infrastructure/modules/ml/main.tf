locals {
  module_name = "ml"
  tags        = {
    "Project" : var.project-name,
    "Location" : data.azurerm_resource_group.rg.location,
    "ResourceGroup" : var.resource-group-name
  }
}

variable "resource-group-name" { type = string }
variable "project-name" { type = string }
variable "api-key" {
  type      = string
  sensitive = true
}
variable "fetched-container-name" { type = string }
variable "cleaned-container-name" { type = string }

data "azurerm_resource_group" "rg" {
  name = var.resource-group-name
}

data "azurerm_client_config" "current" {}

output "ml-workspace-name" {
  value = azurerm_machine_learning_workspace.workspace.name
}

resource "azurerm_application_insights" "app_insights" {
  name                = join("-", [var.project-name, local.module_name])
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  application_type    = "web"
  tags                = local.tags
}

resource "azurerm_key_vault" "key_vault" {
  name                      = join("-", [var.project-name, local.module_name])
  resource_group_name       = data.azurerm_resource_group.rg.name
  location                  = data.azurerm_resource_group.rg.location
  tenant_id                 = data.azurerm_client_config.current.tenant_id
  sku_name                  = "standard"
  enable_rbac_authorization = true
  tags                      = local.tags

}

resource "azurerm_storage_account" "storage" {
  name                     = join("", [var.project-name, local.module_name])
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

resource "azurerm_storage_account" "data-storage" {
  name                     = join("", [var.project-name, local.module_name, "data"])
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  is_hns_enabled           = true
  tags                     = local.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "fetched_container" {
  name               = var.fetched-container-name
  storage_account_id = azurerm_storage_account.data-storage.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "cleaned_container" {
  name               = var.cleaned-container-name
  storage_account_id = azurerm_storage_account.data-storage.id
}

resource "azurerm_user_assigned_identity" "identity" {
  name                = join("-", [var.project-name, local.module_name])
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  tags                = local.tags
}

resource "azurerm_role_assignment" "keyvault_role_administrator_user" {
  principal_id = data.azurerm_client_config.current.object_id
  scope        = azurerm_key_vault.key_vault.id

  role_definition_name = "Key Vault Administrator"
}

resource "azurerm_role_assignment" "keyvault_role_contributor_user" {
  principal_id = data.azurerm_client_config.current.object_id
  scope        = azurerm_key_vault.key_vault.id

  role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_role_assignment" "keyvault_role_contributor" {
  principal_id = azurerm_machine_learning_workspace.workspace.identity[0].principal_id

  scope        = azurerm_key_vault.key_vault.id

  role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_role_assignment" "keyvault_role_contributor_identity" {
  principal_id = azurerm_user_assigned_identity.identity.principal_id

  scope        = azurerm_key_vault.key_vault.id

  role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_role_assignment" "workspace_storage_role" {
  principal_id = azurerm_machine_learning_workspace.workspace.identity[0].principal_id
  scope        = azurerm_storage_account.storage.id

  role_definition_name = "Storage Account Contributor"
}

resource "azurerm_role_assignment" "data_storage_role" {
  principal_id = azurerm_machine_learning_workspace.workspace.identity[0].principal_id
  scope        = azurerm_storage_account.data-storage.id

  role_definition_name = "Storage Blob Data Contributor"
}

resource "azurerm_role_assignment" "data_storage_role_identity" {
  principal_id = azurerm_user_assigned_identity.identity.principal_id
  scope        = azurerm_storage_account.data-storage.id

  role_definition_name = "Storage Blob Data Contributor"
}

resource "azurerm_key_vault_secret" "api-key" {
  key_vault_id = azurerm_key_vault.key_vault.id
  name         = "apikey"
  value        = var.api-key

  depends_on = [azurerm_role_assignment.keyvault_role_contributor, azurerm_role_assignment.keyvault_role_contributor_user]
  tags       = local.tags
}

resource "azurerm_container_registry" "registry" {
  name                = join("", [var.project-name, local.module_name])
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_machine_learning_workspace" "workspace" {
  name                          = join("-", [var.project-name, local.module_name])
  resource_group_name           = data.azurerm_resource_group.rg.name
  location                      = data.azurerm_resource_group.rg.location
  application_insights_id       = azurerm_application_insights.app_insights.id
  key_vault_id                  = azurerm_key_vault.key_vault.id
  storage_account_id            = azurerm_storage_account.storage.id
  public_network_access_enabled = true
  container_registry_id         = azurerm_container_registry.registry.id
  tags                          = local.tags


  identity {
    type         = "SystemAssigned, UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.identity.id]
  }


  depends_on = [azurerm_role_assignment.data_storage_role_identity]
}

data "azurerm_storage_container" "fetched-container" {
  name = var.fetched-container-name
  storage_account_name = azurerm_storage_account.data-storage.name

  depends_on = [azurerm_storage_data_lake_gen2_filesystem.fetched_container]
}

data "azurerm_storage_container" "cleaned-container" {
  name = var.cleaned-container-name
  storage_account_name = azurerm_storage_account.data-storage.name

  depends_on = [azurerm_storage_data_lake_gen2_filesystem.cleaned_container]
}

resource "azurerm_machine_learning_datastore_datalake_gen2" "raw" {
  name                  = "raw"
  workspace_id          = azurerm_machine_learning_workspace.workspace.id
  storage_container_id  = data.azurerm_storage_container.fetched-container.resource_manager_id
  service_data_identity = "WorkspaceSystemAssignedIdentity"
  tags                  = local.tags


}

resource "azurerm_machine_learning_datastore_datalake_gen2" "cleaned" {
  name                  = "cleaned"
  workspace_id          = azurerm_machine_learning_workspace.workspace.id
  storage_container_id  = data.azurerm_storage_container.cleaned-container.resource_manager_id
  service_data_identity = "WorkspaceSystemAssignedIdentity"
  tags                  = local.tags
}

resource "azurerm_role_assignment" "azureml_contributor" {
  principal_id = data.azurerm_client_config.current.object_id
  scope        = azurerm_machine_learning_workspace.workspace.id

  role_definition_name = "Contributor"
}

resource "azurerm_role_assignment" "azureml_system_identity_contributor" {
  principal_id = azurerm_machine_learning_workspace.workspace.identity[0].principal_id
  scope        = azurerm_machine_learning_workspace.workspace.id

  role_definition_name = "Contributor"
}

resource "azurerm_role_assignment" "azureml_user_identity_contributor" {
  principal_id = azurerm_user_assigned_identity.identity.principal_id
  scope        = azurerm_machine_learning_workspace.workspace.id

  role_definition_name = "Contributor"
}