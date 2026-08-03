output "storage_account_name" {
  value = azurerm_storage_account.adls.name
}

output "eventhub_namespace" {
  value = azurerm_eventhub_namespace.ehns.name
}

output "eventhub_connection_string" {
  value     = azurerm_eventhub_authorization_rule.send_listen.primary_connection_string
  sensitive = true
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.dbx.workspace_url
}
