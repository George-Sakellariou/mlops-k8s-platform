#!/bin/bash

# Deploy ML Platform to Kubernetes

set -e

echo "🚀 Deploying ML Platform to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "💡 Make sure your cluster is running and kubectl is configured"
    exit 1
fi

echo "✅ Kubernetes cluster is accessible"

# Deploy in order
echo ""
echo "1️⃣  Creating namespace and configuration..."
kubectl apply -f k8s/namespace.yaml

echo ""
echo "2️⃣  Deploying PostgreSQL database..."
kubectl apply -f k8s/postgresql.yaml

echo ""
echo "3️⃣  Deploying MinIO object storage..."
kubectl apply -f k8s/minio.yaml

echo ""
echo "4️⃣  Installing Custom Resource Definition..."
kubectl apply -f k8s/model-deployment-crd.yaml

echo ""
echo "5️⃣  Setting up RBAC for operator..."
kubectl apply -f k8s/rbac.yaml

echo ""
echo "6️⃣  Deploying ML Operator..."
kubectl apply -f k8s/operator.yaml

echo ""
echo "7️⃣  Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n ml-platform --timeout=300s
kubectl wait --for=condition=ready pod -l app=minio -n ml-platform --timeout=300s

echo ""
echo "8️⃣  Deploying Model Registry API..."
kubectl apply -f k8s/model-registry.yaml

echo ""
echo "9️⃣  Waiting for API to be ready..."
kubectl wait --for=condition=ready pod -l app=model-registry-api -n ml-platform --timeout=300s

echo ""
echo "🔟 Waiting for operator to be ready..."
kubectl wait --for=condition=ready pod -l app=ml-operator -n ml-platform --timeout=300s

echo ""
echo "✅ ML Platform deployed successfully!"

echo ""
echo "📊 Deployment Status:"
kubectl get pods -n ml-platform

echo ""
echo "🌐 Access Points:"
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    echo "   🔗 Model Registry API: http://$MINIKUBE_IP:30800"
    echo "   🔗 MinIO Console: http://$MINIKUBE_IP:30901"
else
    echo "   🔗 Model Registry API: kubectl port-forward -n ml-platform svc/model-registry-service 8000:8000"
    echo "   🔗 MinIO Console: kubectl port-forward -n ml-platform svc/minio-console-external 9001:9001"
fi

echo ""
echo "🎯 Next Steps:"
echo "   1. Upload models to registry:"
echo "      ./scripts/upload-models.sh"
echo ""
echo "   2. Deploy sample models:"
echo "      kubectl apply -f k8s/examples/"
echo ""
echo "   3. Test model predictions:"
echo "      ./scripts/test-predictions.sh"
echo ""
echo "   4. Monitor deployments:"
echo "      kubectl get modeldeployments -n ml-platform"
echo "      kubectl describe modeldeployment iris-classifier -n ml-platform"