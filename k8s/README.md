# ML Platform - Kubernetes Deployment

This directory contains Kubernetes manifests and deployment scripts for the ML Model Serving Platform.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   ML Operator   │    │ Model Registry  │    │  PostgreSQL  │ │
│  │                 │    │      API        │    │   Database   │ │
│  │  - Watches CRDs │◄──►│  - Model CRUD   │◄──►│  - Metadata  │ │
│  │  - Creates Pods │    │  - Version Mgmt │    │  - Versions  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                             │
│           ▼                       │              ┌──────────────┐ │
│  ┌─────────────────┐              └─────────────►│    MinIO     │ │
│  │ Inference Pods  │                             │Object Storage│ │
│  │                 │                             │ - Model Files│ │
│  │ iris-v1-xxx     │◄────────────────────────────┤ - Artifacts  │ │
│  │ iris-v2-yyy     │                             └──────────────┘ │
│  │ churn-v1-zzz    │                                              │
│  └─────────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Components

### Core Infrastructure
- **namespace.yaml** - ML platform namespace and configuration
- **postgresql.yaml** - PostgreSQL database with persistent storage
- **minio.yaml** - MinIO object storage for model files

### Application Services  
- **model-registry.yaml** - Model Registry API deployment
- **model-deployment-crd.yaml** - Custom Resource Definition for ModelDeployments

### Operator & RBAC
- **rbac.yaml** - Service accounts and permissions for the operator
- **operator.yaml** - ML Operator deployment that manages ModelDeployments

### Examples
- **examples/iris-model.yaml** - Sample iris classifier deployment
- **examples/churn-model.yaml** - Sample churn predictor deployment

## 🚀 Quick Start

### Prerequisites

```bash
# Kubernetes cluster (minikube, kind, or cloud provider)
kubectl cluster-info

# Docker for building images  
docker --version

# Make scripts executable
chmod +x scripts/*.sh
```

### Deployment Steps

```bash
# 1. Build Docker images
./scripts/build-images.sh

# 2. Deploy to Kubernetes
./scripts/deploy-k8s.sh

# 3. Upload sample models
./scripts/upload-models.sh

# 4. Deploy sample models
kubectl apply -f k8s/examples/

# 5. Test predictions
./scripts/test-predictions.sh
```

## 🔧 ModelDeployment Custom Resource

The `ModelDeployment` CRD allows you to declaratively deploy ML models:

```yaml
apiVersion: ml.example.com/v1
kind: ModelDeployment
metadata:
  name: my-model
  namespace: ml-platform
spec:
  modelName: iris-classifier      # Model name in registry
  modelVersion: 2                 # Version to deploy
  replicas: 3                     # Number of pods
  environment: production         # Environment tag
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi" 
      cpu: "1000m"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
```

## 🎯 Key Features

### Automatic Model Deployment
- **Declarative**: Describe desired state, operator handles implementation
- **Version Management**: Deploy specific model versions
- **Auto-scaling**: HPA based on CPU utilization
- **Health Checks**: Built-in liveness and readiness probes

### Model Registry Integration
- **Dynamic Loading**: Models downloaded from registry at startup
- **Version Control**: Track and manage model versions
- **Metadata Storage**: Rich model information and metrics

### Production Ready
- **RBAC Security**: Proper service accounts and permissions
- **Resource Management**: CPU/memory requests and limits
- **Persistent Storage**: Data survives pod restarts
- **Monitoring**: Health endpoints and metrics

## 📊 Management Commands

### View Deployments
```bash
# List all model deployments
kubectl get modeldeployments -n ml-platform

# Detailed view of specific deployment
kubectl describe modeldeployment iris-classifier -n ml-platform

# Watch deployment status
kubectl get modeldeployments -n ml-platform -w
```

### Scale Models
```bash
# Scale to 5 replicas
kubectl patch modeldeployment iris-classifier -n ml-platform \
  --type='merge' -p='{"spec":{"replicas":5}}'

# Enable autoscaling
kubectl patch modeldeployment iris-classifier -n ml-platform \
  --type='merge' -p='{"spec":{"autoscaling":{"enabled":true,"maxReplicas":10}}}'
```

### Update Model Version
```bash
# Deploy new model version
kubectl patch modeldeployment iris-classifier -n ml-platform \
  --type='merge' -p='{"spec":{"modelVersion":2}}'
```

### View Logs
```bash
# Operator logs
kubectl logs -n ml-platform -l app=ml-operator -f

# Model inference logs
kubectl logs -n ml-platform -l component=inference-server -f

# Specific model logs
kubectl logs -n ml-platform -l model-name=iris-classifier
```

## 🌐 Access Services

### With Minikube
```bash
minikube ip  # Get cluster IP

# Access points:
# Model Registry: http://<minikube-ip>:30800
# MinIO Console: http://<minikube-ip>:30901
```

### With Port Forwarding
```bash
# Model Registry API
kubectl port-forward -n ml-platform svc/model-registry-service 8000:8000

# MinIO Console
kubectl port-forward -n ml-platform svc/minio-console-external 9001:9001

# Inference Service (example)
kubectl port-forward -n ml-platform svc/iris-classifier-service 8001:8001
```

## 🧪 Testing

### Health Checks
```bash
# Registry API health
curl http://localhost:8000/health

# Model inference health  
curl http://localhost:8001/health

# Model metrics
curl http://localhost:8001/metrics
```

### Make Predictions
```bash
# Iris classification
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [[5.1, 3.5, 1.4, 0.2]],
    "return_probabilities": true
  }'

# Churn prediction  
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [[45, 80.5, 24, 2]],
    "return_probabilities": true
  }'
```

## 🛠️ Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n ml-platform
kubectl logs <pod-name> -n ml-platform
```

**Images not found:**
```bash
# Make sure images are built
docker images | grep ml-platform

# For minikube, ensure using minikube's Docker
eval $(minikube docker-env)
./scripts/build-images.sh
```

**Operator not working:**
```bash
# Check operator logs
kubectl logs -n ml-platform -l app=ml-operator

# Verify RBAC permissions
kubectl auth can-i create deployments --as=system:serviceaccount:ml-platform:ml-operator
```

**Models not loading:**
```bash
# Check registry connectivity
kubectl exec -n ml-platform <inference-pod> -- curl http://model-registry-service:8000/health

# Verify model exists in registry
curl http://localhost:8000/models/iris-classifier/versions
```

## 🗑️ Cleanup

```bash
# Remove all ML Platform resources
./scripts/cleanup.sh

# Remove Docker images
docker rmi ml-platform/api:latest ml-platform/inference-server:latest ml-platform/operator:latest
```

## 📚 Next Steps

1. **Production Deployment**: 
   - Use proper image registry
   - Configure ingress/load balancers  
   - Set up monitoring (Prometheus/Grafana)

2. **Security Hardening**:
   - Network policies
   - Pod security policies
   - Secrets management

3. **CI/CD Integration**:
   - Automated model training
   - Model validation pipelines
   - GitOps deployment workflows