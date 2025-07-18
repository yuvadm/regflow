import pytest
from ..config import Config
from ..providers.namecheap import NamecheapAPI
from ..providers.cloudflare import CloudflareAPI
from ..domains import DomainManager


@pytest.fixture
def config():
    """Load configuration for tests"""
    return Config.from_env()


@pytest.fixture
def namecheap_api(config):
    """Create Namecheap API instance"""
    return NamecheapAPI(config)


@pytest.fixture
def cloudflare_api(config):
    """Create Cloudflare API instance"""
    return CloudflareAPI(config)


@pytest.fixture
def domain_manager(config):
    """Create DomainManager instance"""
    return DomainManager(config)


def test_namecheap_credentials_loaded(config):
    """Test that Namecheap credentials are loaded"""
    assert config.namecheap_api_key, "Namecheap API key not found"
    assert config.namecheap_api_user, "Namecheap API user not found"
    assert config.namecheap_username, "Namecheap username not found"
    assert config.namecheap_client_ip, "Namecheap client IP not found"


def test_cloudflare_credentials_loaded(config):
    """Test that Cloudflare credentials are loaded"""
    assert config.cloudflare_api_token, "Cloudflare API token not found"
    assert config.cloudflare_api_token != "your_cloudflare_api_token", (
        "Cloudflare API token is placeholder"
    )
    assert len(config.cloudflare_api_token) == 40, (
        f"Cloudflare API token should be 40 chars, got {len(config.cloudflare_api_token)}"
    )


def test_namecheap_domain_availability(namecheap_api):
    """Test domain availability check"""
    test_domain = "test-domain-12345.com"
    is_available = namecheap_api.check_domain_availability(test_domain)
    assert isinstance(is_available, bool), "Domain availability should return boolean"


def test_namecheap_account_balance(namecheap_api):
    """Test account balance retrieval"""
    balance = namecheap_api.get_account_balance()
    assert isinstance(balance, (int, float)), "Balance should be numeric"
    assert balance >= 0, "Balance should be non-negative"


def test_namecheap_domain_pricing(namecheap_api):
    """Test domain pricing retrieval"""
    pricing = namecheap_api.get_domain_pricing("example.com")
    assert isinstance(pricing, dict), "Pricing should be a dictionary"
    assert "register" in pricing, "Pricing should contain 'register' key"
    assert "renew" in pricing, "Pricing should contain 'renew' key"
    assert pricing["register"] > 0, "Registration price should be positive"
    assert pricing["renew"] > 0, "Renewal price should be positive"


def test_namecheap_different_tld_pricing(namecheap_api):
    """Test pricing for different TLD"""
    pricing = namecheap_api.get_domain_pricing("example.xyz")
    assert isinstance(pricing, dict), "Pricing should be a dictionary"
    assert pricing["register"] > 0, ".xyz registration price should be positive"


def test_cloudflare_list_zones(cloudflare_api):
    """Test listing Cloudflare zones"""
    zones = cloudflare_api.list_zones()
    assert isinstance(zones, list), "Zones should be a list"

    if zones:
        zone = zones[0]
        assert "id" in zone, "Zone should have 'id' field"
        assert "name" in zone, "Zone should have 'name' field"


def test_cloudflare_zone_info(cloudflare_api):
    """Test getting zone information"""
    zones = cloudflare_api.list_zones()

    if zones:
        zone_name = zones[0]["name"]
        zone_info = cloudflare_api.get_zone_info(zone_name)

        assert zone_info is not None, "Zone info should not be None"
        assert zone_info["name"] == zone_name, "Zone name should match"
        assert "id" in zone_info, "Zone info should have 'id' field"


def test_cloudflare_nameservers(cloudflare_api):
    """Test getting zone nameservers"""
    zones = cloudflare_api.list_zones()

    if zones:
        zone_id = zones[0]["id"]
        nameservers = cloudflare_api.get_zone_nameservers(zone_id)

        assert isinstance(nameservers, list), "Nameservers should be a list"
        assert len(nameservers) > 0, "Should have at least one nameserver"

        for ns in nameservers:
            assert isinstance(ns, str), "Nameserver should be a string"
            assert "cloudflare.com" in ns, "Nameserver should be from Cloudflare"


