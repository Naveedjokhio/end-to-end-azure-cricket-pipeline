terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# ---------------------------------------------------------------------------
# Storage: ADLS Gen2 with raw + silver + gold containers
# ---------------------------------------------------------------------------
resource "azurerm_storage_account" "adls" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # required for ADLS Gen2
}

resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

# ---------------------------------------------------------------------------
# Event Hubs: streaming ingestion (Kafka-compatible, replaces raw Kafka)
# ---------------------------------------------------------------------------
resource "azurerm_eventhub_namespace" "ehns" {
  name                = var.eventhub_namespace_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
  capacity            = 1
}

resource "azurerm_eventhub" "cricket_stream" {
  name                = "cricket-ball-events"
  namespace_name      = azurerm_eventhub_namespace.ehns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 2
  message_retention   = 1
}

resource "azurerm_eventhub_authorization_rule" "send_listen" {
  name                = "send-listen-rule"
  namespace_name      = azurerm_eventhub_namespace.ehns.name
  eventhub_name       = azurerm_eventhub.cricket_stream.name
  resource_group_name = azurerm_resource_group.rg.name
  listen              = true
  send                = true
  manage              = false
}

# ---------------------------------------------------------------------------
# Databricks workspace (Spark, dbt, Cricket_Mart, Dashboard live here)
# ---------------------------------------------------------------------------
resource "azurerm_databricks_workspace" "dbx" {
  name                = var.databricks_workspace_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "premium"
}