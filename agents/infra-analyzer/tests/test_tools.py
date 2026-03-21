"""Tests for infra-analyzer agent tools."""

from infra_analyzer.tools import apply_fix, check_security_best_practices, scan_terraform


_STORAGE_NO_ENCRYPTION = """
resource "azurerm_storage_account" "example" {
  name                     = "examplestorage"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = "westeurope"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
"""

_STORAGE_PUBLIC_ACCESS = """
resource "azurerm_storage_account" "public" {
  name                          = "publicstorage"
  resource_group_name           = azurerm_resource_group.example.name
  location                      = "westeurope"
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  allow_blob_public_access      = true
  public_network_access_enabled = true

  tags = {
    environment = "dev"
  }
}
"""

_STORAGE_HARDCODED_CREDS = """
resource "azurerm_storage_account" "creds" {
  name                     = "credsstorage"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = "westeurope"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  access_key               = "supersecretaccesskey1234567890"

  tags = {
    environment = "dev"
  }
}
"""

_CLEAN_CONFIG = """
resource "azurerm_storage_account" "secure" {
  name                          = "securestorage"
  resource_group_name           = azurerm_resource_group.example.name
  location                      = "westeurope"
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  enable_https_traffic_only     = true
  min_tls_version               = "TLS1_2"
  allow_blob_public_access      = false
  public_network_access_enabled = false

  logging {
    delete                = true
    read                  = true
    write                 = true
  }

  tags = {
    environment = "production"
    owner       = "platform-team"
  }
}
"""


class TestScanTerraform:
    def test_scan_detects_no_encryption(self):
        result = scan_terraform(_STORAGE_NO_ENCRYPTION)
        assert "NO_ENCRYPTION" in result
        assert "encryption" in result.lower() or "HTTPS" in result

    def test_scan_detects_public_access(self):
        result = scan_terraform(_STORAGE_PUBLIC_ACCESS)
        assert "PUBLIC_ACCESS" in result
        assert "CRITICAL" in result

    def test_scan_detects_no_tags(self):
        result = scan_terraform(_STORAGE_NO_ENCRYPTION)
        assert "NO_TAGS" in result

    def test_scan_detects_hardcoded_credentials(self):
        result = scan_terraform(_STORAGE_HARDCODED_CREDS)
        assert "HARDCODED_CREDENTIALS" in result
        assert "CRITICAL" in result

    def test_scan_clean_config(self):
        result = scan_terraform(_CLEAN_CONFIG)
        assert "NO_ENCRYPTION" not in result
        assert "PUBLIC_ACCESS" not in result
        assert "NO_TAGS" not in result
        assert "HARDCODED_CREDENTIALS" not in result

    def test_scan_returns_score(self):
        result = scan_terraform(_STORAGE_NO_ENCRYPTION)
        assert "Score:" in result
        assert "/100" in result

    def test_scan_returns_summary(self):
        result = scan_terraform(_STORAGE_NO_ENCRYPTION)
        assert "Summary:" in result
        assert "issue" in result.lower()


class TestBestPractices:
    def test_best_practices_storage_account(self):
        result = check_security_best_practices("azurerm_storage_account")
        assert "HTTPS" in result
        assert "TLS" in result
        assert "network" in result.lower()

    def test_best_practices_key_vault(self):
        result = check_security_best_practices("azurerm_key_vault")
        assert "purge protection" in result.lower()
        assert "access policies" in result.lower() or "RBAC" in result

    def test_best_practices_unknown_resource(self):
        result = check_security_best_practices("azurerm_unicorn")
        assert "No best practices found" in result
        assert "azurerm_unicorn" in result


class TestApplyFix:
    def test_apply_fix_returns_confirmation(self):
        result = apply_fix(
            "azurerm_storage_account.example",
            "Enable HTTPS-only traffic",
        )
        assert "Fix applied" in result
        assert "azurerm_storage_account.example" in result
        assert "HTTPS" in result
