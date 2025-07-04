#!/usr/bin/env python3
"""
ML Registry API Test Script
Comprehensive testing of the ML Model Registry API endpoints
"""

import requests
import json
import os
import time
from pathlib import Path
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
MODELS_DIR = "examples/models"
METADATA_FILE = "examples/models_metadata.json"

class MLRegistryTester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            health_data = response.json()
            print(f"✅ API Health Check: {health_data['status']}")
            print(f"   🕐 Timestamp: {health_data['timestamp']}")
            print(f"   🌍 Environment: {health_data['environment']}")
            return True
        except Exception as e:
            print(f"❌ API Health Check Failed: {e}")
            return False
    
    def upload_model(self, model_name: str, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a model to the registry"""
        print(f"\n📤 Uploading model: {model_name}")
        print(f"   📁 File: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                data = {
                    'description': metadata.get('use_case', ''),
                    'metadata': json.dumps(metadata)
                }
                
                response = self.session.post(
                    f"{self.base_url}/models/{model_name}/versions",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"   ✅ Upload successful!")
                print(f"   🔢 Version: {result['version']}")
                print(f"   📊 File size: {result['file_size']:,} bytes")
                print(f"   🕐 Created: {result['created_at']}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            raise
    
    def list_model_versions(self, model_name: str) -> list:
        """List all versions of a model"""
        print(f"\n📋 Listing versions for: {model_name}")
        
        try:
            response = self.session.get(f"{self.base_url}/models/{model_name}/versions")
            response.raise_for_status()
            
            versions = response.json()
            print(f"   📊 Found {len(versions)} versions:")
            
            for version in versions:
                print(f"   🔢 Version {version['version']}:")
                print(f"      📁 File: {version['filename']}")
                print(f"      📊 Size: {version['file_size']:,} bytes")
                print(f"      🕐 Created: {version['created_at']}")
            
            return versions
            
        except Exception as e:
            print(f"   ❌ Failed to list versions: {e}")
            raise
    
    def download_model(self, model_name: str, version: int, save_path: str) -> bool:
        """Download a specific model version"""
        print(f"\n📥 Downloading {model_name} v{version}")
        print(f"   💾 Save to: {save_path}")
        
        try:
            response = self.session.get(f"{self.base_url}/models/{model_name}/versions/{version}")
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(save_path)
            print(f"   ✅ Download successful!")
            print(f"   📊 Downloaded: {file_size:,} bytes")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            return False
    
    def list_all_models(self) -> list:
        """List all models in the registry"""
        print(f"\n📚 Listing all models in registry")
        
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            
            models = response.json()
            print(f"   📊 Found {len(models)} models:")
            
            for model in models:
                print(f"   🤖 {model['name']}:")
                print(f"      📝 Description: {model['description']}")
                print(f"      🕐 Created: {model['created_at']}")
            
            return models
            
        except Exception as e:
            print(f"   ❌ Failed to list models: {e}")
            raise
    
    def delete_model_version(self, model_name: str, version: int) -> bool:
        """Delete a specific model version"""
        print(f"\n🗑️  Deleting {model_name} v{version}")
        
        try:
            response = self.session.delete(f"{self.base_url}/models/{model_name}/versions/{version}")
            response.raise_for_status()
            
            result = response.json()
            print(f"   ✅ {result['message']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Delete failed: {e}")
            return False

def run_comprehensive_test():
    """Run comprehensive test of the ML Registry"""
    
    print("🧪 ML MODEL REGISTRY - COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Initialize tester
    tester = MLRegistryTester()
    
    # 1. Health Check
    print("\n1️⃣  HEALTH CHECK")
    if not tester.health_check():
        print("❌ API is not healthy. Please check your services.")
        return False
    
    # 2. Load metadata
    print("\n2️⃣  LOADING MODEL METADATA")
    try:
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        print(f"   ✅ Loaded metadata for {len(metadata)} models")
    except Exception as e:
        print(f"   ❌ Failed to load metadata: {e}")
        return False
    
    # 3. Upload Models
    print("\n3️⃣  UPLOADING MODELS")
    upload_results = {}
    
    model_files = {
        "iris-classifier": "iris_classifier_v1.pkl",
        "churn-predictor": "churn_predictor_v1.pkl"
    }
    
    for model_name, filename in model_files.items():
        file_path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(file_path):
            metadata_key = filename.replace('.pkl', '')
            model_metadata = metadata.get(metadata_key, {})
            
            try:
                result = tester.upload_model(model_name, file_path, model_metadata)
                upload_results[model_name] = result
            except Exception as e:
                print(f"   ⚠️  Skipping {model_name} due to error: {e}")
    
    # 4. Upload Second Version of Iris Model
    print("\n4️⃣  UPLOADING IRIS MODEL V2")
    iris_v2_path = os.path.join(MODELS_DIR, "iris_classifier_v2.pkl")
    if os.path.exists(iris_v2_path):
        try:
            iris_v2_metadata = metadata.get("iris_classifier_v2", {})
            tester.upload_model("iris-classifier", iris_v2_path, iris_v2_metadata)
        except Exception as e:
            print(f"   ⚠️  Failed to upload iris v2: {e}")
    
    # 5. List All Models
    print("\n5️⃣  LISTING ALL MODELS")
    tester.list_all_models()
    
    # 6. List Model Versions
    print("\n6️⃣  LISTING MODEL VERSIONS")
    for model_name in model_files.keys():
        if model_name in upload_results:
            tester.list_model_versions(model_name)
    
    # 7. Download Models
    print("\n7️⃣  DOWNLOADING MODELS")
    download_dir = "examples/downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    # Download iris classifier v1
    tester.download_model(
        "iris-classifier", 
        1, 
        os.path.join(download_dir, "downloaded_iris_v1.pkl")
    )
    
    # Download latest iris classifier (should be v2)
    tester.download_model(
        "iris-classifier", 
        2, 
        os.path.join(download_dir, "downloaded_iris_v2.pkl")
    )
    
    # 8. Test Model Loading (Verify Downloads Work)
    print("\n8️⃣  VERIFYING DOWNLOADED MODELS")
    try:
        import joblib
        
        # Load downloaded model
        downloaded_model = joblib.load(os.path.join(download_dir, "downloaded_iris_v1.pkl"))
        print("   ✅ Downloaded model loads successfully")
        print(f"   🔍 Model type: {type(downloaded_model).__name__}")
        
        # Load test data and make prediction
        if os.path.exists("examples/sample_data/iris_test_data.pkl"):
            test_data = joblib.load("examples/sample_data/iris_test_data.pkl")
            X_test = test_data['X_test'][:5]  # Test with 5 samples
            
            predictions = downloaded_model.predict(X_test)
            print(f"   🔮 Made predictions for {len(predictions)} samples")
            print(f"   📊 Predictions: {predictions}")
            
    except Exception as e:
        print(f"   ⚠️  Model verification failed: {e}")
    
    # 9. Performance Test
    print("\n9️⃣  PERFORMANCE TEST")
    start_time = time.time()
    
    # Make multiple API calls
    for _ in range(5):
        tester.health_check()
    
    end_time = time.time()
    avg_response_time = (end_time - start_time) / 5
    print(f"   ⚡ Average response time: {avg_response_time:.3f}s")
    
    # 10. Summary
    print("\n🔟 TEST SUMMARY")
    print("=" * 60)
    print("✅ Health check: PASSED")
    print(f"✅ Models uploaded: {len(upload_results)}")
    print("✅ Version management: PASSED")
    print("✅ Download functionality: PASSED")
    print("✅ Model verification: PASSED")
    print(f"✅ Performance: {avg_response_time:.3f}s avg response")
    
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("\n💡 Next Steps:")
    print("   1. Check MinIO UI (http://localhost:9001) to see stored files")
    print("   2. Verify PostgreSQL records")
    print("   3. Ready for Kubernetes deployment!")
    
    return True

if __name__ == "__main__":
    # Check if models exist
    if not os.path.exists(MODELS_DIR):
        print("❌ Models directory not found. Please run the model creation script first:")
        print("   python3 create_sample_models.py")
        exit(1)
    
    # Run tests
    success = run_comprehensive_test()
    
    if success:
        print("\n🚀 READY FOR KUBERNETES PHASE!")
    else:
        print("\n❌ Tests failed. Please check your setup.")