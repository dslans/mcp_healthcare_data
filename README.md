# Healthcare Analytics MCP Server

A comprehensive Model Context Protocol (MCP) server for healthcare data analysis using Tuva Health demo data. This server provides tools for value-based care analytics, quality measures, utilization analysis, and financial metrics commonly used in healthcare organizations.

## Motivation
To get a quick MCP setup that can be used to service most of the common data questions that get floated over to analysts and are simple data pulls. Something like this could be utilized at healthcare companies to free up time for analysts to work on more complicated analytics, while also providing well-defined queries to be reused across an org. 
- Tuva Health provides a typical database setup that translates well across the industry. 
- Warp (I think it was using Sonnet) did pretty well with the initial setup. I had the demo data loaded to bigquery and MCP toolbox for databases set up so it could get context from the existing tables. The queries were wrong, but only required minimal fixes. The scaffolding is there for analysts to write official queries to be used by the server.

## Features

### Core Analytics Tools
- **Patient Demographics**: Age groups, gender distribution, enrollment analysis
- **Utilization Summary**: Claims analysis, service category breakdown
- **PMPM Analysis**: Per Member Per Month financial metrics with trends
- **Quality Measures**: HEDIS and clinical quality indicator tracking
- **Chronic Conditions**: Prevalence analysis and condition family insights
- **High-Cost Patients**: Case management identification
- **Readmissions Analysis**: 30-day readmission patterns
- **HCC Risk Scores**: Risk adjustment and stratification

### Value-Based Care Metrics
- Risk-adjusted cost analysis
- Quality performance tracking
- Population health insights
- Care gap identification
- Financial performance monitoring

## Setup

### Prerequisites
- Python 3.8+
- Google Cloud Project with BigQuery API enabled
- Tuva Health demo data loaded in BigQuery
- Service account with BigQuery access

### Installation

1. Install dependencies using uv (recommended):
```bash
uv pip install -r requirements.txt
```

2. Set up environment variables by copying `.env.example` to `.env`:
```bash
cp .env.example .env
```

3. Configure your `.env` file with:
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
GCP_PROJECT_ID=your-project-id
BIGQUERY_DATASET_PREFIX=your_dataset_prefix
```

### Google Cloud Authentication

The server supports two authentication methods:

#### Option 1: Service Account JSON File (Recommended for Local Development)

1. Create a Google Cloud service account:
```bash
gcloud iam service-accounts create healthcare-mcp-server \
    --display-name="Healthcare MCP Server"
```

2. Grant BigQuery permissions:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:healthcare-mcp-server@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:healthcare-mcp-server@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"
```

3. Download service account key:
```bash
gcloud iam service-accounts keys create ~/healthcare-mcp-key.json \
    --iam-account=healthcare-mcp-server@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. Set the path in your `.env` file:
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/healthcare-mcp-key.json
```

#### Option 2: Application Default Credentials (Recommended for Cloud Deployments)

For cloud deployments (Google Cloud Run, Compute Engine, etc.), you can use ADC:

1. Leave `GOOGLE_APPLICATION_CREDENTIALS` empty or unset in your `.env` file
2. Ensure your compute environment has the necessary BigQuery permissions
3. For local development with ADC:

