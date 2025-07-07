#!/bin/bash

# Test predictions from deployed models

set -e

echo "🧪 Testing predictions from deployed models..."

# Check if models are deployed
echo "📊 Checking deployed models..."
kubectl get modeldeployments -n ml-platform

echo ""
echo "📋 Model deployment status:"
for model in $(kubectl get modeldeployments -n ml-platform -o jsonpath='{.items[*].metadata.name}'); do
    echo "   🤖 $model:"
    kubectl get modeldeployment $model -n ml-platform -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown"
    echo ""
done

# Wait for deployments to be ready
echo "⏳ Waiting for model deployments to be ready..."
kubectl wait --for=condition=ready pod -l component=inference-server -n ml-platform --timeout=300s

echo ""
echo "🌐 Available inference services:"
kubectl get services -n ml-platform -l component=inference-server

# Test Iris Classifier
echo ""
echo "🌸 Testing Iris Classifier..."

# Port forward to iris classifier service
IRIS_SERVICE=$(kubectl get service -n ml-platform -l model-name=iris-classifier -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ ! -z "$IRIS_SERVICE" ]; then
    echo "   🔗 Port-forwarding to $IRIS_SERVICE..."
    kubectl port-forward -n ml-platform svc/$IRIS_SERVICE 8001:8001 &
    IRIS_PF_PID=$!
    
    # Wait for port-forward
    sleep 3
    
    # Test health endpoint
    echo "   🩺 Health check:"
    curl -s http://localhost:8001/health | python3 -m json.tool
    
    echo ""
    echo "   🔮 Making prediction (sample iris flower):"
    curl -X POST http://localhost:8001/predict \
        -H "Content-Type: application/json" \
        -d '{
            "features": [[5.1, 3.5, 1.4, 0.2]],
            "return_probabilities": true
        }' | python3 -m json.tool
    
    # Kill port-forward
    kill $IRIS_PF_PID 2>/dev/null || true
    sleep 1
else
    echo "   ⚠️  Iris classifier service not found"
fi

# Test Churn Predictor
echo ""
echo "💼 Testing Churn Predictor..."

CHURN_SERVICE=$(kubectl get service -n ml-platform -l model-name=churn-predictor -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ ! -z "$CHURN_SERVICE" ]; then
    echo "   🔗 Port-forwarding to $CHURN_SERVICE..."
    kubectl port-forward -n ml-platform svc/$CHURN_SERVICE 8002:8001 &
    CHURN_PF_PID=$!
    
    # Wait for port-forward
    sleep 3
    
    # Test health endpoint
    echo "   🩺 Health check:"
    curl -s http://localhost:8002/health | python3 -m json.tool
    
    echo ""
    echo "   🔮 Making prediction (sample customer):"
    curl -X POST http://localhost:8002/predict \
        -H "Content-Type: application/json" \
        -d '{
            "features": [[45, 80.5, 24, 2]],
            "return_probabilities": true
        }' | python3 -m json.tool
    
    # Kill port-forward
    kill $CHURN_PF_PID 2>/dev/null || true
    sleep 1
else
    echo "   ⚠️  Churn predictor service not found"
fi

echo ""
echo "📊 Model metrics:"
echo "   📈 Checking model deployment metrics..."

for deployment in $(kubectl get modeldeployments -n ml-platform -o jsonpath='{.items[*].metadata.name}'); do
    echo ""
    echo "   🤖 $deployment status:"
    kubectl describe modeldeployment $deployment -n ml-platform | grep -A 10 "Status:"
done

echo ""
echo "🎯 Scaling test:"
echo "   📈 Scaling iris-classifier to 3 replicas..."
kubectl patch modeldeployment iris-classifier -n ml-platform --type='merge' -p='{"spec":{"replicas":3}}'

echo "   ⏳ Waiting for scale operation..."
sleep 5

echo "   📊 Current replica status:"
kubectl get pods -n ml-platform -l model-name=iris-classifier

echo ""
echo "✅ Prediction testing completed!"
echo ""
echo "🔍 Useful commands:"
echo "   📊 Watch deployments: kubectl get modeldeployments -n ml-platform -w"
echo "   📝 View logs: kubectl logs -n ml-platform -l app=ml-operator"
echo "   🔧 Debug pod: kubectl describe pod <pod-name> -n ml-platform"
echo "   📈 Scale model: kubectl patch modeldeployment <name> -n ml-platform --type='merge' -p='{\"spec\":{\"replicas\":5}}'"