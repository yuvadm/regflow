#!/usr/bin/env python3

import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def test_api_connectivity():
    """Test basic API connectivity"""
    print("="*50)
    print("API CONNECTIVITY TEST")
    print("="*50)
    
    config = Config.from_env()
    
    # Test Namecheap API connectivity
    print("\n1. Testing Namecheap API connectivity...")
    try:
        response = requests.get("https://api.namecheap.com/xml.response", 
                               params={"Command": "namecheap.domains.check", "DomainList": "test.com"}, 
                               timeout=10)
        print(f"   ✓ Namecheap API reachable (Status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Namecheap API unreachable: {e}")
    
    # Test Cloudflare API connectivity
    print("\n2. Testing Cloudflare API connectivity...")
    try:
        headers = {"Authorization": f"Bearer {config.cloudflare_api_token}"}
        response = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", 
                               headers=headers, timeout=10)
        print(f"   ✓ Cloudflare API reachable (Status: {response.status_code})")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✓ Cloudflare API token is valid")
            else:
                print(f"   ❌ Cloudflare API token is invalid: {result.get('errors', [])}")
        else:
            print(f"   ❌ Cloudflare API token verification failed")
    except Exception as e:
        print(f"   ❌ Cloudflare API unreachable: {e}")
    
    print("\n3. API Token Information:")
    print(f"   - Namecheap API Key: {len(config.namecheap_api_key)} chars")
    print(f"   - Cloudflare API Token: {len(config.cloudflare_api_token)} chars")
    print(f"   - Expected Cloudflare token length: 40 chars")
    
    if len(config.cloudflare_api_token) < 40:
        print(f"   ⚠ Cloudflare token appears to be truncated")
        print(f"   - Current token: {config.cloudflare_api_token}")
        print(f"   - Please check if the token is complete in .env file")

if __name__ == "__main__":
    test_api_connectivity()