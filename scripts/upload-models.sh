#!/bin/bash

# Upload sample models to Kubernetes-deployed Model Registry

set -e

echo "📤 Uploading sample models to Kubernetes Model Registry..."

# Determine API endpoint
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    API_URL="http://$MINIKUBE_IP:30800"
    echo "🔗 Using minikube endpoint: $API_URL"
else
    echo "🔗 Using port-forward to access API..."
    # Start port-forward in background
    kubectl port-forward -n ml-platform svc/model-registry-service 8000:8000 &
    PORT_FORWARD_PID=$!
    API_URL="http://localhost:8000"
    
    # Wait for port-forward to be ready
    sleep 3
    
    # Cleanup function
    cleanup() {
        if [ ! -z "$PORT_FORWARD_PID" ]; then
            kill $PORT_FORWARD_PID 2>/dev/null || true
        fi
    }
    trap cleanup EXIT
fi

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo "   Attempt $i/30 - waiting..."
    sleep 2
done

# Check if API is responding
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ API is not responding. Check deployment status:"
    kubectl get pods -n ml-platform
    exit 1
fi

# Load metadata
if [ ! -f "examples/models_metadata.json" ]; then
    echo "❌ Model metadata not found. Run examples/create_sample_models.py first"
    exit 1
fi

echo ""
echo "📋 Available models:"
ls -la examples/models/

echo ""
echo "📤 Uploading models..."

# Upload Iris Classifier v1
if [ -f "examples/models/iris_classifier_v1.pkl" ]; then
    echo "   🌸 Uploading Iris Classifier v1..."
    curl -X POST "$API_URL/models/iris-classifier/versions" \
        -F "file=@examples/models/iris_classifier_v1.pkl" \
        -F "description=Iris classification model for Kubernetes deployment" \
        -F "metadata={\"framework\":\"scikit-learn\",\"accuracy\":1.0,\"environment\":\"kubernetes\"}"
    echo ""
fi

# Upload Iris Classifier v2
if [ -f "examples/models/iris_classifier_v2.pkl" ]; then
    echo "   🌸 Uploading Iris Classifier v2..."
    curl -X POST "$API_URL/models/iris-classifier/versions" \
        -F "file=@examples/models/iris_classifier_v2.pkl" \
        -F "description=Improved iris classification model" \
        -F "metadata={\"framework\":\"scikit-learn\",\"accuracy\":1.0,\"improvements\":\"regularization\",\"environment\":\"kubernetes\"}"
    echo ""
fi

# Upload Churn Predictor
if [ -f "examples/models/churn_predictor_v1.pkl" ]; then
    echo "   💼 Uploading Churn Predictor v1..."
    curl -X POST "$API_URL/models/churn-predictor/versions" \
        -F "file=@examples/models/churn_predictor_v1.pkl" \
        -F "description=Customer churn prediction model" \
        -F "metadata={\"framework\":\"scikit-learn\",\"accuracy\":0.95,\"use_case\":\"churn_prediction\",\"environment\":\"kubernetes\"}"
    echo ""
fi

echo ""
echo "📊 Verifying uploads..."
echo "   📋 Available models:"
curl -s "$API_URL/models" | python3 -m json.tool

echo ""
echo "   🔢 Iris classifier versions:"
curl -s "$API_URL/models/iris-classifier/versions" | python3 -m json.tool

echo ""
echo "✅ Model upload completed successfully!"
echo ""
echo "💡 Next steps:"
echo "   1. Deploy models: kubectl apply -f k8s/examples/"
echo "   2. Check deployments: kubectl get modeldeployments -n ml-platform"
echo "   3. Test predictions: ./scripts/test-predictions.sh"