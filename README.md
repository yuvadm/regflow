# RegFlow

A domain registration and DNS management automation tool that integrates with Namecheap and Cloudflare APIs.

## Features

- **Idempotent domain setup** - Safe to run multiple times
- **Domain registration** with Namecheap (with strict confirmation)
- **Cloudflare zone management** - Automatic zone creation
- **Nameserver synchronization** - Keeps Namecheap and Cloudflare in sync
- **Status checking** - View current domain configuration
- **Dry-run mode** - Preview changes without making them
- **Comprehensive logging** - Track all operations

## Installation

### Prerequisites

- Python 3.8.1 or higher
- Namecheap API access (API key, username, client IP)
- Cloudflare API access (API token)

### Install from source

```bash
git clone <repository-url>
cd regflow
pip install -e .
```

## Configuration

Create a `.env` file in your project directory:

```bash
# Namecheap API Configuration
NAMECHEAP_API_KEY=your_namecheap_api_key
NAMECHEAP_API_USER=your_namecheap_api_user
NAMECHEAP_USERNAME=your_namecheap_username
NAMECHEAP_CLIENT_IP=your_public_ip_address

# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
```

### Getting API Credentials

#### Namecheap
1. Log in to your Namecheap account
2. Go to Profile → Tools → API Access
3. Enable API access and whitelist your IP
4. Note your API Key, Username, and Client IP

#### Cloudflare
1. Log in to your Cloudflare account
2. Go to My Profile → API Tokens
3. Create a token with these permissions:
   - Zone:Edit, Zone:Read, DNS:Edit
   - Include: All zones

## Usage

### Basic Commands

```bash
# Check domain status
regflow example.com --status

# Setup domain (idempotent)
regflow example.com --setup

# Dry run (preview changes)
regflow example.com --setup --dry-run

# Register new domain (requires confirmation)
regflow example.com --setup --force-registration

# Setup without worker subdomain
regflow example.com --setup --no-workers
```

### Command Options

| Option | Description |
|--------|-------------|
| `--status` | Show current domain status across all services |
| `--setup` | Set up domain (default action if no option specified) |
| `--dry-run` | Show what would be done without making changes |
| `--force-registration` | Allow domain registration (costs money!) |
| `--no-workers` | Skip worker subdomain setup |

### Status Output

The status command shows:
- ✅ Domain registration status in Namecheap
- ✅ Cloudflare zone existence and details
- ✅ Current nameservers from both services
- ✅ Nameserver synchronization status

Example output:
```
=== Domain Status: example.com ===
✓ Domain is registered in Namecheap
✓ Cloudflare zone exists (ID: abc123, Status: active)
Namecheap nameservers: ns1.cloudflare.com, ns2.cloudflare.com
Cloudflare nameservers: ns1.cloudflare.com, ns2.cloudflare.com
✓ Nameservers are properly configured
==================================================
```

## Domain Setup Process

RegFlow follows this idempotent workflow:

1. **Domain Registration Check** - Verify domain is registered in Namecheap
2. **Domain Registration** - Register domain if needed (with user confirmation)
3. **Cloudflare Zone Creation** - Create zone if it doesn't exist
4. **Nameserver Retrieval** - Get Cloudflare nameservers
5. **Nameserver Synchronization** - Update Namecheap nameservers if needed
6. **DNS Record Setup** - Configure basic DNS records
7. **Worker Subdomain** - Optional app.domain.com setup

## Safety Features

### Domain Registration Protection
- Requires explicit `--force-registration` flag
- Multiple confirmation prompts
- Shows exact cost before charging
- Dry-run mode available

### Idempotent Operations
- Safe to run multiple times
- Only makes necessary changes
- Skips completed steps
- Preserves existing configuration

### Error Handling
- Graceful API failure handling
- Clear error messages
- Rollback on critical failures
- Detailed logging

## Examples

### New Domain Registration
```bash
# Check if domain is available
regflow newdomain.com --status

# Register and set up completely (with confirmation)
regflow newdomain.com --setup --force-registration

# Preview the registration process
regflow newdomain.com --setup --force-registration --dry-run
```

### Existing Domain Management
```bash
# Check current configuration
regflow existingdomain.com --status

# Fix nameserver configuration
regflow existingdomain.com --setup

# Set up without worker subdomain
regflow existingdomain.com --setup --no-workers
```

### Troubleshooting Setup
```bash
# See what would be changed
regflow domain.com --setup --dry-run

# Check detailed status
regflow domain.com --status

# Force nameserver update
regflow domain.com --setup
```

## Development

### Running Tests

```bash
# Run all tests
pytest regflow/tests/

# Run specific test category
pytest regflow/tests/ -k "nameserver"

# Run with verbose output
pytest regflow/tests/ -v
```

### Project Structure

```
regflow/
├── __init__.py
├── config.py              # Configuration management
├── domains.py             # Main domain orchestration
├── providers/
│   ├── namecheap.py       # Namecheap API client
│   ├── cloudflare.py      # Cloudflare API client
│   └── __init__.py
└── tests/
    ├── test_integration.py # Integration tests
    └── __init__.py
```

### Adding New Providers

1. Create new provider module in `regflow/providers/`
2. Implement required methods (register, configure, status)
3. Add integration to `domains.py`
4. Add tests to `test_integration.py`

## Troubleshooting

### Common Issues

**API Authentication Errors**
- Verify API credentials in `.env`
- Check IP whitelist for Namecheap
- Verify Cloudflare token permissions

**Domain Not Found**
- Ensure domain is registered in Namecheap account
- Check domain spelling and TLD
- Verify API access to domain

**Nameserver Issues**
- Allow up to 24 hours for nameserver propagation
- Check domain registrar settings
- Verify Cloudflare zone is active

### Error Messages

| Error | Solution |
|-------|----------|
| `Missing required API credentials` | Add all required variables to `.env` |
| `Domain not registered and force_registration not enabled` | Use `--force-registration` to register |
| `Cannot retrieve nameservers` | Check API credentials and domain ownership |
| `Insufficient balance` | Add funds to Namecheap account |

## API Rate Limits

- **Namecheap**: No official limits, but be respectful
- **Cloudflare**: 1200 requests per 5 minutes per token

## Security Notes

- Store API credentials securely
- Use environment variables, not hardcoded values
- Regular credential rotation recommended
- Enable two-factor authentication on provider accounts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## License

[Add your license here]

## Support

- **Documentation**: This README
- **Issues**: [GitHub Issues](link-to-issues)
- **API Docs**: [Namecheap API](https://www.namecheap.com/support/api/intro/) | [Cloudflare API](https://developers.cloudflare.com/api/)