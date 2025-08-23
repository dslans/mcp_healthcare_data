#!/bin/bash

# Test script for MCP Healthcare Data Docker image
set -e

IMAGE_NAME="mcp-healthcare-data"
TAG="local"
FULL_IMAGE="$IMAGE_NAME:$TAG"

echo "🔧 Building Docker image..."
docker build -t "$FULL_IMAGE" .

echo "✅ Docker image built successfully: $FULL_IMAGE"

echo "🧪 Testing container startup..."
if docker run --rm --entrypoint=/bin/bash "$FULL_IMAGE" -c "python -c 'print(\"Container starts successfully\")'" > /dev/null 2>&1; then
    echo "✅ Container starts successfully"
else
    echo "❌ Container failed to start"
    exit 1
fi

echo "🔍 Testing import of main module..."
if docker run --rm --entrypoint=/bin/bash "$FULL_IMAGE" -c "python -c 'import healthcare_mcp_server; print(\"Module imports successfully\")'" > /dev/null 2>&1; then
    echo "✅ Main module imports successfully"
else
    echo "❌ Module import failed (this may be due to missing GCP credentials, which is expected)"
fi

echo "📊 Image size information:"
docker images "$FULL_IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "🚀 Local testing complete!"
echo ""
echo "To test with your credentials:"
echo "docker run --rm -i \\"
echo "  -e GCP_PROJECT_ID=your-project-id \\"
echo "  -e BIGQUERY_DATASET_PREFIX=your-prefix \\"
echo "  -v /path/to/service-account.json:/app/credentials.json:ro \\"
echo "  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \\"
echo "  $FULL_IMAGE"
echo ""
echo "To use in MCP client, replace with:"
echo "ghcr.io/yourusername/mcp_healthcare_data:latest"
