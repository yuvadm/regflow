#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_namecheap_api import test_namecheap_api
from tests.test_cloudflare_api import test_cloudflare_api

def run_all_tests():
    """Run all integration tests"""
    print("🧪 REGFLOW INTEGRATION TEST SUITE")
    print("="*60)
    print("Testing API integrations with real endpoints")
    print("(Non-mutating operations only)")
    print("="*60)
    
    results = []
    
    # Test Namecheap API
    print("\n" + "="*60)
    namecheap_success = test_namecheap_api()
    results.append(("Namecheap API", namecheap_success))
    
    # Test Cloudflare API
    print("\n" + "="*60)
    cloudflare_success = test_cloudflare_api()
    results.append(("Cloudflare API", cloudflare_success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if not success:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! API integrations are working correctly.")
        print("\nYour API credentials are valid and the system is ready for use.")
        print("\nNext steps:")
        print("  - Use --dry-run for safe testing")
        print("  - Use --setup-only for existing domains")
        print("  - Run without flags for live domain registration")
    else:
        print("❌ SOME TESTS FAILED! Please check your API credentials and network connection.")
        print("\nTroubleshooting:")
        print("  - Verify API tokens are correct and complete")
        print("  - Check that APIs are enabled for your accounts")
        print("  - Ensure network connectivity to API endpoints")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)