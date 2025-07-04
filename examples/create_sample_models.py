#!/usr/bin/env python3
"""
Sample ML Models Creation Script
Creates training data and models for testing the ML Registry Platform
"""

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris, make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from datetime import datetime

# Create examples directory
os.makedirs("examples", exist_ok=True)
os.makedirs("examples/models", exist_ok=True)
os.makedirs("examples/sample_data", exist_ok=True)

print("🤖 Creating Sample ML Models for Registry Testing")
print("=" * 60)

# 1. IRIS CLASSIFICATION MODEL
print("\n1. 🌸 Creating Iris Classification Model...")

# Load Iris dataset
iris = load_iris()
X_iris, y_iris = iris.data, iris.target

# Split the data
X_train_iris, X_test_iris, y_train_iris, y_test_iris = train_test_split(
    X_iris, y_iris, test_size=0.2, random_state=42
)

# Train Random Forest model
iris_model = RandomForestClassifier(n_estimators=100, random_state=42)
iris_model.fit(X_train_iris, y_train_iris)

# Evaluate
iris_predictions = iris_model.predict(X_test_iris)
iris_accuracy = accuracy_score(y_test_iris, iris_predictions)

print(f"   ✅ Iris Model Accuracy: {iris_accuracy:.3f}")
print(f"   📊 Feature names: {iris.feature_names}")
print(f"   🏷️  Target names: {iris.target_names}")

# Save model
iris_model_path = "examples/models/iris_classifier_v1.pkl"
joblib.dump(iris_model, iris_model_path)
print(f"   💾 Saved model to: {iris_model_path}")

# Save test data for later inference testing
iris_test_data = {
    'X_test': X_test_iris,
    'y_test': y_test_iris,
    'feature_names': iris.feature_names,
    'target_names': iris.target_names
}
joblib.dump(iris_test_data, "examples/sample_data/iris_test_data.pkl")

# 2. CUSTOMER CHURN PREDICTION MODEL
print("\n2. 💼 Creating Customer Churn Prediction Model...")

# Generate synthetic customer data
np.random.seed(42)
n_customers = 1000

# Features: age, monthly_charges, tenure_months, support_calls
X_churn, y_churn = make_classification(
    n_samples=n_customers,
    n_features=4,
    n_informative=3,
    n_redundant=1,
    n_clusters_per_class=1,
    random_state=42
)

# Make features more realistic
X_churn[:, 0] = np.clip(X_churn[:, 0] * 10 + 45, 18, 80)  # Age: 18-80
X_churn[:, 1] = np.clip(X_churn[:, 1] * 20 + 50, 20, 200)  # Monthly charges: $20-200
X_churn[:, 2] = np.clip(X_churn[:, 2] * 5 + 12, 1, 60)     # Tenure: 1-60 months
X_churn[:, 3] = np.clip(X_churn[:, 3] * 2 + 3, 0, 10)      # Support calls: 0-10

feature_names = ['age', 'monthly_charges', 'tenure_months', 'support_calls']

# Create DataFrame for better handling
churn_df = pd.DataFrame(X_churn, columns=feature_names)
churn_df['churn'] = y_churn

print(f"   📊 Generated {n_customers} customer records")
print(f"   🏷️  Churn rate: {y_churn.mean():.1%}")

# Split the data
X_train_churn, X_test_churn, y_train_churn, y_test_churn = train_test_split(
    X_churn, y_churn, test_size=0.2, random_state=42, stratify=y_churn
)

# Train Logistic Regression model
churn_model = LogisticRegression(random_state=42, max_iter=1000)
churn_model.fit(X_train_churn, y_train_churn)

# Evaluate
churn_predictions = churn_model.predict(X_test_churn)
churn_accuracy = accuracy_score(y_test_churn, churn_predictions)

print(f"   ✅ Churn Model Accuracy: {churn_accuracy:.3f}")

# Save model
churn_model_path = "examples/models/churn_predictor_v1.pkl"
joblib.dump(churn_model, churn_model_path)
print(f"   💾 Saved model to: {churn_model_path}")

# Save test data
churn_test_data = {
    'X_test': X_test_churn,
    'y_test': y_test_churn,
    'feature_names': feature_names,
    'sample_customer': X_test_churn[0]  # First test customer for demo
}
joblib.dump(churn_test_data, "examples/sample_data/churn_test_data.pkl")

# Save sample dataset
churn_df.to_csv("examples/sample_data/customer_churn_dataset.csv", index=False)