```bash
# Authenticate with your user account
gcloud auth application-default login

# Or set up ADC with a service account
gcloud auth application-default login --impersonate-service-account=healthcare-mcp-server@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Usage

### Running the Server

Start the MCP server:
```bash
fastmcp run healthcare_mcp_server.py
```

Set up the config with your IDE, CLI assistant, etc.
```json
{
  "mcpServers": {
    "healthcare-analytics": {
      "command": "python",
      "args": ["/path/to/your/healthcare_mcp_server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GCP_PROJECT_ID": "your-project-id",
        "BIGQUERY_DATASET_PREFIX": "your_dataset_prefix."
      }
    }
  }
}
```

### Available Tools

#### 1. Patient Demographics Analysis
```python
get_patient_demographics(
    start_date="2018-01-01",
    end_date="2018-12-31", 
    age_groups=True
)
```
Returns demographic breakdown including age groups, gender distribution, and total patient counts.

#### 2. Healthcare Utilization Summary
```python
get_utilization_summary(
    start_date="2018-01-01",
    end_date="2018-12-31",
    service_category="Emergency Department"  # Optional
)
```
Provides comprehensive utilization metrics including claims counts, costs, and service category breakdowns.

#### 3. PMPM Financial Analysis
```python
get_pmpm_analysis(
    start_date="2018-01-01",
    end_date="2018-12-31",
    payer="Medicare"  # Optional
)
```
Calculates Per Member Per Month costs across different service categories with trend analysis.

#### 4. Quality Measures Summary
```python
get_quality_measures_summary(
    measure_name="adh_diabetes",  # Optional - use actual column names like 'adh_diabetes', 'cqm_130', etc.
    year="2018"
)
```
Returns quality measure performance rates and compliance flags for HEDIS and clinical measures.

#### 5. Chronic Conditions Prevalence
```python
get_chronic_conditions_prevalence(
    condition_category="Diabetes",  # Optional
    year="2018"
)
```
Analyzes prevalence rates for chronic conditions across the patient population.

#### 6. High-Cost Patient Identification
```python
get_high_cost_patients(
    cost_threshold=10000.0,
    year="2018",
    limit=100
)
```
Identifies patients exceeding cost thresholds for case management prioritization.

#### 7. Readmissions Analysis
```python
get_readmissions_analysis(
    year="2018",
    condition_category="Heart Failure"  # Optional
)
```
Calculates 30-day readmission rates and patterns for quality improvement.

#### 8. HCC Risk Score Analysis
```python
get_hcc_risk_scores(
    year="2018",
    limit=1000
)
```
Provides HCC risk score distribution and population risk stratification.

## Data Structure

The server expects Tuva Health formatted data with the following key datasets:
- `core.*` - Claims, patient, eligibility, and encounter data
- `quality_measures.*` - HEDIS and clinical quality measures
- `financial_pmpm.*` - Per Member Per Month financial calculations
- `chronic_conditions.*` - Chronic condition classifications
- `cms_hcc.*` - HCC risk adjustment data
- `readmissions.*` - Readmission analysis results

## Example Use Cases

### Value-Based Care Analytics
```python
# Get overall population health metrics
demographics = get_patient_demographics()
quality = get_quality_measures_summary()
chronic = get_chronic_conditions_prevalence()

# Analyze cost and utilization patterns
pmpm = get_pmpm_analysis()
utilization = get_utilization_summary()

# Identify care management opportunities  
high_cost = get_high_cost_patients(cost_threshold=15000)
risk_scores = get_hcc_risk_scores()
```

### Monthly Performance Reporting
```python
# Generate monthly financial and quality reports
monthly_pmpm = get_pmpm_analysis(
    start_date="2018-01-01",
    end_date="2018-01-31"
)

monthly_quality = get_quality_measures_summary(year="2018")
monthly_readmissions = get_readmissions_analysis(year="2018")
```

## Development

### Adding New Tools

To add new healthcare analytics tools:

1. Create a new function with the `@mcp.tool()` decorator
2. Add proper type hints and documentation
3. Use the `execute_query()` helper for BigQuery operations
4. Return structured data as dictionaries

Example:
```python
@mcp.tool()
def get_medication_adherence(
    therapeutic_class: str,
    year: str = "2018"
) -> Dict[str, Any]:
    """
    Calculate medication adherence rates for a therapeutic class.
    
    Args:
        therapeutic_class: Medication therapeutic class
        year: Analysis year
        
    Returns:
        Dictionary with adherence metrics
    """
    query = f"""
    SELECT 
        COUNT(DISTINCT person_id) as total_patients,
        AVG(pdc_score) as avg_adherence_rate
    FROM `{DATASET_PREFIX}pharmacy.adherence_scores`
    WHERE therapeutic_class = '{therapeutic_class}'
      AND measurement_year = {year}
    """
    
    df = execute_query(query)
    return df.iloc[0].to_dict()
```

### Testing

Run basic validation tests:
```bash
python -c "
import healthcare_mcp_server as hms
# Test BigQuery connection
print('Testing connection...')
result = hms.get_patient_demographics()
print(f'Found {result[\"total_patients\"]} patients')
"
```

## Docker Deployment

Run the healthcare MCP server in a Docker container for easy deployment and isolation.

### Quick Start

1. **Build and run with Docker script:**
```bash
./scripts/docker-deploy.sh
```

2. **Manual Docker commands:**
```bash
# Build the image
docker build -t healthcare-mcp-server .

# Run the container
docker run -d \
  --name healthcare-mcp-server \
  --port 8000:8000 \
  --env-file .env \
  healthcare-mcp-server
```

### Docker Script Options

```bash
# Custom port and container name
./scripts/docker-deploy.sh --port 8080 --name my-mcp-server

# Build only (don't run)
./scripts/docker-deploy.sh --build-only

# Help
./scripts/docker-deploy.sh --help
```

### Docker Compose (Optional)

Create a `docker-compose.yml` for easier management:
```yaml
version: '3.8'
services:
  healthcare-mcp:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

## Cloud Run Deployment

Deploy to Google Cloud Run for scalable, serverless hosting.

### Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Required APIs will be enabled automatically

### Quick Start

1. **Deploy with Cloud Run script:**
```bash
./scripts/cloud-run-deploy.sh YOUR_PROJECT_ID
```

