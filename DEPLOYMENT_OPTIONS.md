# MCP Healthcare Data Server - Deployment Options

This document outlines the two main deployment options for the MCP Healthcare Data Server.

## Option 1: Docker Deployment (Recommended)

### Why Docker?
- ✅ **Zero Local Setup**: Users only need Docker installed
- ✅ **Automatic Updates**: `--pull=always` gets latest version
- ✅ **Consistent Environment**: Same runtime across all platforms
- ✅ **Easy Distribution**: GitHub Container Registry
- ✅ **Isolation**: No dependency conflicts

### Authentication Methods

#### A. Service Account Key (Recommended)
Best for production environments and when you need explicit control over permissions.

```json
{
  "mcpServers": {
    "healthcare-data": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--pull=always",
        "-v", "/path/to/service-account.json:/app/credentials.json:ro",
        "-e", "GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json",
        "-e", "GCP_PROJECT_ID=your-project-id",
        "-e", "BIGQUERY_DATASET_PREFIX=your-prefix",
        "ghcr.io/username/mcp_healthcare_data:latest"
      ]
    }
  }
}
```

#### B. Application Default Credentials (ADC)
Best for development when you're already authenticated with gcloud.

```bash
# First, authenticate
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

```json
{
  "mcpServers": {
    "healthcare-data": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--pull=always",
        "-v", "~/.config/gcloud:/home/appuser/.config/gcloud:ro",
        "-e", "GCP_PROJECT_ID=your-project-id",
        "-e", "BIGQUERY_DATASET_PREFIX=your-prefix",
        "ghcr.io/username/mcp_healthcare_data:latest"
      ]
    }
  }
}
```

## Option 2: Local Installation

### Why Local?
- ✅ **Development**: Easy to modify and customize code
- ✅ **Debugging**: Full access to logs and debugging tools
- ✅ **Learning**: Understand the codebase and dependencies
- ✅ **Custom Analytics**: Add your own healthcare tools

### Setup Steps

1. **Clone and Install**
   ```bash
   git clone <your-repo>
   cd mcp_healthcare_data
   uv pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your GCP credentials and project info
   ```

3. **Test Installation**
   ```bash
   python test_server.py
   ```

4. **Configure MCP Client**
   ```json
   {
     "mcpServers": {
       "healthcare-analytics": {
         "command": "python",
         "args": ["/full/path/to/healthcare_mcp_server.py"],
         "env": {
           "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json",
           "GCP_PROJECT_ID": "your-project-id",
           "BIGQUERY_DATASET_PREFIX": "your_prefix"
         }
       }
     }
   }
   ```

## Comparison

| Aspect | Docker | Local |
|--------|--------|-------|
| **Setup Time** | < 5 minutes | 10-15 minutes |
| **Maintenance** | Automatic updates | Manual updates |
| **Customization** | Limited | Full control |
| **Resource Usage** | Container overhead | Direct system |
| **Debugging** | Container logs | Full debugging |
| **Distribution** | Easy sharing | Requires setup |
| **Best For** | End users, production | Developers, customization |

## Recommendations

- **End Users**: Use Docker deployment with service account key
- **Developers**: Start with Docker, switch to local for customization
- **Organizations**: Docker for standardization, local for development
- **Quick Testing**: Docker with ADC if already authenticated

## Security Considerations

### Docker
- Use read-only volume mounts for credentials
- Rotate service account keys regularly
- Limit BigQuery dataset access
- Use specific image tags for production

### Local
- Store credentials outside the repository
- Use environment variables for secrets
- Keep dependencies updated
- Follow principle of least privilege

## Troubleshooting

### Docker Issues
- Ensure Docker is running
- Check image exists: `docker pull ghcr.io/username/mcp_healthcare_data:latest`
- Verify volume mounts are correct
- Check container logs: `docker logs <container>`

### Local Issues  
- Verify Python version (3.8+)
- Check all dependencies installed: `pip list`
- Validate environment variables in `.env`
- Test BigQuery connection independently

## Next Steps

1. Choose your deployment method
2. Follow the appropriate setup guide
3. Configure your MCP client
4. Test with sample healthcare queries
5. Customize analytics tools as needed

For detailed instructions, see:
- [README.md](README.md) - Complete setup guide
- [DOCKER_USAGE.md](DOCKER_USAGE.md) - Docker-specific instructions