# 3. IMPROVED IRIS MODEL (Version 2)
print("\n3. 🌸 Creating Improved Iris Classification Model (v2)...")

# Train with different parameters for version 2
iris_model_v2 = RandomForestClassifier(
    n_estimators=200,  # More trees
    max_depth=5,       # Limit depth
    min_samples_split=5,
    random_state=42
)
iris_model_v2.fit(X_train_iris, y_train_iris)

# Evaluate
iris_v2_predictions = iris_model_v2.predict(X_test_iris)
iris_v2_accuracy = accuracy_score(y_test_iris, iris_v2_predictions)

print(f"   ✅ Iris Model v2 Accuracy: {iris_v2_accuracy:.3f}")
print(f"   📈 Improvement: {iris_v2_accuracy - iris_accuracy:+.3f}")

# Save model v2
iris_v2_model_path = "examples/models/iris_classifier_v2.pkl"
joblib.dump(iris_model_v2, iris_v2_model_path)
print(f"   💾 Saved model to: {iris_v2_model_path}")

# 4. MODEL METADATA CREATION
print("\n4. 📋 Creating Model Metadata...")

models_metadata = {
    "iris_classifier_v1": {
        "model_type": "RandomForestClassifier",
        "framework": "scikit-learn",
        "accuracy": iris_accuracy,
        "features": 4,
        "classes": 3,
        "training_samples": len(X_train_iris),
        "hyperparameters": {
            "n_estimators": 100,
            "random_state": 42
        },
        "created_date": datetime.now().isoformat(),
        "use_case": "Multi-class classification of iris flowers",
        "input_features": list(iris.feature_names),
        "output_classes": list(iris.target_names)
    },
    
    "iris_classifier_v2": {
        "model_type": "RandomForestClassifier", 
        "framework": "scikit-learn",
        "accuracy": iris_v2_accuracy,
        "features": 4,
        "classes": 3,
        "training_samples": len(X_train_iris),
        "hyperparameters": {
            "n_estimators": 200,
            "max_depth": 5,
            "min_samples_split": 5,
            "random_state": 42
        },
        "created_date": datetime.now().isoformat(),
        "use_case": "Improved iris classification with regularization",
        "improvements": "Reduced overfitting with depth limit",
        "input_features": list(iris.feature_names),
        "output_classes": list(iris.target_names)
    },
    
    "churn_predictor_v1": {
        "model_type": "LogisticRegression",
        "framework": "scikit-learn", 
        "accuracy": churn_accuracy,
        "features": 4,
        "classes": 2,
        "training_samples": len(X_train_churn),
        "hyperparameters": {
            "max_iter": 1000,
            "random_state": 42
        },
        "created_date": datetime.now().isoformat(),
        "use_case": "Binary classification for customer churn prediction",
        "input_features": feature_names,
        "output_classes": ["no_churn", "churn"],
        "business_impact": "Reduces customer acquisition cost by identifying at-risk customers"
    }
}

# Save metadata
import json
with open("examples/models_metadata.json", "w") as f:
    json.dump(models_metadata, f, indent=2)

print(f"   💾 Saved metadata to: examples/models_metadata.json")

# 5. SUMMARY
print("\n" + "=" * 60)
print("🎉 MODEL CREATION COMPLETE!")
print("=" * 60)

print(f"""
📁 Files Created:
   ├── examples/models/
   │   ├── iris_classifier_v1.pkl      ({os.path.getsize(iris_model_path):,} bytes)
   │   ├── iris_classifier_v2.pkl      ({os.path.getsize(iris_v2_model_path):,} bytes)
   │   └── churn_predictor_v1.pkl      ({os.path.getsize(churn_model_path):,} bytes)
   ├── examples/sample_data/
   │   ├── iris_test_data.pkl
   │   ├── churn_test_data.pkl
   │   └── customer_churn_dataset.csv
   └── examples/models_metadata.json

📊 Model Performance:
   🌸 Iris Classifier v1:    {iris_accuracy:.1%} accuracy
   🌸 Iris Classifier v2:    {iris_v2_accuracy:.1%} accuracy  
   💼 Churn Predictor:       {churn_accuracy:.1%} accuracy

🚀 Ready for upload to ML Registry!
""")

print("\n💡 Next Steps:")
print("   1. Run the API test script to upload these models")
print("   2. Test download and version management")
print("   3. Verify MinIO storage and PostgreSQL records")
print("   4. Move to Kubernetes deployment")