#!/usr/bin/env python3

import sys
from typing import Dict, Any, Optional
from .config import Config
from .providers.namecheap_api import NamecheapAPI
from .providers.cloudflare_api import CloudflareAPI


class DomainManager:
    def __init__(self, config: Config):
        self.config = config
        self.namecheap = NamecheapAPI(config)
        self.cloudflare = CloudflareAPI(config)

    def register_and_setup_domain(
        self,
        domain: str,
        registrant_info: Optional[Dict[str, str]] = None,
        setup_workers: bool = True,
        dry_run: bool = False,
        skip_registration: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete domain registration and setup workflow:
        1. Check domain availability
        2. Verify pricing and account balance
        3. Register domain (with user confirmation)
        4. Add domain to Cloudflare
        5. Update nameservers in Namecheap
        6. Set up basic DNS records
        """
        result = {"domain": domain, "steps_completed": [], "errors": []}

        try:
            if not skip_registration:
                # Step 1: Check domain availability
                print(f"Checking availability for {domain}...")
                if not self.namecheap.check_domain_availability(domain):
                    result["errors"].append(f"Domain {domain} is not available")
                    return result

                result["steps_completed"].append("availability_check")
                print(f"✓ Domain {domain} is available")

                # Step 2: Check pricing and balance
                print("Checking pricing and account balance...")

                try:
                    pricing = self.namecheap.get_domain_pricing(domain)
                except Exception as e:
                    result["errors"].append(f"Failed to get domain pricing: {str(e)}")
                    return result

                try:
                    balance = self.namecheap.get_account_balance()
                except Exception as e:
                    result["errors"].append(f"Failed to get account balance: {str(e)}")
                    return result

                if balance < pricing["register"]:
                    result["errors"].append(
                        f"Insufficient balance. Required: ${pricing['register']:.2f}, "
                        f"Available: ${balance:.2f}"
                    )
                    return result

                result["steps_completed"].append("pricing_check")
                print(f"✓ Pricing: ${pricing['register']:.2f}, Balance: ${balance:.2f}")

                # Step 3: User confirmation with multiple safeguards
                print(f"\n" + "=" * 50)
                print(f"DOMAIN REGISTRATION CONFIRMATION")
                print(f"=" * 50)
                print(f"Domain: {domain}")
                print(f"Registration Price: ${pricing['register']:.2f}")
                print(f"Account Balance: ${balance:.2f}")
                print(f"Remaining Balance: ${balance - pricing['register']:.2f}")
                print(f"=" * 50)

                # Multiple confirmation steps to prevent accidents
                print(
                    f"\nWARNING: This will charge ${pricing['register']:.2f} to your account!"
                )
                first_confirm = input(
                    f"Type 'REGISTER' to proceed with registration of {domain}: "
                ).strip()
                if first_confirm != "REGISTER":
                    result["errors"].append("Registration cancelled by user")
                    return result

                second_confirm = (
                    input(
                        f"Are you absolutely sure you want to register {domain} for ${pricing['register']:.2f}? (yes/no): "
                    )
                    .lower()
                    .strip()
                )
                if second_confirm != "yes":
                    result["errors"].append("Registration cancelled by user")
                    return result

                # Step 4: Register domain
                if dry_run:
                    print(
                        f"DRY RUN: Would register domain {domain} (skipping actual registration)"
                    )
                    result["steps_completed"].append("domain_registration_dry_run")
                else:
                    print(f"Registering domain {domain}...")
                    if not self.namecheap.register_domain(
                        domain, registrant_info=registrant_info
                    ):
                        result["errors"].append(f"Failed to register domain {domain}")
                        return result
                    result["steps_completed"].append("domain_registration")

                print(f"✓ Domain {domain} registered successfully")
            else:
                print(
                    f"✓ Skipping domain registration for {domain} (assuming already registered)"
                )
                result["steps_completed"].append("domain_registration_skipped")

            # Step 5: Add domain to Cloudflare
            print(f"Adding {domain} to Cloudflare...")
            try:
                zone_info = self.cloudflare.add_zone(domain)
                zone_id = zone_info["id"]

                result["steps_completed"].append("cloudflare_zone_creation")
                result["zone_id"] = zone_id
                print(f"✓ Domain added to Cloudflare (Zone ID: {zone_id})")
            except Exception as e:
                result["errors"].append(f"Failed to add domain to Cloudflare: {str(e)}")
                return result

            # Step 6: Get Cloudflare nameservers
            print("Getting Cloudflare nameservers...")
            try:
                nameservers = self.cloudflare.get_zone_nameservers(zone_id)

                result["nameservers"] = nameservers
                print(f"✓ Cloudflare nameservers: {', '.join(nameservers)}")
            except Exception as e:
                result["errors"].append(
                    f"Failed to get Cloudflare nameservers: {str(e)}"
                )
                return result

            # Step 7: Update nameservers in Namecheap
            if not dry_run:
                print(f"Updating nameservers in Namecheap...")
                try:
                    if not self.namecheap.set_dns_servers(domain, nameservers):
                        result["errors"].append(
                            "Failed to update nameservers in Namecheap"
                        )
                        return result

                    result["steps_completed"].append("nameserver_update")
                    print(f"✓ Nameservers updated in Namecheap")
                except Exception as e:
                    result["errors"].append(
                        f"Failed to update nameservers in Namecheap: {str(e)}"
                    )
                    return result
            else:
                print(
                    f"DRY RUN: Would update nameservers in Namecheap to: {', '.join(nameservers)}"
                )
                result["steps_completed"].append("nameserver_update_dry_run")

            # Step 8: Set up basic DNS records (skip for now, empty DNS list)
            print("Setting up basic DNS records...")
            try:
                # For now, just create an empty DNS list as requested
                dns_records = []
                result["dns_records"] = dns_records
                result["steps_completed"].append("basic_dns_setup")
                print(f"✓ Basic DNS records ready (empty list as requested)")
            except Exception as e:
                result["errors"].append(f"Failed to set up DNS records: {str(e)}")
                return result

            # Step 9: Set up worker subdomain if requested
            if setup_workers:
                print("Setting up worker subdomain...")
                try:
                    worker_record = self.cloudflare.create_worker_subdomain(
                        zone_id, f"app.{domain}"
                    )
                    result["worker_record"] = worker_record
                    result["steps_completed"].append("worker_subdomain_setup")
                    print(f"✓ Worker subdomain app.{domain} created")
                except Exception as e:
                    result["errors"].append(
                        f"Failed to set up worker subdomain: {str(e)}"
                    )
                    return result

            result["success"] = True
            print(f"\n🎉 Domain {domain} setup completed successfully!")
            print(f"Zone ID: {zone_id}")
            print(f"Nameservers: {', '.join(nameservers)}")

            return result

        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            return result

    def setup_google_analytics_dns(self, domain: str) -> Dict[str, Any]:
        """Set up DNS records for Google Analytics"""
        try:
            zone_info = self.cloudflare.get_zone_info(domain)
            if not zone_info:
                return {"error": f"Domain {domain} not found in Cloudflare"}

            records = self.cloudflare.setup_google_analytics_dns(
                zone_info["id"], domain
            )
            return {"success": True, "records": records}

        except Exception as e:
            return {"error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python domain_manager.py <domain> [--dry-run] [--setup-only]")
        sys.exit(1)

    domain = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    setup_only = "--setup-only" in sys.argv

    # Load configuration
    config = Config.from_env()

    # Validate required configuration
    if not all(
        [
            config.namecheap_api_key,
            config.namecheap_api_user,
            config.namecheap_username,
            config.namecheap_client_ip,
            config.cloudflare_api_token,
        ]
    ):
        print("Error: Missing required API credentials. Please check your .env file.")
        sys.exit(1)

    # Initialize domain manager
    manager = DomainManager(config)

    # Register and setup domain
    if setup_only:
        print("Running in SETUP-ONLY mode - skipping domain registration")
    if dry_run:
        print("Running in DRY RUN mode - no actual registration will occur")
    result = manager.register_and_setup_domain(
        domain, dry_run=dry_run, skip_registration=setup_only
    )

    if result.get("success"):
        print(f"\nSuccess! Domain {domain} is ready for use.")
    else:
        print(f"\nErrors occurred:")
        for error in result.get("errors", []):
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
