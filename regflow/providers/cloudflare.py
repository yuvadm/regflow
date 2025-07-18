import requests
from typing import Dict, Any, List, Optional
from ..config import Config


class CloudflareAPI:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {config.cloudflare_api_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a request to Cloudflare API"""
        url = f"{self.base_url}{endpoint}"

        response = requests.request(
            method, url, headers=self.headers, json=data, timeout=30
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            # Try to get the error details from the response
            try:
                error_details = response.json()
                errors = error_details.get("errors", [])
                if errors:
                    error_msg = ", ".join(
                        [error.get("message", "Unknown error") for error in errors]
                    )
                    raise Exception(f"Cloudflare API Error: {error_msg}")
                else:
                    raise Exception(
                        f"Cloudflare API Error: {response.status_code} - {response.text}"
                    )
            except ValueError:
                raise Exception(
                    f"Cloudflare API Error: {response.status_code} - {response.text}"
                )

        result = response.json()

        if not result.get("success", False):
            errors = result.get("errors", [])
            if errors:
                error_msg = ", ".join(
                    [error.get("message", "Unknown error") for error in errors]
                )
                raise Exception(f"Cloudflare API Error: {error_msg}")
            else:
                raise Exception(
                    "Cloudflare API Error: Request failed but no error details provided"
                )

        return result

    def add_zone(self, domain: str) -> Dict[str, Any]:
        """Add a new zone (domain) to Cloudflare"""
        data = {"name": domain, "type": "full"}

        result = self._make_request("POST", "/zones", data)
        return result["result"]

    def get_zone_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get zone information for a domain"""
        result = self._make_request("GET", f"/zones?name={domain}")

        zones = result.get("result", [])
        if zones:
            return zones[0]

        return None

    def get_zone_nameservers(self, zone_id: str) -> List[str]:
        """Get nameservers for a zone"""
        result = self._make_request("GET", f"/zones/{zone_id}")

        zone = result.get("result", {})
        return zone.get("name_servers", [])

    def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 300,
        proxied: bool = False,
    ) -> Dict[str, Any]:
        """Create a DNS record"""
        data = {"type": record_type, "name": name, "content": content, "ttl": ttl}

        if record_type in ["A", "AAAA", "CNAME"]:
            data["proxied"] = proxied

        result = self._make_request("POST", f"/zones/{zone_id}/dns_records", data)
        return result["result"]

    def create_worker_subdomain(self, zone_id: str, subdomain: str) -> Dict[str, Any]:
        """Create a worker route for a subdomain"""
        # Create A record pointing to dummy IP (will be overridden by worker)
        return self.create_dns_record(
            zone_id=zone_id,
            record_type="A",
            name=subdomain,
            content="192.0.2.1",  # Dummy IP
            proxied=True,
        )

    def setup_google_analytics_dns(
        self, zone_id: str, domain: str
    ) -> List[Dict[str, Any]]:
        """Set up DNS records for Google Analytics"""
        records = []

        # Google Analytics doesn't typically require specific DNS records
        # But we can add common verification records if needed
        # This is a placeholder for future GA4 requirements

        return records

    def setup_basic_dns_records(
        self, zone_id: str, domain: str
    ) -> List[Dict[str, Any]]:
        """Set up basic DNS records for a domain"""
        records = []

        # Root domain A record (placeholder)
        records.append(
            self.create_dns_record(
                zone_id=zone_id,
                record_type="A",
                name=domain,
                content="192.0.2.1",
                proxied=True,
            )
        )

        # WWW CNAME record
        records.append(
            self.create_dns_record(
                zone_id=zone_id,
                record_type="CNAME",
                name=f"www.{domain}",
                content=domain,
                proxied=True,
            )
        )

        return records

    def list_zones(self) -> List[Dict[str, Any]]:
        """List all zones in the account"""
        result = self._make_request("GET", "/zones")
        return result.get("result", [])

    def get_zone_dns_records(self, zone_id: str) -> List[Dict[str, Any]]:
        """Get all DNS records for a zone"""
        result = self._make_request("GET", f"/zones/{zone_id}/dns_records")
        return result.get("result", [])

    def zone_exists(self, domain: str) -> bool:
        """Check if domain exists as a zone in Cloudflare"""
        zone_info = self.get_zone_info(domain)
        return zone_info is not None
