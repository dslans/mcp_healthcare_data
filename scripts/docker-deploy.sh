#!/bin/bash
# Healthcare MCP Server - Docker Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏥 Healthcare MCP Server - Docker Deployment${NC}"
echo "=================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Default values
IMAGE_NAME="healthcare-mcp-server"
IMAGE_TAG="latest"
PORT="8000"
CONTAINER_NAME="healthcare-mcp-server"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --port PORT          Port to run the server on (default: 8000)"
            echo "  --tag TAG            Docker image tag (default: latest)"
            echo "  --name NAME          Container name (default: healthcare-mcp-server)"
            echo "  --build-only         Only build the image, don't run it"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build the Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Exit if build-only flag is set
if [ "${BUILD_ONLY}" = true ]; then
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    exit 0
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
    docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 Please edit .env file with your actual configuration before running the container.${NC}"
        echo -e "${YELLOW}   Required variables: GCP_PROJECT_ID, BIGQUERY_DATASET_PREFIX${NC}"
        echo -e "${YELLOW}   Optional: GOOGLE_APPLICATION_CREDENTIALS${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example file not found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

# Run the container
echo -e "${YELLOW}🚀 Starting Healthcare MCP Server container...${NC}"
docker run -d \
    --name ${CONTAINER_NAME} \
    --port ${PORT}:8000 \
    --env-file .env \
    --restart unless-stopped \
    ${IMAGE_NAME}:${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo ""
    echo -e "${GREEN}📋 Container Information:${NC}"
    echo "   Name: ${CONTAINER_NAME}"
    echo "   Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "   Port: ${PORT}"
    echo "   URL: http://localhost:${PORT}"
    echo ""
    echo -e "${GREEN}📊 Useful commands:${NC}"
    echo "   View logs:    docker logs ${CONTAINER_NAME}"
    echo "   Stop server:  docker stop ${CONTAINER_NAME}"
    echo "   Start server: docker start ${CONTAINER_NAME}"
    echo "   Remove:       docker rm -f ${CONTAINER_NAME}"
    echo ""
    echo -e "${GREEN}🎉 Healthcare MCP Server is now running!${NC}"
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi
