variable "resource_group_name" {
  default = "rg-e2e-cricket-project"
}

variable "location" {
  default = "eastus"
}

variable "storage_account_name" {
  # must be globally unique, lowercase, no dashes, 3-24 chars
  default = "najcricket2026adls"
}

variable "eventhub_namespace_name" {
  # must be globally unique
  default = "naj-cricket-ehns-2026"
}

variable "databricks_workspace_name" {
  default = "databricks-e2e-cricket"
}