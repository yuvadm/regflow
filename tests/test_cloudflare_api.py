#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from cloudflare_api import CloudflareAPI

def test_cloudflare_api():
    """Test Cloudflare API integration with non-mutating calls"""
    print("="*50)
    print("CLOUDFLARE API INTEGRATION TESTS")
    print("="*50)
    
    # Load configuration
    config = Config.from_env()
    
    # Check if API credentials are available
    if not config.cloudflare_api_token or config.cloudflare_api_token == "your_cloudflare_api_token":
        print("❌ Cloudflare API token not found. Please set CLOUDFLARE_API_TOKEN in .env file.")
        return False
    
    print(f"✓ API credentials loaded")
    print(f"  - API Token: {'*' * (len(config.cloudflare_api_token) - 8)}{config.cloudflare_api_token[-8:]}")
    print(f"  - Token length: {len(config.cloudflare_api_token)} chars")
    
    # Initialize API
    api = CloudflareAPI(config)
    
    # Test 1: List existing zones (non-mutating)
    print(f"\n1. Testing zones listing...")
    try:
        zones = api.list_zones()
        print(f"   ✓ Zone listing successful")
        print(f"   - Found {len(zones)} zones in account")
        
        if zones:
            print(f"   - Example zones:")
            for i, zone in enumerate(zones[:3]):  # Show first 3 zones
                print(f"     • {zone.get('name', 'Unknown')} (ID: {zone.get('id', 'Unknown')[:8]}...)")
                if i >= 2:  # Limit to 3 zones
                    break
    except Exception as e:
        print(f"   ❌ Zone listing failed: {e}")
        return False
    
    # Test 2: Get zone info for an existing zone (if any)
    if zones:
        print(f"\n2. Testing zone info retrieval...")
        try:
            first_zone = zones[0]
            zone_name = first_zone.get('name')
            zone_info = api.get_zone_info(zone_name)
            
            if zone_info:
                print(f"   ✓ Zone info retrieved successfully")
                print(f"   - Zone: {zone_info.get('name')}")
                print(f"   - Status: {zone_info.get('status')}")
                print(f"   - ID: {zone_info.get('id')[:8]}...")
                
                # Test 3: Get nameservers for the zone
                print(f"\n3. Testing nameserver retrieval...")
                try:
                    nameservers = api.get_zone_nameservers(zone_info['id'])
                    print(f"   ✓ Nameservers retrieved successfully")
                    print(f"   - Nameservers for {zone_name}:")
                    for ns in nameservers:
                        print(f"     • {ns}")
                except Exception as e:
                    print(f"   ❌ Nameserver retrieval failed: {e}")
                    return False
                
                # Test 4: Get DNS records for the zone (non-mutating)
                print(f"\n4. Testing DNS records retrieval...")
                try:
                    dns_records = api.get_zone_dns_records(zone_info['id'])
                    print(f"   ✓ DNS records retrieved successfully")
                    print(f"   - Found {len(dns_records)} DNS records")
                    
                    if dns_records:
                        print(f"   - Example records:")
                        for i, record in enumerate(dns_records[:3]):  # Show first 3 records
                            print(f"     • {record.get('type', 'Unknown')} {record.get('name', 'Unknown')} -> {record.get('content', 'Unknown')}")
                            if i >= 2:  # Limit to 3 records
                                break
                except Exception as e:
                    print(f"   ❌ DNS records retrieval failed: {e}")
                    return False
            else:
                print(f"   ❌ Zone info retrieval failed: No zone info returned")
                return False
        except Exception as e:
            print(f"   ❌ Zone info retrieval failed: {e}")
            return False
    else:
        print(f"\n2. Skipping zone-specific tests (no zones found)")
        print(f"3. Skipping nameserver tests (no zones found)")
        print(f"4. Skipping DNS records tests (no zones found)")
    
    print(f"\n✅ All Cloudflare API tests passed!")
    return True

if __name__ == "__main__":
    success = test_cloudflare_api()
    sys.exit(0 if success else 1)