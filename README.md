# Healthcare Analytics MCP Server

A comprehensive Model Context Protocol (MCP) server for healthcare data analysis using Tuva Health demo data. This server provides tools for value-based care analytics, quality measures, utilization analysis, and financial metrics commonly used in healthcare organizations.

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

### Available Tools

#### 1. Patient Demographics Analysis
```python
get_patient_demographics(
    start_date="2022-01-01",
    end_date="2022-12-31", 
    age_groups=True
)
```
Returns demographic breakdown including age groups, gender distribution, and total patient counts.

#### 2. Healthcare Utilization Summary
```python
get_utilization_summary(
    start_date="2022-01-01",
    end_date="2022-12-31",
    service_category="Emergency Department"  # Optional
)
```
Provides comprehensive utilization metrics including claims counts, costs, and service category breakdowns.

#### 3. PMPM Financial Analysis
```python
get_pmpm_analysis(
    start_date="2022-01-01",
    end_date="2022-12-31",
    payer="Medicare"  # Optional
)
```
Calculates Per Member Per Month costs across different service categories with trend analysis.

#### 4. Quality Measures Summary
```python
get_quality_measures_summary(
    measure_name="Diabetes HbA1c Testing",  # Optional
    year="2022"
)
```
Returns quality measure performance rates and compliance flags for HEDIS and clinical measures.

#### 5. Chronic Conditions Prevalence
```python
get_chronic_conditions_prevalence(
    condition_category="Diabetes",  # Optional
    year="2022"
)
```
Analyzes prevalence rates for chronic conditions across the patient population.

#### 6. High-Cost Patient Identification
```python
get_high_cost_patients(
    cost_threshold=10000.0,
    year="2022",
    limit=100
)
```
Identifies patients exceeding cost thresholds for case management prioritization.

#### 7. Readmissions Analysis
```python
get_readmissions_analysis(
    year="2022",
    condition_category="Heart Failure"  # Optional
)
```
Calculates 30-day readmission rates and patterns for quality improvement.

#### 8. HCC Risk Score Analysis
```python
get_hcc_risk_scores(
    year="2022",
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
    start_date="2022-01-01",
    end_date="2022-01-31"
)

monthly_quality = get_quality_measures_summary(year="2022")
monthly_readmissions = get_readmissions_analysis(year="2022")
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
    year: str = "2022"
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
        COUNT(DISTINCT patient_id) as total_patients,
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

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your service account key path is correct in `.env`
2. **Dataset Not Found**: Verify your `BIGQUERY_DATASET_PREFIX` matches your data location
3. **Permission Denied**: Confirm your service account has BigQuery viewer/user roles
4. **Import Errors**: Ensure all dependencies are installed with `uv pip install -r requirements.txt`

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

Apache 2.0 License
