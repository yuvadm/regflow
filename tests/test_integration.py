import pytest
import os
from config import Config
from namecheap_api import NamecheapAPI
from cloudflare_api import CloudflareAPI


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


def test_namecheap_credentials_loaded(config):
    """Test that Namecheap credentials are loaded"""
    assert config.namecheap_api_key, "Namecheap API key not found"
    assert config.namecheap_api_user, "Namecheap API user not found"
    assert config.namecheap_username, "Namecheap username not found"
    assert config.namecheap_client_ip, "Namecheap client IP not found"


def test_cloudflare_credentials_loaded(config):
    """Test that Cloudflare credentials are loaded"""
    assert config.cloudflare_api_token, "Cloudflare API token not found"
    assert config.cloudflare_api_token != "your_cloudflare_api_token", "Cloudflare API token is placeholder"
    assert len(config.cloudflare_api_token) == 40, f"Cloudflare API token should be 40 chars, got {len(config.cloudflare_api_token)}"


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