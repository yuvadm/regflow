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

    def get_domain_status(self, domain: str) -> Dict[str, Any]:
        """Get current status of domain across all services"""
        status = {
            "domain": domain,
            "registered": False,
            "cloudflare_zone": None,
            "nameservers": {"namecheap": [], "cloudflare": []},
            "nameservers_match": False,
        }

        # Check if domain is registered
        try:
            status["registered"] = self.namecheap.is_domain_registered(domain)
        except Exception as e:
            status["registration_error"] = str(e)

        # Get Cloudflare zone info
        try:
            zone_info = self.cloudflare.get_zone_info(domain)
            if zone_info:
                status["cloudflare_zone"] = {
                    "id": zone_info["id"],
                    "name": zone_info["name"],
                    "status": zone_info.get("status", "unknown"),
                }

                # Get Cloudflare nameservers
                cf_nameservers = self.cloudflare.get_zone_nameservers(zone_info["id"])
                status["nameservers"]["cloudflare"] = cf_nameservers
        except Exception as e:
            status["cloudflare_error"] = str(e)

        # Get Namecheap nameservers if domain is registered
        if status["registered"]:
            try:
                nc_nameservers = self.namecheap.get_domain_nameservers(domain)
                status["nameservers"]["namecheap"] = nc_nameservers

                # Check if nameservers match
                cf_ns = set(status["nameservers"]["cloudflare"])
                nc_ns = set(nc_nameservers)
                
                # Only consider nameservers matching if we have both sets and they match
                if len(cf_ns) > 0 and len(nc_ns) > 0:
                    status["nameservers_match"] = cf_ns == nc_ns
                else:
                    # If we can't retrieve nameservers from either side, assume they don't match
                    status["nameservers_match"] = False
            except Exception as e:
                status["namecheap_ns_error"] = str(e)

        return status

    def print_domain_status(self, domain: str):
        """Print formatted status of domain"""
        status = self.get_domain_status(domain)

        print(f"\n=== Domain Status: {domain} ===")

        # Registration status
        if status["registered"]:
            print("✓ Domain is registered in Namecheap")
        else:
            print("✗ Domain is NOT registered in Namecheap")
            if "registration_error" in status:
                print(f"  Error: {status['registration_error']}")

        # Cloudflare zone status
        if status["cloudflare_zone"]:
            zone = status["cloudflare_zone"]
            print(
                f"✓ Cloudflare zone exists (ID: {zone['id']}, Status: {zone['status']})"
            )
        else:
            print("✗ No Cloudflare zone found")
            if "cloudflare_error" in status:
                print(f"  Error: {status['cloudflare_error']}")

        # Nameserver status
        nc_ns = status["nameservers"]["namecheap"]
        cf_ns = status["nameservers"]["cloudflare"]

        if nc_ns:
            print(f"Namecheap nameservers: {', '.join(nc_ns)}")
        else:
            print("Namecheap nameservers: None")

        if cf_ns:
            print(f"Cloudflare nameservers: {', '.join(cf_ns)}")
        else:
            print("Cloudflare nameservers: None")

        if len(nc_ns) == 0 and len(cf_ns) == 0:
            print("⚠ Cannot retrieve nameservers from either service")
        elif len(nc_ns) == 0:
            print("⚠ Cannot retrieve Namecheap nameservers - unable to verify configuration")
        elif len(cf_ns) == 0:
            print("⚠ Cannot retrieve Cloudflare nameservers - unable to verify configuration")
        elif status["nameservers_match"]:
            print("✓ Nameservers are properly configured")
        else:
            print("✗ Nameservers do NOT match")

        print("=" * 50)

    def setup_domain(
        self,
        domain: str,
        registrant_info: Optional[Dict[str, str]] = None,
        setup_workers: bool = True,
        dry_run: bool = False,
        force_registration: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete domain setup workflow (idempotent):
        1. Check domain registration status
        2. Register domain if needed (with user confirmation)
        3. Create Cloudflare zone if needed
        4. Update nameservers in Namecheap if needed
        5. Set up basic DNS records
        """
        result = {"domain": domain, "steps_completed": [], "errors": []}

        try:
            # Get current status
            status = self.get_domain_status(domain)

            # Step 1: Handle domain registration
            if not status["registered"]:
                if not force_registration:
                    print(
                        f"Domain {domain} is not registered. Use --force-registration to register it."
                    )
                    result["errors"].append(
                        "Domain not registered and force_registration not enabled"
                    )
                    return result

                # Check availability
                print(f"Checking availability for {domain}...")
                if not self.namecheap.check_domain_availability(domain):
                    result["errors"].append(
                        f"Domain {domain} is not available for registration"
                    )
                    return result

                # Get pricing and balance
                try:
                    pricing = self.namecheap.get_domain_pricing(domain)
                    balance = self.namecheap.get_account_balance()
                except Exception as e:
                    result["errors"].append(f"Failed to get pricing/balance: {str(e)}")
                    return result

                if balance < pricing["register"]:
                    result["errors"].append(
                        f"Insufficient balance. Required: ${pricing['register']:.2f}, "
                        f"Available: ${balance:.2f}"
                    )
                    return result

                # User confirmation
                print("\n" + "=" * 50)
                print("DOMAIN REGISTRATION CONFIRMATION")
                print("=" * 50)
                print(f"Domain: {domain}")
                print(f"Registration Price: ${pricing['register']:.2f}")
                print(f"Account Balance: ${balance:.2f}")
                print(f"Remaining Balance: ${balance - pricing['register']:.2f}")
                print("=" * 50)

                print(
                    f"\nWARNING: This will charge ${pricing['register']:.2f} to your account!"
                )

                if not dry_run:
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

                    # Register domain
                    print(f"Registering domain {domain}...")
                    if not self.namecheap.register_domain(
                        domain, registrant_info=registrant_info
                    ):
                        result["errors"].append(f"Failed to register domain {domain}")
                        return result

                    result["steps_completed"].append("domain_registration")
                    print(f"✓ Domain {domain} registered successfully")
                else:
                    print(f"DRY RUN: Would register domain {domain}")
                    result["steps_completed"].append("domain_registration_dry_run")
            else:
                print(f"✓ Domain {domain} is already registered")
                result["steps_completed"].append("domain_already_registered")

            # Step 2: Handle Cloudflare zone creation
            if not status["cloudflare_zone"]:
                print(f"Creating Cloudflare zone for {domain}...")
                try:
                    if not dry_run:
                        zone_info = self.cloudflare.add_zone(domain)
                        zone_id = zone_info["id"]
                        result["steps_completed"].append("cloudflare_zone_creation")
                        result["zone_id"] = zone_id
                        print(f"✓ Cloudflare zone created (ID: {zone_id})")
                    else:
                        print(f"DRY RUN: Would create Cloudflare zone for {domain}")
                        result["steps_completed"].append(
                            "cloudflare_zone_creation_dry_run"
                        )
                        # For dry run, we can't continue with nameserver setup
                        return result
                except Exception as e:
                    result["errors"].append(
                        f"Failed to create Cloudflare zone: {str(e)}"
                    )
                    return result
            else:
                zone_id = status["cloudflare_zone"]["id"]
                result["zone_id"] = zone_id
                print(f"✓ Cloudflare zone already exists (ID: {zone_id})")
                result["steps_completed"].append("cloudflare_zone_already_exists")

            # Step 3: Get Cloudflare nameservers
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

            # Step 4: Update nameservers in Namecheap if needed
            current_nc_nameservers = set(status["nameservers"]["namecheap"])
            cloudflare_nameservers = set(nameservers)

            if current_nc_nameservers != cloudflare_nameservers:
                if not dry_run:
                    print("Updating nameservers in Namecheap...")
                    try:
                        if not self.namecheap.set_dns_servers(domain, nameservers):
                            result["errors"].append(
                                "Failed to update nameservers in Namecheap"
                            )
                            return result

                        result["steps_completed"].append("nameserver_update")
                        print("✓ Nameservers updated in Namecheap")
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
            else:
                print("✓ Nameservers already configured correctly")
                result["steps_completed"].append("nameservers_already_configured")

            # Step 5: Set up basic DNS records (placeholder for now)
            print("Setting up basic DNS records...")
            try:
                dns_records = []
                result["dns_records"] = dns_records
                result["steps_completed"].append("basic_dns_setup")
                print("✓ Basic DNS records ready (empty list as requested)")
            except Exception as e:
                result["errors"].append(f"Failed to set up DNS records: {str(e)}")
                return result

            # Step 6: Set up worker subdomain if requested
            if setup_workers:
                print("Setting up worker subdomain...")
                try:
                    if not dry_run:
                        worker_record = self.cloudflare.create_worker_subdomain(
                            zone_id, f"app.{domain}"
                        )
                        result["worker_record"] = worker_record
                        result["steps_completed"].append("worker_subdomain_setup")
                        print(f"✓ Worker subdomain app.{domain} created")
                    else:
                        print(f"DRY RUN: Would create worker subdomain app.{domain}")
                        result["steps_completed"].append(
                            "worker_subdomain_setup_dry_run"
                        )
                except Exception as e:
                    result["errors"].append(
                        f"Failed to set up worker subdomain: {str(e)}"
                    )
                    return result

            result["success"] = True
            print(f"\n🎉 Domain {domain} setup completed successfully!")
            if "zone_id" in result:
                print(f"Zone ID: {result['zone_id']}")
            if "nameservers" in result:
                print(f"Nameservers: {', '.join(result['nameservers'])}")

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
        print("Usage: regflow <domain> [options]")
        print("")
        print("Options:")
        print("  --status                 Show current status of domain")
        print("  --setup                  Set up domain (idempotent)")
        print(
            "  --dry-run               Show what would be done without making changes"
        )
        print("  --force-registration    Allow domain registration (costs money!)")
        print("  --no-workers            Skip worker subdomain setup")
        print("")
        print("Examples:")
        print("  regflow example.com --status")
        print("  regflow example.com --setup --dry-run")
        print("  regflow example.com --setup --force-registration")
        sys.exit(1)

    domain = sys.argv[1]

    # Parse command line arguments
    show_status = "--status" in sys.argv
    setup_domain = "--setup" in sys.argv
    dry_run = "--dry-run" in sys.argv
    force_registration = "--force-registration" in sys.argv
    setup_workers = "--no-workers" not in sys.argv

    # Default to setup if no action specified
    if not show_status and not setup_domain:
        setup_domain = True

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

    # Handle status command
    if show_status:
        manager.print_domain_status(domain)
        return

    # Handle setup command
    if setup_domain:
        if dry_run:
            print("Running in DRY RUN mode - no actual changes will be made")
        if force_registration:
            print("FORCE REGISTRATION enabled - will register domain if needed")

        result = manager.setup_domain(
            domain,
            dry_run=dry_run,
            force_registration=force_registration,
            setup_workers=setup_workers,
        )

        if result.get("success"):
            print(f"\nSuccess! Domain {domain} is ready for use.")
        else:
            print("\nErrors occurred:")
            for error in result.get("errors", []):
                print(f"  - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
