#!/bin/bash

# Healthcare MCP Server - Authentication Setup Script
# This script helps you set up Google Cloud authentication for the healthcare MCP server

set -e

echo "Healthcare Analytics MCP Server - Authentication Setup"
echo "======================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI found"

# Get project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Project ID is required"
    exit 1
fi

echo "🔧 Setting up authentication for project: $PROJECT_ID"

# Set the project
gcloud config set project "$PROJECT_ID"

echo ""
echo "Choose authentication method:"
echo "1) Service Account JSON file (recommended for local development)"
echo "2) Application Default Credentials (recommended for cloud deployments)"
read -p "Select option (1 or 2): " AUTH_OPTION

case $AUTH_OPTION in
    1)
        echo ""
        echo "🔐 Setting up Service Account authentication..."
        
        # Create service account
        SERVICE_ACCOUNT_NAME="healthcare-mcp-server"
        SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
        
        echo "Creating service account: $SERVICE_ACCOUNT_NAME"
        gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
            --display-name="Healthcare MCP Server" \
            --description="Service account for Healthcare Analytics MCP Server" || true
        
        # Grant permissions
        echo "Granting BigQuery permissions..."
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="roles/bigquery.user"
        
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="roles/bigquery.dataViewer"
        
        # Create and download key
        KEY_FILE="healthcare-mcp-key.json"
        echo "Creating service account key: $KEY_FILE"
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SERVICE_ACCOUNT_EMAIL"
        
        # Update .env file
        if [ -f ".env" ]; then
            # Update existing .env file
            sed -i.bak "s|^GCP_PROJECT_ID=.*|GCP_PROJECT_ID=$PROJECT_ID|" .env
            sed -i.bak "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/$KEY_FILE|" .env
            rm .env.bak
        else
            # Create new .env file
            cp .env.example .env
            sed -i.bak "s|your-project-id|$PROJECT_ID|" .env
            sed -i.bak "s|/path/to/your/service-account-key.json|$(pwd)/$KEY_FILE|" .env
            rm .env.bak
        fi
        
        echo ""
        echo "✅ Service Account setup complete!"
        echo "📝 Created: $KEY_FILE"
        echo "📝 Updated: .env"
        ;;
        
    2)
        echo ""
        echo "🔐 Setting up Application Default Credentials..."
        
        # Authenticate with ADC
        gcloud auth application-default login
        
        # Update .env file
        if [ -f ".env" ]; then
            # Update existing .env file
            sed -i.bak "s|^GCP_PROJECT_ID=.*|GCP_PROJECT_ID=$PROJECT_ID|" .env
            sed -i.bak "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|# GOOGLE_APPLICATION_CREDENTIALS=|" .env
            rm .env.bak
        else
            # Create new .env file
            cp .env.example .env
            sed -i.bak "s|your-project-id|$PROJECT_ID|" .env
            sed -i.bak "s|GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json|# GOOGLE_APPLICATION_CREDENTIALS=|" .env
            rm .env.bak
        fi
        
        echo ""
        echo "✅ Application Default Credentials setup complete!"
        echo "📝 Updated: .env"
        ;;
        
    *)
        echo "❌ Invalid option selected"
        exit 1
        ;;
esac

echo ""
echo "🧪 Testing authentication..."
python test_server.py

echo ""
echo "🎉 Setup complete! Your healthcare MCP server is ready to use."
echo ""
echo "To start the server:"
echo "  fastmcp run healthcare_mcp_server.py"
echo ""
echo "To test the server:"
echo "  python test_server.py"