def test_cloudflare_dns_records(cloudflare_api):
    """Test getting DNS records"""
    zones = cloudflare_api.list_zones()

    if zones:
        zone_id = zones[0]["id"]
        records = cloudflare_api.get_zone_dns_records(zone_id)

        assert isinstance(records, list), "DNS records should be a list"

        if records:
            record = records[0]
            assert "type" in record, "Record should have 'type' field"
            assert "name" in record, "Record should have 'name' field"
            assert "content" in record, "Record should have 'content' field"


# New tests for domain registration and nameserver functionality


def test_namecheap_domain_registration_check_existing(namecheap_api):
    """Test domain registration check for existing domain"""
    # Test with stackvital.com which we know exists
    is_registered = namecheap_api.is_domain_registered("stackvital.com")
    assert is_registered, "stackvital.com should be registered"


def test_namecheap_domain_registration_check_nonexistent(namecheap_api):
    """Test domain registration check for non-existent domain"""
    # Test with a domain that definitely doesn't exist in the account
    is_registered = namecheap_api.is_domain_registered("nonexistent-domain-12345.com")
    assert not is_registered, "Non-existent domain should not be registered"


def test_namecheap_get_nameservers_existing_domain(namecheap_api):
    """Test nameserver retrieval for existing domain"""
    nameservers = namecheap_api.get_domain_nameservers("stackvital.com")

    assert isinstance(nameservers, list), "Nameservers should be a list"
    assert len(nameservers) > 0, "Should have at least one nameserver"

    # Check that all nameservers are strings
    for ns in nameservers:
        assert isinstance(ns, str), "Each nameserver should be a string"
        assert "." in ns, "Nameserver should be a valid domain name"


def test_namecheap_get_nameservers_nonexistent_domain(namecheap_api):
    """Test nameserver retrieval for non-existent domain"""
    nameservers = namecheap_api.get_domain_nameservers("nonexistent-domain-12345.com")

    # Should return empty list for non-existent domain
    assert isinstance(nameservers, list), (
        "Should return a list even for non-existent domain"
    )
    assert len(nameservers) == 0, "Should return empty list for non-existent domain"


def test_cloudflare_zone_exists_check(cloudflare_api):
    """Test Cloudflare zone existence check"""
    # Test with stackvital.com which should exist in Cloudflare
    zone_exists = cloudflare_api.zone_exists("stackvital.com")
    assert zone_exists, "stackvital.com should exist in Cloudflare"

    # Test with a domain that doesn't exist
    zone_exists = cloudflare_api.zone_exists("nonexistent-domain-12345.com")
    assert not zone_exists, "Non-existent domain should not exist in Cloudflare"


def test_domain_manager_get_status_existing_domain(domain_manager):
    """Test domain status retrieval for existing domain"""
    status = domain_manager.get_domain_status("stackvital.com")

    # Verify status structure
    assert "domain" in status, "Status should contain domain field"
    assert "registered" in status, "Status should contain registered field"
    assert "cloudflare_zone" in status, "Status should contain cloudflare_zone field"
    assert "nameservers" in status, "Status should contain nameservers field"
    assert "nameservers_match" in status, (
        "Status should contain nameservers_match field"
    )

    # Verify domain name
    assert status["domain"] == "stackvital.com", "Domain name should match"

    # Verify registration status
    assert status["registered"], "stackvital.com should be registered"

    # Verify Cloudflare zone exists
    assert status["cloudflare_zone"] is not None, "Cloudflare zone should exist"
    assert "id" in status["cloudflare_zone"], "Zone should have ID"
    assert "name" in status["cloudflare_zone"], "Zone should have name"
    assert "status" in status["cloudflare_zone"], "Zone should have status"

    # Verify nameservers structure
    assert "namecheap" in status["nameservers"], "Should have namecheap nameservers"
    assert "cloudflare" in status["nameservers"], "Should have cloudflare nameservers"
    assert isinstance(status["nameservers"]["namecheap"], list), (
        "Namecheap nameservers should be a list"
    )
    assert isinstance(status["nameservers"]["cloudflare"], list), (
        "Cloudflare nameservers should be a list"
    )

    # Verify nameservers are populated
    assert len(status["nameservers"]["namecheap"]) > 0, (
        "Should have Namecheap nameservers"
    )
    assert len(status["nameservers"]["cloudflare"]) > 0, (
        "Should have Cloudflare nameservers"
    )


