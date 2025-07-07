#!/bin/bash

# Build Docker images for Kubernetes deployment

set -e

echo "🐳 Building Docker images for ML Platform..."

# Check if we're using minikube
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "📦 Using minikube Docker environment"
    eval $(minikube docker-env)
fi

# Build Model Registry API image
echo "🔨 Building Model Registry API image..."
cd api
docker build -t ml-platform/api:latest .
cd ..

# Build Inference Server image
echo "🔨 Building Inference Server image..."
cd inference-server
docker build -t ml-platform/inference-server:latest .
cd ..

# Build Operator image
echo "🔨 Building Operator image..."
cd operator
docker build -t ml-platform/operator:latest .
cd ..

echo "✅ All Docker images built successfully!"

# List built images
echo "📋 Built images:"
docker images | grep ml-platform

echo ""
echo "🚀 Images are ready for Kubernetes deployment!"
echo "   Next: Run ./scripts/deploy-k8s.sh"