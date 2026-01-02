# Auth0 CLI Setup Guide

This guide explains how to use the Auth0 CLI to configure and manage Auth0 settings from the command line, similar to how Vercel CLI works.

## Auth0 CLI Tools

Auth0 provides two main CLI tools:

1. **Auth0 CLI** - For building, managing, and testing Auth0 integrations
2. **Auth0 Deploy CLI** - For managing Auth0 tenant configuration (apps, APIs, rules, etc.)

## Installation

### Windows (Scoop)

```powershell
# Install Scoop if you don't have it
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Add Auth0 bucket and install
scoop bucket add auth0 https://github.com/auth0/scoop-auth0-cli.git
scoop install auth0
```

### macOS (Homebrew)

```bash
brew tap auth0/auth0-cli
brew install auth0
```

### Linux

```bash
curl -sSfL https://raw.githubusercontent.com/auth0/auth0-cli/main/install.sh | sh -s -- -b .
```

### npm (Cross-platform)

```bash
npm install -g @auth0/auth0-cli
```

## Auth0 Deploy CLI (For Configuration Management)

```bash
npm install -g auth0-deploy-cli
```

## Quick Start with Auth0 CLI

### 1. Login to Auth0

```bash
auth0 login
```

This will open your browser to authenticate and authorize the CLI.

### 2. Set Your Tenant

```bash
auth0 tenants use <your-tenant-name>
```

Or set it via environment variable:
```bash
export AUTH0_DOMAIN="your-tenant.auth0.com"
```

### 3. Test Universal Login

```bash
auth0 test login
```

### 4. List Applications

```bash
auth0 apps list
```

### 5. Create an Application

```bash
auth0 apps create \
  --name "Upload Bridge License Server" \
  --type "native" \
  --description "Native application for Upload Bridge desktop client"
```

### 6. Configure Application Settings

```bash
# Get application details
auth0 apps show <app-id>

# Update application (use API or config file for complex updates)
```

## Using Auth0 Deploy CLI for Configuration

The Auth0 Deploy CLI allows you to manage your Auth0 configuration as code, similar to Infrastructure as Code.

### 1. Initialize Configuration

```bash
auth0 deploy init
```

This creates a directory structure:
```
auth0/
├── clients/
├── resource-servers/
├── connections/
├── pages/
└── tenant.yaml
```

### 2. Export Current Configuration

```bash
auth0 deploy export \
  --output-folder ./auth0-config \
  --format yaml \
  --env AUTH0_DOMAIN="your-tenant.auth0.com" \
  --env AUTH0_CLIENT_ID="your-client-id" \
  --env AUTH0_CLIENT_SECRET="your-client-secret"
```

### 3. Create Configuration Files

Create `auth0-config/clients/upload-bridge-native.yaml`:

```yaml
name: Upload Bridge License Server
description: Native application for Upload Bridge desktop client
app_type: native
callbacks:
  - http://localhost:3000/callback
  - https://j-tech-licensing.vercel.app/callback
allowed_logout_urls:
  - http://localhost:3000
  - https://j-tech-licensing.vercel.app
allowed_origins:
  - http://localhost:3000
  - https://j-tech-licensing.vercel.app
grant_types:
  - authorization_code
  - refresh_token
token_endpoint_auth_method: none
```

### 4. Deploy Configuration

```bash
auth0 deploy \
  --input-file ./auth0-config \
  --env AUTH0_DOMAIN="your-tenant.auth0.com" \
  --env AUTH0_CLIENT_ID="your-client-id" \
  --env AUTH0_CLIENT_SECRET="your-client-secret"
```

## Automated Setup Script

We've created an automated setup script that uses Auth0 CLI to configure everything:

### Windows

```powershell
.\setup-auth0-cli.ps1
```

### Linux/Mac

```bash
./setup-auth0-cli.sh
```

## Common Auth0 CLI Commands

### Applications

```bash
# List all applications
auth0 apps list

# Show application details
auth0 apps show <app-id>

# Create application
auth0 apps create --name "My App" --type "native"

# Update application (requires API access)
# Use Auth0 Deploy CLI for complex updates
```

### APIs (Resource Servers)

```bash
# List APIs
auth0 apis list

# Show API details
auth0 apis show <api-id>

# Create API
auth0 apis create \
  --name "Upload Bridge License API" \
  --identifier "https://j-tech-licensing.vercel.app" \
  --signing-algorithm "RS256"
```

### Connections

```bash
# List connections
auth0 connections list

# Show connection details
auth0 connections show <connection-id>
```

### Test Authentication Flow

```bash
# Test login flow
auth0 test login

# Test with specific connection
auth0 test login --connection "Username-Password-Authentication"
```

## Environment Variables for Auth0 Deploy CLI

Create a `.env` file or set environment variables:

```bash
# Required
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-management-api-client-id
AUTH0_CLIENT_SECRET=your-management-api-client-secret

# Optional
AUTH0_API_TOKEN=your-api-token  # Alternative to client ID/secret
```

## Configuration as Code Example

Example `auth0-config/tenant.yaml`:

```yaml
tenant:
  enabled_locales:
    - en

clients:
  - name: Upload Bridge License Server
    description: Native application for Upload Bridge
    app_type: native
    callbacks:
      - http://localhost:3000/callback
      - https://j-tech-licensing.vercel.app/callback
    allowed_logout_urls:
      - http://localhost:3000
      - https://j-tech-licensing.vercel.app
    allowed_origins:
      - http://localhost:3000
      - https://j-tech-licensing.vercel.app
    grant_types:
      - authorization_code
      - refresh_token

resourceServers:
  - name: Upload Bridge License API
    identifier: https://j-tech-licensing.vercel.app
    signing_alg: RS256
    scopes:
      - value: read:licenses
        description: Read license information
      - value: write:licenses
        description: Manage licenses

connections:
  - name: Username-Password-Authentication
    enabled_clients:
      - Upload Bridge License Server
```

## Integration with Our Project

### Step 1: Install Auth0 CLI

```powershell
# Windows
scoop install auth0

# Or via npm
npm install -g @auth0/auth0-cli
```

### Step 2: Login

```bash
auth0 login
```

### Step 3: Export Current Config (if you have existing setup)

```bash
auth0 deploy export \
  --output-folder ./auth0-config \
  --format yaml
```

### Step 4: Update Configuration Files

Edit the exported configuration or create new ones following the examples above.

### Step 5: Deploy

```bash
auth0 deploy --input-file ./auth0-config
```

## Benefits of Using Auth0 CLI

1. **Automation** - Configure Auth0 programmatically
2. **Version Control** - Store configuration in Git
3. **Reproducibility** - Same configuration across environments
4. **CI/CD Integration** - Deploy Auth0 config as part of your pipeline
5. **Testing** - Test authentication flows from command line

## Limitations

- Some features still require the Auth0 Dashboard
- Complex configurations may be easier in the Dashboard
- Management API permissions needed for Deploy CLI

## Troubleshooting

### "Command not found"

Make sure Auth0 CLI is installed and in your PATH:
```bash
auth0 --version
```

### "Authentication failed"

Re-authenticate:
```bash
auth0 logout
auth0 login
```

### "Insufficient permissions"

Make sure your Management API application has the required scopes:
- `read:clients`
- `update:clients`
- `create:clients`
- `read:resource_servers`
- `update:resource_servers`
- `create:resource_servers`

## References

- [Auth0 CLI Documentation](https://github.com/auth0/auth0-cli)
- [Auth0 Deploy CLI Documentation](https://auth0.com/docs/deploy-monitor/deploy-cli-tool)
- [Auth0 Management API](https://auth0.com/docs/api/management/v2)