2. **With custom configuration:**
```bash
./scripts/cloud-run-deploy.sh MY_PROJECT \
  --region us-west1 \
  --dataset-prefix my_tuva_data \
  --service-name my-healthcare-server
```

### Manual Cloud Run Deployment

```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Build and deploy with Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or deploy directly
gcloud run deploy healthcare-mcp-server \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Cloud Run Configuration

- **Memory**: 1GB (configurable)
- **CPU**: 1 vCPU (configurable) 
- **Concurrency**: 100 requests per instance
- **Autoscaling**: 0-10 instances
- **Authentication**: Uses Google Cloud ADC

### Environment Variables for Cloud Run

Set these in the Cloud Run service:
- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `BIGQUERY_DATASET_PREFIX`: Your dataset prefix (e.g., `tuva_synthetic_data`)

### MCP Client Configuration for Cloud Run

Once deployed, configure your MCP client:
```json
{
  "mcpServers": {
    "healthcare-analytics": {
      "command": "curl",
      "args": ["-X", "POST", "https://your-service-url/mcp"],
      "env": {}
    }
  }
}
```

## Deployment Comparison

| Option | Best For | Pros | Cons |
|--------|----------|------|----- |
| **Local Development** | Testing, development | Full control, easy debugging | Requires local setup |
| **Docker** | Small teams, on-premises | Portable, isolated, consistent | Requires Docker knowledge |
| **Cloud Run** | Production, scale | Serverless, auto-scaling, managed | Cloud vendor lock-in |

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your service account key path is correct in `.env`
2. **Dataset Not Found**: Verify your `BIGQUERY_DATASET_PREFIX` matches your data location
3. **Permission Denied**: Confirm your service account has BigQuery viewer/user roles
4. **Import Errors**: Ensure all dependencies are installed with `uv pip install -r requirements.txt`
5. **Docker Build Fails**: Check that Docker is running and you have sufficient disk space
6. **Cloud Run Deploy Fails**: Verify your Google Cloud project has billing enabled

### Docker Troubleshooting

```bash
# View container logs
docker logs healthcare-mcp-server

# Debug inside container
docker exec -it healthcare-mcp-server bash

# Check container status
docker ps -a
```

### Cloud Run Troubleshooting

```bash
# View service logs
gcloud run services logs tail healthcare-mcp-server --region=us-central1

# Check service status
gcloud run services describe healthcare-mcp-server --region=us-central1

# View recent builds
gcloud builds list --limit=10
```

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Warp (or IDE) Integration

### MCP Bridge

For an integrated experience, use the MCP bridge that provides native MCP tools:

1. **Install the bridge dependencies:**
```bash
pip install httpx
```

2. **Test the bridge:**
```bash
python healthcare_mcp_bridge.py --test
```

3. **Configure Warp with the bridge:**
```json
{
  "mcpServers": {
    "healthcare-analytics": {
      "command": "python",
      "args": ["/absolute/path/to/healthcare_mcp_bridge.py"],
      "env": {
        "CLOUD_RUN_URL": "https://healthcare-mcp-server-842907846470.us-central1.run.app"
      }
    }
  }
}
```

4. **Use natural language commands:**
```
"Get patient demographics for 2018"
"Show me high-cost patients with threshold over $20,000"
"Analyze readmissions for diabetes patients"
```

**Pros:**
- ✅ Native MCP integration
- ✅ Natural language interface
- ✅ Automatic parameter handling
- ✅ Type-safe tool definitions

**Cons:**
- ❌ Requires setup
- ❌ Additional dependency layer


### Available API Endpoints

All endpoints accept JSON POST requests unless otherwise noted:

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/health` | GET | Service health check |
| `/api/info` | GET | API documentation |
| `/analytics/demographics` | POST | Patient demographics analysis |
| `/analytics/utilization` | POST | Healthcare utilization summary |
| `/analytics/pmpm` | POST | PMPM financial analysis |
| `/analytics/quality-measures` | POST | Quality measures summary |
| `/analytics/chronic-conditions` | POST | Chronic conditions prevalence |
| `/analytics/high-cost-patients` | POST | High-cost patient identification |
| `/analytics/readmissions` | POST | Readmissions analysis |
| `/analytics/hcc-risk-scores` | POST | HCC risk scores analysis |

### Example API Request Bodies

**Demographics:**
```json
{
  "start_date": "2018-01-01",
  "end_date": "2018-12-31",
  "age_groups": true
}
```

**High-Cost Patients:**
```json
{
  "cost_threshold": 10000.0,
  "year": "2018",
  "limit": 100
}
```

**Quality Measures:**
```json
{
  "measure_name": "adh_diabetes",
  "year": "2018"
}
```
