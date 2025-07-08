# MLOps Kubernetes Platform

A production-ready ML model serving platform demonstrating advanced Python AI, Kubernetes, and DevOps skills. This platform provides automated model deployment, version management, and scalable inference services using cloud-native technologies.

## 🚀 Features

- **🤖 Model Registry API**: FastAPI-based service for ML model versioning and storage
- **⚙️ Inference Server**: Scalable prediction service with auto-scaling capabilities  
- **☸️ Kubernetes Operator**: Custom operator for automated model deployments via CRDs
- **📊 Model Management**: Complete lifecycle management with rollback capabilities
- **🔄 Auto-scaling**: Horizontal Pod Autoscaler integration for production workloads
- **💾 Persistent Storage**: PostgreSQL + MinIO for metadata and model artifacts
- **🔍 Monitoring**: Built-in health checks, metrics, and observability

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

### Core Services
- **Model Registry API** (`api/`): FastAPI service for model CRUD operations
- **Inference Server** (`inference-server/`): Scalable prediction service  
- **ML Operator** (`operator/`): Kubernetes operator using kopf framework
- **PostgreSQL**: Model metadata and version tracking
- **MinIO**: Binary model file storage

### Custom Resources
- **ModelDeployment CRD**: Declarative model deployment specification
- **Automatic Resource Management**: Deployments, Services, HPA creation
- **Status Tracking**: Real-time deployment status and health monitoring

## 🚀 Quick Start

### Prerequisites

```bash
# Required tools
kubectl version --client    # Kubernetes CLI
docker --version           # Container runtime
python3 --version          # Python 3.10+

# Kubernetes cluster (choose one)
minikube start             # Local development
kind create cluster        # Alternative local option
# Or use cloud provider (GKE, EKS, AKS)
```

### One-Command Deployment

```bash
# Complete platform deployment
chmod +x deploy-complete.sh
./deploy-complete.sh
```

This script will:
1. ✅ Verify prerequisites
2. 🐳 Build Docker images
3. ☸️ Deploy to Kubernetes  
4. 📤 Upload sample models
5. 🤖 Deploy ModelDeployments
6. 🧪 Test predictions

### Manual Deployment

```bash
# 1. Create sample models
python examples/create_sample_models.py

# 2. Build Docker images
./scripts/build-images.sh

# 3. Deploy infrastructure
./scripts/deploy-k8s.sh

# 4. Upload models to registry
./scripts/upload-models.sh

# 5. Deploy sample models
kubectl apply -f k8s/examples/

# 6. Test predictions
./scripts/test-predictions.sh
```

## 🎯 Usage Examples

### Deploy a Model

Create a `ModelDeployment` to automatically deploy an ML model:

```yaml
apiVersion: ml.example.com/v1
kind: ModelDeployment
metadata:
  name: iris-classifier
  namespace: ml-platform
spec:
  modelName: iris-classifier      # Model in registry
  modelVersion: 2                 # Version to deploy
  replicas: 3                     # Initial replicas
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

### Make Predictions

```bash
# Iris classification
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [[5.1, 3.5, 1.4, 0.2]],
    "return_probabilities": true
  }'

# Response
{
  "predictions": [0],
  "probabilities": [[0.98, 0.01, 0.01]],
  "model_name": "iris-classifier",
  "model_version": 2,
  "prediction_time": "2025-07-08T10:30:00Z"
}
```

### Upload New Model Version

```bash
# Upload via API
curl -X POST http://localhost:8000/models/my-model/versions \
  -F "file=@model.pkl" \
  -F "description=Improved accuracy model" \
  -F "metadata={\"accuracy\":0.95,\"framework\":\"scikit-learn\"}"
```

### Scale Deployments

```bash
# Scale manually
kubectl patch modeldeployment iris-classifier -n ml-platform \
  --type='merge' -p='{"spec":{"replicas":5}}'

# Update model version
kubectl patch modeldeployment iris-classifier -n ml-platform \
  --type='merge' -p='{"spec":{"modelVersion":3}}'

# Enable auto-scaling
kubectl patch modeldeployment iris-classifier -n ml-platform \
  --type='merge' -p='{"spec":{"autoscaling":{"enabled":true,"maxReplicas":10}}}'
```

## 📊 Management & Monitoring

### View Deployments
```bash
# List all model deployments
kubectl get modeldeployments -n ml-platform

# Detailed deployment info
kubectl describe modeldeployment iris-classifier -n ml-platform

# Watch deployment status
kubectl get modeldeployments -n ml-platform -w
```

### Health Checks & Metrics
```bash
# API health
curl http://localhost:8000/health

# Model inference health
curl http://localhost:8001/health

