#!/usr/bin/env python3
"""
ML Registry Demo Script
Demonstrates real-world ML model lifecycle management
"""

import joblib
import numpy as np
import requests
import json
import os
from datetime import datetime

def demo_ml_lifecycle():
    """Demonstrate complete ML model lifecycle"""
    
    print("🎭 ML MODEL REGISTRY - LIVE DEMO")
    print("=" * 50)
    print("Scenario: E-commerce Recommendation System")
    print("Business Need: Deploy and manage product recommendation models")
    print()
    
    # Load test data
    if os.path.exists("examples/sample_data/iris_test_data.pkl"):
        test_data = joblib.load("examples/sample_data/iris_test_data.pkl")
        X_test = test_data['X_test']
        print("📊 Test data loaded successfully")
    else:
        print("⚠️  Test data not found. Run create_sample_models.py first")
        return
    
    print("\n" + "="*50)
    print("SCENARIO 1: Initial Model Deployment")
    print("="*50)
    
    print("""
🏢 DataCorp Inc. - ML Engineering Team
📅 Monday Morning: Deploy new product recommendation model

Team Lead: "We need to deploy our iris classification model for 
           the flower identification feature on our gardening app."
           
ML Engineer: "I'll upload it to our model registry..."
""")
    
    # Simulate model upload
    print("\n🔄 Uploading iris-classifier v1...")
    upload_response = requests.post(
        "http://localhost:8000/models/iris-classifier/versions",
        files={'file': open('examples/models/iris_classifier_v1.pkl', 'rb')},
        data={
            'description': 'Production iris classifier for gardening app',
            'metadata': json.dumps({
                'environment': 'production',
                'accuracy': 0.967,
                'deployment_date': datetime.now().isoformat(),
                'responsible_team': 'ML Engineering'
            })
        }
    )
    
    if upload_response.status_code == 200:
        print("✅ Model deployed successfully!")
        model_info = upload_response.json()
        print(f"   🔢 Version: {model_info['version']}")
        print(f"   📊 Size: {model_info['file_size']:,} bytes")
    else:
        print("❌ Upload failed")
        return
    
    print("\n📱 App Team: Testing the new model...")
    
    # Download and test model
    download_response = requests.get("http://localhost:8000/models/iris-classifier/versions/1")
    if download_response.status_code == 200:
        with open("temp_model.pkl", "wb") as f:
            f.write(download_response.content)
        
        # Load and test model
        model = joblib.load("temp_model.pkl")
        test_sample = X_test[0:1]  # One flower sample
        prediction = model.predict(test_sample)[0]
        confidence = model.predict_proba(test_sample)[0].max()
        
        flower_names = ['Setosa', 'Versicolor', 'Virginica']
        print(f"🌸 Prediction: {flower_names[prediction]} (confidence: {confidence:.1%})")
        print("✅ Model working perfectly in production!")
        
        os.remove("temp_model.pkl")
    
    print("\n" + "="*50)
    print("SCENARIO 2: Model Performance Issue")
    print("="*50)
    
    print("""
📅 Wednesday Afternoon: Performance monitoring alert

🚨 Monitoring Alert: Model accuracy dropped to 85% on new data
📞 Product Manager: "Users are complaining about wrong flower predictions!"
🔬 Data Scientist: "I've improved the model. Let me deploy v2..."
""")
    
    # Upload improved model
    print("\n🔄 Uploading improved iris-classifier v2...")
    upload_v2_response = requests.post(
        "http://localhost:8000/models/iris-classifier/versions",
        files={'file': open('examples/models/iris_classifier_v2.pkl', 'rb')},
        data={
            'description': 'Improved iris classifier with better regularization',
            'metadata': json.dumps({
                'environment': 'production',
                'accuracy': 0.975,
                'improvements': 'Reduced overfitting, better generalization',
                'deployment_date': datetime.now().isoformat(),
                'responsible_team': 'ML Engineering'
            })
        }
    )
    
    if upload_v2_response.status_code == 200:
        print("✅ Model v2 deployed successfully!")
        model_v2_info = upload_v2_response.json()
        print(f"   🔢 Version: {model_v2_info['version']}")
        print(f"   📈 Accuracy improved: 96.7% → 97.5%")
    
    print("\n📊 Comparing model versions...")
    versions_response = requests.get("http://localhost:8000/models/iris-classifier/versions")
    if versions_response.status_code == 200:
        versions = versions_response.json()
        print(f"   📚 Total versions available: {len(versions)}")
        for v in versions:
            print(f"   🔢 Version {v['version']}: {v['filename']} ({v['file_size']:,} bytes)")
    
    print("\n" + "="*50)
    print("SCENARIO 3: Emergency Rollback")
    print("="*50)
    
    print("""
📅 Friday Evening: Critical bug discovered

🚨 URGENT: v2 model has a bug causing app crashes on edge cases!
👨‍💻 On-call Engineer: "We need to rollback immediately!""")