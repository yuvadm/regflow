import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Config(BaseModel):
    namecheap_api_user: str
    namecheap_api_key: str
    namecheap_username: str
    namecheap_client_ip: str
    cloudflare_api_token: str
    
    @classmethod
    def from_env(cls):
        return cls(
            namecheap_api_user=os.getenv("NAMECHEAP_API_USER", ""),
            namecheap_api_key=os.getenv("NAMECHEAP_API_KEY", ""),
            namecheap_username=os.getenv("NAMECHEAP_USERNAME", ""),
            namecheap_client_ip=os.getenv("NAMECHEAP_CLIENT_IP", ""),
            cloudflare_api_token=os.getenv("CLOUDFLARE_API_TOKEN", "")
        )