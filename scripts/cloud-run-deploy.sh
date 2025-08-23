#!/bin/bash
# Healthcare MCP Server - Cloud Run Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}☁️  Healthcare MCP Server - Cloud Run Deployment${NC}"
echo "======================================================"

# Default values
REGION="us-central1"
SERVICE_NAME="healthcare-mcp-server"
DATASET_PREFIX="tuva_synthetic_data"

# Function to show usage
show_usage() {
    echo "Usage: $0 <project-id> [options]"
    echo ""
    echo "Required:"
    echo "  project-id               Your Google Cloud Project ID"
    echo ""
    echo "Options:"
    echo "  --region REGION         Cloud Run region (default: us-central1)"
    echo "  --service-name NAME     Service name (default: healthcare-mcp-server)"
    echo "  --dataset-prefix PREFIX BigQuery dataset prefix (default: tuva_synthetic_data)"
    echo "  --build-only            Only build and push image, don't deploy"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 my-project-123"
    echo "  $0 my-project-123 --region us-west1 --dataset-prefix my_data"
    echo ""
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: Project ID is required${NC}"
    echo ""
    show_usage
    exit 1
fi

PROJECT_ID="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --dataset-prefix)
            DATASET_PREFIX="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Validate project ID format
if [[ ! "$PROJECT_ID" =~ ^[a-z0-9][a-z0-9-]{4,28}[a-z0-9]$ ]]; then
    echo -e "${RED}❌ Invalid project ID format. Must be 6-30 characters, lowercase letters, digits, and hyphens only.${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "   Project ID: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service Name: ${SERVICE_NAME}"
echo "   Dataset Prefix: ${DATASET_PREFIX}"
echo ""

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first:${NC}"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | grep -q "@"; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run:${NC}"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
echo -e "${YELLOW}🔧 Setting project...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    bigquery.googleapis.com

# Build and deploy using Cloud Build
echo -e "${YELLOW}🔨 Starting Cloud Build...${NC}"
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _DATASET_PREFIX=${DATASET_PREFIX} \
    --timeout=1200s

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Build failed${NC}"
    exit 1
fi

# Exit if build-only flag is set
if [ "${BUILD_ONLY}" = true ]; then
    echo -e "${GREEN}🎉 Build and push completed successfully!${NC}"
    echo -e "${GREEN}📦 Image available at: gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest${NC}"
    exit 0
fi

# Get the service URL
echo -e "${YELLOW}🔍 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

if [ $? -eq 0 ] && [ ! -z "$SERVICE_URL" ]; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    echo -e "${GREEN}🌐 Service Information:${NC}"
    echo "   Service Name: ${SERVICE_NAME}"
    echo "   Project: ${PROJECT_ID}"
    echo "   Region: ${REGION}"
    echo "   URL: ${SERVICE_URL}"
    echo ""
    echo -e "${GREEN}🔧 Management Commands:${NC}"
    echo "   View logs:    gcloud run services logs tail ${SERVICE_NAME} --region=${REGION}"
    echo "   Update:       gcloud run deploy ${SERVICE_NAME} --region=${REGION}"
    echo "   Delete:       gcloud run services delete ${SERVICE_NAME} --region=${REGION}"
    echo ""
    echo -e "${GREEN}📊 MCP Client Configuration:${NC}"
    echo "   Add this to your MCP client config:"
    echo "   {"
    echo "     \"mcpServers\": {"
    echo "       \"healthcare-analytics\": {"
    echo "         \"command\": \"curl\","
    echo "         \"args\": [\"-X\", \"POST\", \"${SERVICE_URL}/mcp\"],"
    echo "         \"env\": {}"
    echo "       }"
    echo "     }"
    echo "   }"
    echo ""
    echo -e "${GREEN}🎉 Healthcare MCP Server is now live on Cloud Run!${NC}"
else
    echo -e "${RED}❌ Failed to get service URL. Deployment may have failed.${NC}"
    exit 1
fi
