import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from ..config import Config


class NamecheapAPI:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://api.namecheap.com/xml.response"

    def _make_request(self, command: str, params: Dict[str, Any]) -> ET.Element:
        """Make a request to Namecheap API"""
        default_params = {
            "ApiUser": self.config.namecheap_api_user,
            "ApiKey": self.config.namecheap_api_key,
            "UserName": self.config.namecheap_username,
            "ClientIp": self.config.namecheap_client_ip,
            "Command": command,
        }

        all_params = {**default_params, **params}

        try:
            response = requests.get(self.base_url, params=all_params, timeout=60)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise Exception(f"API request timed out for command: {command}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed for command {command}: {str(e)}")

        root = ET.fromstring(response.text)

        # Check for API errors
        if root.get("Status") == "ERROR":
            ns = {"ns": "http://api.namecheap.com/xml.response"}
            errors = root.find(".//ns:Errors", ns)
            if errors is not None:
                error_elem = errors.find(".//ns:Error", ns)
                if error_elem is not None:
                    error_msg = error_elem.text
                    raise Exception(f"Namecheap API Error: {error_msg}")
            raise Exception("Namecheap API returned an error")

        return root

    def check_domain_availability(self, domain: str) -> bool:
        """Check if domain is available for registration"""
        params = {"DomainList": domain}

        root = self._make_request("namecheap.domains.check", params)

        # Parse the response
        ns = {"ns": "http://api.namecheap.com/xml.response"}
        domain_check = root.find(".//ns:DomainCheckResult", ns)

        if domain_check is None:
            raise Exception(f"Could not find domain check result for {domain}")

        return domain_check.get("Available") == "true"

    def get_domain_pricing(self, domain: str) -> Dict[str, float]:
        """Get pricing information for a domain"""
        tld = domain.split(".")[-1].upper()

        params = {
            "ProductType": "DOMAIN",
            "ProductCategory": "DOMAINS",
            "ActionName": "REGISTER",
            "ProductName": tld,
        }

        root = self._make_request("namecheap.users.getPricing", params)

        # Find pricing for the TLD
        ns = {"ns": "http://api.namecheap.com/xml.response"}

        # Look for the specific TLD in the response
        for product in root.findall(".//ns:Product", ns):
            product_name = product.get("Name")
            if product_name and product_name.lower() == tld.lower():
                for price in product.findall(".//ns:Price", ns):
                    duration = price.get("Duration")
                    if duration == "1":
                        price_val = float(price.get("Price", 0))

                        # Get renewal price (might be in a separate call or same structure)
                        renew_val = (
                            price_val  # Use same price for renewal if not specified
                        )

                        return {"register": price_val, "renew": renew_val}

        raise Exception(f"No pricing information found for .{tld} domains")

    def get_account_balance(self) -> float:
        """Get current account balance"""
        root = self._make_request("namecheap.users.getBalances", {})

        ns = {"ns": "http://api.namecheap.com/xml.response"}
        balance_result = root.find(".//ns:UserGetBalancesResult", ns)

        if balance_result is not None:
            available_balance = balance_result.get("AvailableBalance")
            if available_balance:
                return float(available_balance)

        raise Exception("Could not retrieve account balance")

    def register_domain(
        self,
        domain: str,
        years: int = 1,
        registrant_info: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Register a domain"""
        if not registrant_info:
            registrant_info = {
                "FirstName": "John",
                "LastName": "Doe",
                "Address1": "123 Main St",
                "City": "Anytown",
                "StateProvince": "NY",
                "PostalCode": "12345",
                "Country": "US",
                "Phone": "+1.5551234567",
                "EmailAddress": "john.doe@example.com",
            }

        params = {
            "DomainName": domain,
            "Years": str(years),
            **{f"Registrant{key}": value for key, value in registrant_info.items()},
            **{f"Tech{key}": value for key, value in registrant_info.items()},
            **{f"Admin{key}": value for key, value in registrant_info.items()},
            **{f"AuxBilling{key}": value for key, value in registrant_info.items()},
        }

        root = self._make_request("namecheap.domains.create", params)

        # Check if registration was successful
        ns = {"ns": "http://api.namecheap.com/xml.response"}
        domain_create = root.find(".//ns:DomainCreateResult", ns)
        if domain_create is None:
            raise Exception(f"Could not find domain creation result for {domain}")

        return domain_create.get("Registered") == "true"

    def set_dns_servers(self, domain: str, nameservers: list) -> bool:
        """Set DNS servers for a domain"""
        sld, tld = domain.split(".", 1)

        params = {"SLD": sld, "TLD": tld, "Nameservers": ",".join(nameservers)}

        root = self._make_request("namecheap.domains.dns.setCustom", params)

        # Check if DNS update was successful
        ns = {"ns": "http://api.namecheap.com/xml.response"}
        dns_result = root.find(".//ns:DomainDNSSetCustomResult", ns)
        if dns_result is None:
            raise Exception(f"Could not find DNS update result for {domain}")

        return dns_result.get("Updated") == "true"

    def is_domain_registered(self, domain: str) -> bool:
        """Check if domain is registered in user's account"""
        try:
            # Get list of all domains in the account
            root = self._make_request("namecheap.domains.getList", {})

            ns = {"ns": "http://api.namecheap.com/xml.response"}

            # Look for the domain in the list
            for domain_elem in root.findall(".//ns:Domain", ns):
                domain_name = domain_elem.get("Name")
                if domain_name and domain_name.lower() == domain.lower():
                    return True

            return False
        except Exception:
            # If API call fails, assume not registered
            return False

    def get_domain_nameservers(self, domain: str) -> list:
        """Get current nameservers for a domain"""
        try:
            params = {"DomainName": domain}

            # Use getInfo to get domain details including nameservers
            root = self._make_request("namecheap.domains.getInfo", params)

            ns = {"ns": "http://api.namecheap.com/xml.response"}
            nameservers = []

            # Look for nameservers in the domain info response
            # The structure might be different, let's check multiple possible locations

            # Try to find nameservers in DnsDetails
            dns_details = root.find(".//ns:DnsDetails", ns)
            if dns_details is not None:
                # Look for nameserver elements
                for ns_elem in dns_details.findall(".//ns:Nameserver", ns):
                    if ns_elem.text:
                        nameservers.append(ns_elem.text)

            # If no nameservers found in DnsDetails, try other locations
            if not nameservers:
                # Try to find in different structure
                for ns_elem in root.findall(".//ns:Nameserver", ns):
                    if ns_elem.text:
                        nameservers.append(ns_elem.text)

            # If still no nameservers, check for attributes in the domain result
            if not nameservers:
                domain_result = root.find(".//ns:DomainGetInfoResult", ns)
                if domain_result is not None:
                    # Check for nameserver attributes (common in Namecheap responses)
                    for i in range(1, 5):  # Check for ns1, ns2, ns3, ns4
                        ns_attr = domain_result.get(f"Nameserver{i}")
                        if ns_attr:
                            nameservers.append(ns_attr)

                    # Also check for DNS details in attributes
                    dns_type = domain_result.get("DnsProviderType")
                    if dns_type == "CUSTOM":
                        # For custom DNS, nameservers should be in the response
                        # Try looking for nameservers in different attribute names
                        for attr_name in domain_result.attrib:
                            if (
                                "nameserver" in attr_name.lower()
                                or "ns" in attr_name.lower()
                            ):
                                ns_value = domain_result.get(attr_name)
                                if ns_value and ns_value not in nameservers:
                                    nameservers.append(ns_value)

            return nameservers
        except Exception:
            # For debugging, you might want to print the exception
            # print(f"Error getting nameservers for {domain}: {e}")
            return []