# Model metrics
curl http://localhost:8001/metrics

# Operator logs
kubectl logs -n ml-platform -l app=ml-operator -f
```

### Access Services
```bash
# With minikube
minikube ip  # Get cluster IP
# Model Registry: http://<minikube-ip>:30800
# MinIO Console: http://<minikube-ip>:30901

# With port-forwarding
kubectl port-forward -n ml-platform svc/model-registry-service 8000:8000
kubectl port-forward -n ml-platform svc/minio-console-external 9001:9001
```

## 🛠️ Development

### Project Structure

```
ml-serving-platform/
├── README.md
├── deploy-complete.sh          # One-command deployment
├── docker-compose.yml          # Local development
├── requirements.txt
├── .env                        # Environment configuration
├── api/                        # Model Registry API
│   ├── Dockerfile
│   ├── main.py                 # FastAPI application
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # Database configuration
│   ├── storage.py              # MinIO integration
│   ├── config.py               # Configuration management
│   └── requirements.txt
├── inference-server/           # ML Inference Service
│   ├── Dockerfile
│   ├── main.py                 # FastAPI inference server
│   └── requirements.txt
├── operator/                   # Kubernetes Operator
│   ├── Dockerfile
│   ├── main.py                 # Kopf-based operator
│   └── requirements.txt
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yaml
│   ├── postgresql.yaml
│   ├── minio.yaml
│   ├── model-registry.yaml
│   ├── model-deployment-crd.yaml
│   ├── operator.yaml
│   ├── rbac.yaml
│   └── examples/
│       ├── iris-model.yaml
│       └── churn-model.yaml
├── scripts/                    # Deployment scripts
│   ├── build-images.sh
│   ├── deploy-k8s.sh
│   ├── upload-models.sh
│   ├── test-predictions.sh
│   └── cleanup.sh
└── examples/                   # Sample models & tests
    ├── create_sample_models.py
    ├── test_api.py
    ├── demo.py
    └── models/
```

### Local Development

```bash
# Start local services
docker-compose up -d

# Activate virtual environment
python3 -m venv mlserv
source mlserv/bin/activate
pip install -r requirements.txt

# Run API locally
cd api
uvicorn main:app --reload --port 8000

# Test API
python ../examples/test_api.py
```

### Running Tests

```bash
# Create sample models
python examples/create_sample_models.py

# Test API endpoints
python examples/test_api.py

# Integration test with Kubernetes
./scripts/test-predictions.sh
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mlplatform
POSTGRES_DB=mlplatform
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MODEL_BUCKET=models

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Kubernetes Configuration

Key configurations in `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ml-platform-config
  namespace: ml-platform
data:
  POSTGRES_DB: "mlplatform"
  MINIO_ENDPOINT: "minio-service:9000"
  MODEL_BUCKET: "models"
  ENVIRONMENT: "kubernetes"
  LOG_LEVEL: "INFO"
```

## 🔒 Security & Production

### RBAC Configuration
- Service accounts with minimal required permissions
- ClusterRole for CRD and resource management
- Namespace-specific roles for enhanced security

### Resource Management
- CPU/Memory requests and limits on all components
- Liveness and readiness probes for health monitoring
- Persistent volumes for data durability

### Production Considerations
- Use external PostgreSQL and object storage
- Configure ingress controllers and TLS termination
- Implement proper secrets management
- Set up monitoring with Prometheus/Grafana
- Enable network policies for network segmentation

## 🧪 Testing Strategy

### Unit Tests
- API endpoint testing with pytest
- Model loading and inference validation
- Operator event handler testing

### Integration Tests  
- End-to-end workflow validation
- Kubernetes resource creation verification
- Cross-service communication testing

### Sample Models Included
- **Iris Classifier**: Multi-class flower classification
- **Churn Predictor**: Binary customer churn prediction
- Both with multiple versions for testing updates

## 🚨 Troubleshooting

### Common Issues

**Images not found:**
```bash
# For minikube, use minikube's Docker daemon
eval $(minikube docker-env)
./scripts/build-images.sh
```

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n ml-platform
kubectl logs <pod-name> -n ml-platform
```

**Operator not creating resources:**
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

# Verify model exists
curl http://localhost:8000/models/iris-classifier/versions
```

## 🗑️ Cleanup

```bash
# Remove all platform resources
./scripts/cleanup.sh

# Remove Docker images
docker rmi ml-platform/api:latest ml-platform/inference-server:latest ml-platform/operator:latest

# Reset minikube (if used)
minikube delete
```

**🚀 Ready to deploy ML models at scale? Start with `./deploy-complete.sh` and experience the future of MLOps!**