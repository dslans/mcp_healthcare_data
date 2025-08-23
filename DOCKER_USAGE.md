# Using MCP Healthcare Data Server with Docker

This guide explains how to use the MCP Healthcare Data Server using the pre-built Docker image from GitHub Container Registry.

## Prerequisites

1. **Docker** installed on your machine
2. **MCP-compatible client** such as:
   - Claude Desktop
   - Warp Terminal (with MCP support)
   - Any other MCP client

## Quick Start

### For Claude Desktop Users

1. **Configure Claude Desktop** by editing your `claude_desktop_config.json` file:

   **macOS:**
   ```bash
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows:**
   ```bash
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Add the MCP server configuration:**
   ```json
   {
     "mcpServers": {
       "healthcare-data": {
         "command": "docker",
         "args": [
           "run", 
           "--rm", 
           "-i",
           "--pull=always",
           "-e", "GCP_PROJECT_ID=your-gcp-project-id",
           "-e", "BIGQUERY_DATASET_PREFIX=your-dataset-prefix",
           "ghcr.io/yourusername/mcp_healthcare_data:latest"
         ]
       }
     }
   }
   ```

3. **Set up your environment variables:**
   - Replace `your-gcp-project-id` with your actual GCP project ID
   - Replace `your-dataset-prefix` with your BigQuery dataset prefix
   - Replace `yourusername` with the actual GitHub username/organization

4. **For GCP Authentication**, you have two options:

   **Option A: Service Account Key (Recommended)**
   ```json
   {
     "mcpServers": {
       "healthcare-data": {
         "command": "docker",
         "args": [
           "run", 
           "--rm", 
           "-i",
           "--pull=always",
           "-v", "/path/to/your/service-account.json:/app/credentials.json:ro",
           "-e", "GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json",
           "-e", "GCP_PROJECT_ID=your-gcp-project-id",
           "-e", "BIGQUERY_DATASET_PREFIX=your-dataset-prefix",
           "ghcr.io/yourusername/mcp_healthcare_data:latest"
         ]
       }
     }
   }
   ```

   **Option B: Application Default Credentials (ADC)**
   
   First, authenticate with gcloud:
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```
   
   Then configure your MCP client:
   ```json
   {
     "mcpServers": {
       "healthcare-data": {
         "command": "docker",
         "args": [
           "run", 
           "--rm", 
           "-i",
           "--pull=always",
           "-v", "~/.config/gcloud:/home/appuser/.config/gcloud:ro",
           "-e", "GCP_PROJECT_ID=your-gcp-project-id",
           "-e", "BIGQUERY_DATASET_PREFIX=your-dataset-prefix",
           "ghcr.io/yourusername/mcp_healthcare_data:latest"
         ]
       }
     }
   }
   ```

5. **Restart Claude Desktop** to load the new configuration.

### For Warp Terminal Users

1. **Configure Warp MCP** in your terminal settings or configuration file with the same Docker command structure as above.

2. **Activate the MCP server** within Warp terminal sessions.

## Available Tools

Once configured, you'll have access to these healthcare analytics tools:

- `get_patient_demographics` - Patient demographic analysis
- `get_utilization_summary` - Healthcare utilization metrics
- `get_chronic_conditions_prevalence` - Chronic condition statistics
- `get_high_cost_patients` - High-cost patient analysis
- `get_pmpm_analysis` - Per-member-per-month cost analysis
- `get_readmission_analysis` - Hospital readmission metrics
- `get_quality_measures` - Healthcare quality indicators
- `get_medication_adherence` - Medication compliance analysis
- `get_provider_network_analysis` - Provider network utilization
- `get_risk_adjustment` - Risk adjustment calculations

## Configuration Options

### Environment Variables

- `GCP_PROJECT_ID` - Your Google Cloud Project ID (required)
- `BIGQUERY_DATASET_PREFIX` - Prefix for your BigQuery datasets (optional)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON file (optional)

### Docker Volume Mounts

For persistent authentication:
```bash
-v "/path/to/credentials.json:/app/credentials.json:ro"
```

For gcloud ADC:
```bash
-v "~/.config/gcloud:/home/appuser/.config/gcloud:ro"
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure your GCP credentials are properly configured
   - Verify the service account has BigQuery permissions
   - Check that the volume mounts are correct

2. **Docker Pull Issues**
   - Ensure you have internet connectivity
   - Check if the image name is correct
   - Make sure Docker is running

3. **Permission Errors**
   - Verify your BigQuery datasets are accessible
   - Check IAM permissions for your service account

### Testing the Connection

You can test the Docker container directly:

```bash
# Test basic container startup
docker run --rm \
  -e GCP_PROJECT_ID=your-project \
  -v /path/to/service-account.json:/app/credentials.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  ghcr.io/yourusername/mcp_healthcare_data:latest --help

# Interactive testing
docker run --rm -it \
  -e GCP_PROJECT_ID=your-project \
  -v /path/to/service-account.json:/app/credentials.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  --entrypoint=/bin/bash \
  ghcr.io/yourusername/mcp_healthcare_data:latest
```

## Updates

The Docker image automatically pulls the latest version with the `--pull=always` flag. To use a specific version:

```json
"ghcr.io/yourusername/mcp_healthcare_data:v1.0.0"
```

## Data Requirements

This MCP server expects Tuva Health formatted data in BigQuery. Ensure your datasets include:

- `core.patient` - Patient demographics
- `core.eligibility` - Member eligibility
- `core.medical_claim` - Medical claims data
- `core.pharmacy_claim` - Pharmacy claims data
- Additional Tuva tables as needed

## Security Notes

- Use read-only volume mounts for credential files
- Rotate service account keys regularly
- Limit BigQuery permissions to only required datasets
- Consider using Workload Identity for production deployments

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker and MCP client logs
3. Verify your BigQuery data structure and permissions
