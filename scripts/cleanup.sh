#!/bin/bash

# Cleanup ML Platform deployment from Kubernetes

set -e

echo "🧹 Cleaning up ML Platform from Kubernetes..."

# Delete ModelDeployments first (let operator handle cleanup)
echo "1️⃣  Deleting ModelDeployments..."
kubectl delete -f k8s/examples/ --ignore-not-found=true

echo "2️⃣  Waiting for operator to cleanup resources..."
sleep 10

# Delete operator
echo "3️⃣  Deleting ML Operator..."
kubectl delete -f k8s/operator.yaml --ignore-not-found=true

# Delete RBAC
echo "4️⃣  Deleting RBAC configuration..."
kubectl delete -f k8s/rbac.yaml --ignore-not-found=true

# Delete CRD
echo "5️⃣  Deleting Custom Resource Definition..."
kubectl delete -f k8s/model-deployment-crd.yaml --ignore-not-found=true

# Delete applications
echo "6️⃣  Deleting Model Registry API..."
kubectl delete -f k8s/model-registry.yaml --ignore-not-found=true

echo "7️⃣  Deleting MinIO..."
kubectl delete -f k8s/minio.yaml --ignore-not-found=true

echo "8️⃣  Deleting PostgreSQL..."
kubectl delete -f k8s/postgresql.yaml --ignore-not-found=true

# Delete namespace (this will cleanup any remaining resources)
echo "9️⃣  Deleting namespace..."
kubectl delete -f k8s/namespace.yaml --ignore-not-found=true

echo ""
echo "⏳ Waiting for cleanup to complete..."
kubectl wait --for=delete namespace/ml-platform --timeout=300s

echo ""
echo "✅ ML Platform cleanup completed!"
echo ""
echo "🗑️  To also remove Docker images:"
echo "   docker rmi ml-platform/api:latest ml-platform/inference-server:latest ml-platform/operator:latest"