def test_domain_manager_get_status_nonexistent_domain(domain_manager):
    """Test domain status retrieval for non-existent domain"""
    status = domain_manager.get_domain_status("nonexistent-domain-12345.com")

    # Verify status structure
    assert "domain" in status, "Status should contain domain field"
    assert "registered" in status, "Status should contain registered field"
    assert "cloudflare_zone" in status, "Status should contain cloudflare_zone field"
    assert "nameservers" in status, "Status should contain nameservers field"
    assert "nameservers_match" in status, (
        "Status should contain nameservers_match field"
    )

    # Verify domain name
    assert status["domain"] == "nonexistent-domain-12345.com", (
        "Domain name should match"
    )

    # Verify registration status
    assert not status["registered"], "Non-existent domain should not be registered"

    # Verify Cloudflare zone doesn't exist
    assert status["cloudflare_zone"] is None, "Cloudflare zone should not exist"

    # Verify nameservers are empty
    assert len(status["nameservers"]["namecheap"]) == 0, (
        "Should have no Namecheap nameservers"
    )
    assert len(status["nameservers"]["cloudflare"]) == 0, (
        "Should have no Cloudflare nameservers"
    )

    # Verify nameservers don't match
    assert not status["nameservers_match"], (
        "Nameservers should not match for non-existent domain"
    )


def test_nameserver_matching_logic(domain_manager):
    """Test nameserver matching logic with stackvital.com"""
    status = domain_manager.get_domain_status("stackvital.com")

    # Get the nameservers
    nc_nameservers = status["nameservers"]["namecheap"]
    cf_nameservers = status["nameservers"]["cloudflare"]

    # Both should have nameservers
    assert len(nc_nameservers) > 0, "Should have Namecheap nameservers"
    assert len(cf_nameservers) > 0, "Should have Cloudflare nameservers"

    # Check if they match (they should for stackvital.com)
    nc_set = set(nc_nameservers)
    cf_set = set(cf_nameservers)

    # The nameservers should match
    assert nc_set == cf_set, "Nameservers should match for properly configured domain"
    assert status["nameservers_match"], "Status should indicate nameservers match"


def test_domain_manager_print_status_no_errors(domain_manager, capsys):
    """Test that print_domain_status runs without errors"""
    # This should not raise any exceptions
    domain_manager.print_domain_status("stackvital.com")

    # Verify some output was produced
    captured = capsys.readouterr()
    assert "Domain Status: stackvital.com" in captured.out, (
        "Should print domain status header"
    )
    assert "registered" in captured.out.lower(), "Should mention registration status"
    assert "nameservers" in captured.out.lower(), "Should mention nameservers"


def test_setup_domain_dry_run_existing_domain(domain_manager):
    """Test setup_domain with dry run for existing domain"""
    result = domain_manager.setup_domain(
        "stackvital.com", dry_run=True, force_registration=False
    )

    # Should succeed since domain is already registered
    assert "success" in result, "Result should contain success field"
    assert result.get("success"), "Should succeed for existing domain"
    assert "errors" in result, "Result should contain errors field"
    assert len(result["errors"]) == 0, "Should have no errors"
    assert "steps_completed" in result, "Result should contain steps_completed field"
    assert len(result["steps_completed"]) > 0, "Should have completed some steps"
