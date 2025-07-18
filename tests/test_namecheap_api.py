#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from namecheap_api import NamecheapAPI

def test_namecheap_api():
    """Test Namecheap API integration with non-mutating calls"""
    print("="*50)
    print("NAMECHEAP API INTEGRATION TESTS")
    print("="*50)
    
    # Load configuration
    config = Config.from_env()
    
    # Check if API credentials are available
    if not all([
        config.namecheap_api_key,
        config.namecheap_api_user,
        config.namecheap_username,
        config.namecheap_client_ip
    ]):
        print("❌ Namecheap API credentials not found. Please set them in .env file.")
        return False
    
    print(f"✓ API credentials loaded")
    print(f"  - API User: {config.namecheap_api_user}")
    print(f"  - Username: {config.namecheap_username}")
    print(f"  - Client IP: {config.namecheap_client_ip}")
    print(f"  - API Key: {'*' * len(config.namecheap_api_key)}")
    
    # Initialize API
    api = NamecheapAPI(config)
    
    # Test 1: Check domain availability (non-mutating)
    print(f"\n1. Testing domain availability check...")
    try:
        test_domain = "test-domain-12345.com"
        is_available = api.check_domain_availability(test_domain)
        print(f"   ✓ Domain availability check successful")
        print(f"   - {test_domain} is {'available' if is_available else 'not available'}")
    except Exception as e:
        print(f"   ❌ Domain availability check failed: {e}")
        return False
    
    # Test 2: Get account balance (non-mutating)
    print(f"\n2. Testing account balance retrieval...")
    try:
        balance = api.get_account_balance()
        print(f"   ✓ Account balance retrieved successfully")
        print(f"   - Current balance: ${balance:.2f}")
    except Exception as e:
        print(f"   ❌ Account balance retrieval failed: {e}")
        return False
    
    # Test 3: Get domain pricing (non-mutating)
    print(f"\n3. Testing domain pricing retrieval...")
    try:
        test_domain = "example.com"
        pricing = api.get_domain_pricing(test_domain)
        print(f"   ✓ Domain pricing retrieved successfully")
        print(f"   - .com registration: ${pricing['register']:.2f}")
        print(f"   - .com renewal: ${pricing['renew']:.2f}")
    except Exception as e:
        print(f"   ❌ Domain pricing retrieval failed: {e}")
        return False
    
    # Test 4: Test with different TLD
    print(f"\n4. Testing pricing for different TLD...")
    try:
        test_domain = "example.xyz"
        pricing = api.get_domain_pricing(test_domain)
        print(f"   ✓ .xyz domain pricing retrieved successfully")
        print(f"   - .xyz registration: ${pricing['register']:.2f}")
        print(f"   - .xyz renewal: ${pricing['renew']:.2f}")
    except Exception as e:
        print(f"   ❌ .xyz domain pricing retrieval failed: {e}")
        return False
    
    print(f"\n✅ All Namecheap API tests passed!")
    return True

if __name__ == "__main__":
    success = test_namecheap_api()
    sys.exit(0 if success else 1)