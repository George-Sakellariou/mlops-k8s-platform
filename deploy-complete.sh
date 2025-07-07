#!/bin/bash

# Complete ML Platform deployment script
# Deploys everything from Docker Compose to Kubernetes with sample models

set -e

echo "🚀 ML PLATFORM - COMPLETE DEPLOYMENT"
echo "======================================"
echo ""
echo "This script will:"
echo "  1. ✅ Verify prerequisites"
echo "  2. 🐳 Build Docker images"  
echo "  3. ☸️  Deploy to Kubernetes"
echo "  4. 📤 Upload sample models"
echo "  5. 🤖 Deploy ModelDeployments"
echo "  6. 🧪 Test predictions"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Prerequisites check
echo ""
echo "1️⃣  CHECKING PREREQUISITES"
echo "=========================="

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed"
    echo "💡 Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    echo "💡 Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check cluster access
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "💡 Ensure cluster is running and kubectl is configured"
    echo ""
    echo "🔧 Quick setup options:"
    echo "   - minikube: minikube start"
    echo "   - kind: kind create cluster"
    echo "   - Docker Desktop: Enable Kubernetes"
    exit 1
fi

# Check if sample models exist
if [ ! -d "examples/models" ] || [ ! -f "examples/models_metadata.json" ]; then
    echo "⚠️  Sample models not found. Creating them first..."
    echo ""
    
    # Ensure virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "🐍 Activating Python virtual environment..."
        source mlserv/bin/activate || {
            echo "❌ Virtual environment not found. Please run:"
            echo "   python3 -m venv mlserv"
            echo "   source mlserv/bin/activate"
            echo "   pip install -r requirements.txt"
            exit 1
        }
    fi
    
    # Create sample models
    echo "🤖 Creating sample models..."
    python examples/create_sample_models.py
    
    # Create metadata manually if script failed
    if [ ! -f "examples/models_metadata.json" ]; then
        echo "📋 Creating metadata file..."
        cat > examples/models_metadata.json << 'EOF'
{
  "iris_classifier_v1": {
    "model_type": "RandomForestClassifier",
    "framework": "scikit-learn",
    "accuracy": 1.0,
    "features": 4,
    "classes": 3,
    "use_case": "Multi-class classification of iris flowers"
  },
  "churn_predictor_v1": {
    "model_type": "LogisticRegression",
    "framework": "scikit-learn",
    "accuracy": 0.95,
    "features": 4,
    "classes": 2,
    "use_case": "Binary classification for customer churn prediction"
  }
}
EOF
    fi
fi

echo "✅ Prerequisites check passed"

# Build images
echo ""
echo "2️⃣  BUILDING DOCKER IMAGES"
echo "=========================="
./scripts/build-images.sh

# Deploy to Kubernetes
echo ""
echo "3️⃣  DEPLOYING TO KUBERNETES" 
echo "==========================="
./scripts/deploy-k8s.sh

# Upload models
echo ""
echo "4️⃣  UPLOADING SAMPLE MODELS"
echo "==========================="
./scripts/upload-models.sh

# Deploy sample ModelDeployments
echo ""
echo "5️⃣  DEPLOYING SAMPLE MODELS"
echo "==========================="
echo "📱 Deploying iris classifier..."
kubectl apply -f k8s/examples/iris-model.yaml

echo "📱 Deploying churn predictor..."
kubectl apply -f k8s/examples/churn-model.yaml

echo "⏳ Waiting for model deployments to be ready..."
sleep 10

# Wait for deployments to be ready
kubectl wait --for=condition=ready pod -l component=inference-server -n ml-platform --timeout=300s

# Test predictions
echo ""
echo "6️⃣  TESTING PREDICTIONS"
echo "======================"
./scripts/test-predictions.sh

# Final status
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "📊 Platform Status:"
kubectl get all -n ml-platform

echo ""
echo "🤖 Model Deployments:"
kubectl get modeldeployments -n ml-platform

echo ""
echo "🌐 Access Points:"
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    echo "   🔗 Model Registry API: http://$MINIKUBE_IP:30800"
    echo "   🔗 MinIO Console: http://$MINIKUBE_IP:30901 (admin/minioadmin)"
    echo "   🔗 API Documentation: http://$MINIKUBE_IP:30800/docs"
else
    echo "   🔗 Model Registry API: kubectl port-forward -n ml-platform svc/model-registry-service 8000:8000"
    echo "   🔗 MinIO Console: kubectl port-forward -n ml-platform svc/minio-console-external 9001:9001"
fi

echo ""
echo "🎯 What you can do now:"
echo "   📊 Monitor: kubectl get modeldeployments -n ml-platform -w"
echo "   📈 Scale: kubectl patch modeldeployment iris-classifier -n ml-platform --type='merge' -p='{\"spec\":{\"replicas\":5}}'"
echo "   🔄 Update: kubectl patch modeldeployment iris-classifier -n ml-platform --type='merge' -p='{\"spec\":{\"modelVersion\":2}}'"
echo "   📝 Logs: kubectl logs -n ml-platform -l app=ml-operator -f"
echo "   🧹 Cleanup: ./scripts/cleanup.sh"

echo ""
echo "✨ Your ML Platform is ready for production!"