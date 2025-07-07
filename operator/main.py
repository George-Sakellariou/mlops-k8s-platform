import kopf
import kubernetes
import yaml
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
try:
    kubernetes.config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes configuration")
except:
    try:
        kubernetes.config.load_kube_config()
        logger.info("Loaded local Kubernetes configuration")
    except Exception as e:
        logger.error(f"Failed to load Kubernetes configuration: {e}")
        raise

# Initialize Kubernetes API clients
apps_v1 = kubernetes.client.AppsV1Api()
core_v1 = kubernetes.client.CoreV1Api()
autoscaling_v1 = kubernetes.client.AutoscalingV1Api()

def create_inference_deployment(spec: Dict[str, Any], name: str, namespace: str) -> Dict[str, Any]:
    """Create Kubernetes Deployment for inference server"""
    
    deployment_name = f"{name}-inference"
    model_name = spec["modelName"]
    model_version = spec["modelVersion"]
    replicas = spec.get("replicas", 1)
    resources = spec.get("resources", {})
    environment = spec.get("environment", "development")
    
    # Define container resources
    resource_requests = resources.get("requests", {"memory": "256Mi", "cpu": "250m"})
    resource_limits = resources.get("limits", {"memory": "512Mi", "cpu": "500m"})
    
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_name,
            "namespace": namespace,
            "labels": {
                "app": deployment_name,
                "component": "inference-server",
                "model-name": model_name,
                "model-version": str(model_version),
                "environment": environment,
                "managed-by": "ml-operator"
            }
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": {
                    "app": deployment_name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": deployment_name,
                        "component": "inference-server",
                        "model-name": model_name,
                        "model-version": str(model_version),
                        "environment": environment
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "inference-server",
                            "image": "ml-platform/inference-server:latest",
                            "imagePullPolicy": "Never",  # For local development
                            "ports": [
                                {
                                    "containerPort": 8001,
                                    "name": "http"
                                }
                            ],
                            "env": [
                                {
                                    "name": "MODEL_NAME",
                                    "value": model_name
                                },
                                {
                                    "name": "MODEL_VERSION",
                                    "value": str(model_version)
                                },
                                {
                                    "name": "MODEL_REGISTRY_URL",
                                    "value": "http://model-registry-service:8000"
                                },
                                {
                                    "name": "INFERENCE_PORT",
                                    "value": "8001"
                                },
                                {
                                    "name": "ENVIRONMENT",
                                    "value": environment
                                }
                            ],
                            "resources": {
                                "requests": resource_requests,
                                "limits": resource_limits
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": 8001
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10,
                                "timeoutSeconds": 5
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": 8001
                                },
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5,
                                "timeoutSeconds": 3
                            }
                        }
                    ]
                }
            }
        }
    }
    
    return deployment

def create_inference_service(spec: Dict[str, Any], name: str, namespace: str) -> Dict[str, Any]:
    """Create Kubernetes Service for inference server"""
    
    deployment_name = f"{name}-inference"
    service_name = f"{name}-service"
    model_name = spec["modelName"]
    model_version = spec["modelVersion"]
    environment = spec.get("environment", "development")
    
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_name,
            "namespace": namespace,
            "labels": {
                "app": deployment_name,
                "component": "inference-server",
                "model-name": model_name,
                "model-version": str(model_version),
                "environment": environment,
                "managed-by": "ml-operator"
            }
        },
        "spec": {
            "selector": {
                "app": deployment_name
            },
            "ports": [
                {
                    "name": "http",
                    "port": 8001,
                    "targetPort": 8001
                }
            ],
            "type": "ClusterIP"
        }
    }
    
    return service

def create_hpa(spec: Dict[str, Any], name: str, namespace: str) -> Dict[str, Any]:
    """Create Horizontal Pod Autoscaler if autoscaling is enabled"""
    
    autoscaling = spec.get("autoscaling", {})
    if not autoscaling.get("enabled", False):
        return None
    
    deployment_name = f"{name}-inference"
    hpa_name = f"{name}-hpa"
    
    hpa = {
        "apiVersion": "autoscaling/v1",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {
            "name": hpa_name,
            "namespace": namespace,
            "labels": {
                "app": deployment_name,
                "component": "inference-server",
                "managed-by": "ml-operator"
            }
        },
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "name": deployment_name
            },
            "minReplicas": autoscaling.get("minReplicas", 1),
            "maxReplicas": autoscaling.get("maxReplicas", 5),
            "targetCPUUtilizationPercentage": autoscaling.get("targetCPUUtilizationPercentage", 70)
        }
    }
    
    return hpa

@kopf.on.create('ml.example.com', 'v1', 'modeldeployments')
async def create_model_deployment(spec, name, namespace, logger, **kwargs):
    """Handle ModelDeployment creation"""
    
    logger.info(f"Creating ModelDeployment {name} in namespace {namespace}")
    logger.info(f"Model: {spec['modelName']} v{spec['modelVersion']}")
    
    try:
        # Create Deployment
        deployment = create_inference_deployment(spec, name, namespace)
        logger.info(f"Creating Deployment: {deployment['metadata']['name']}")
        
        apps_v1.create_namespaced_deployment(
            namespace=namespace,
            body=deployment
        )
        
        # Create Service
        service = create_inference_service(spec, name, namespace)
        logger.info(f"Creating Service: {service['metadata']['name']}")
        
        core_v1.create_namespaced_service(
            namespace=namespace,
            body=service
        )
        
        # Create HPA if autoscaling is enabled
        hpa = create_hpa(spec, name, namespace)
        if hpa:
            logger.info(f"Creating HPA: {hpa['metadata']['name']}")
            autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(
                namespace=namespace,
                body=hpa
            )
        
        # Update status
        return {
            'phase': 'Running',
            'deploymentName': deployment['metadata']['name'],
            'serviceName': service['metadata']['name'],
            'replicas': spec.get('replicas', 1),
            'lastUpdated': datetime.utcnow().isoformat(),
            'conditions': [{
                'type': 'Ready',
                'status': 'True',
                'lastTransitionTime': datetime.utcnow().isoformat(),
                'reason': 'DeploymentCreated',
                'message': 'ModelDeployment resources created successfully'
            }]
        }
        
    except Exception as e:
        logger.error(f"Failed to create ModelDeployment {name}: {e}")
        return {
            'phase': 'Failed',
            'lastUpdated': datetime.utcnow().isoformat(),
            'conditions': [{
                'type': 'Ready',
                'status': 'False',
                'lastTransitionTime': datetime.utcnow().isoformat(),
                'reason': 'CreationFailed',
                'message': f'Failed to create resources: {str(e)}'
            }]
        }

@kopf.on.update('ml.example.com', 'v1', 'modeldeployments')
async def update_model_deployment(spec, name, namespace, old, new, logger, **kwargs):
    """Handle ModelDeployment updates"""
    
    logger.info(f"Updating ModelDeployment {name} in namespace {namespace}")
    
    try:
        deployment_name = f"{name}-inference"
        
        # Check if model version changed
        old_version = old.get('spec', {}).get('modelVersion')
        new_version = spec.get('modelVersion')
        
        if old_version != new_version:
            logger.info(f"Model version changed from {old_version} to {new_version}")
        
        # Update Deployment
        deployment = create_inference_deployment(spec, name, namespace)
        
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
        
        # Update Service if needed
        service = create_inference_service(spec, name, namespace)
        service_name = f"{name}-service"
        
        core_v1.patch_namespaced_service(
            name=service_name,
            namespace=namespace,
            body=service
        )
        
        # Handle HPA updates
        hpa = create_hpa(spec, name, namespace)
        hpa_name = f"{name}-hpa"
        
        try:
            # Check if HPA exists
            autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(
                name=hpa_name,
                namespace=namespace
            )
            
            if hpa:
                # Update existing HPA
                autoscaling_v1.patch_namespaced_horizontal_pod_autoscaler(
                    name=hpa_name,
                    namespace=namespace,
                    body=hpa
                )
            else:
                # Delete HPA if autoscaling disabled
                autoscaling_v1.delete_namespaced_horizontal_pod_autoscaler(
                    name=hpa_name,
                    namespace=namespace
                )
                
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 404:
                # HPA doesn't exist, create if needed
                if hpa:
                    autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(
                        namespace=namespace,
                        body=hpa
                    )
            else:
                raise
        
        return {
            'phase': 'Running',
            'deploymentName': deployment_name,
            'serviceName': f"{name}-service",
            'replicas': spec.get('replicas', 1),
            'lastUpdated': datetime.utcnow().isoformat(),
            'conditions': [{
                'type': 'Ready',
                'status': 'True',
                'lastTransitionTime': datetime.utcnow().isoformat(),
                'reason': 'DeploymentUpdated',
                'message': 'ModelDeployment updated successfully'
            }]
        }
        
    except Exception as e:
        logger.error(f"Failed to update ModelDeployment {name}: {e}")
        return {
            'phase': 'Failed',
            'lastUpdated': datetime.utcnow().isoformat(),
            'conditions': [{
                'type': 'Ready',
                'status': 'False',
                'lastTransitionTime': datetime.utcnow().isoformat(),
                'reason': 'UpdateFailed',
                'message': f'Failed to update resources: {str(e)}'
            }]
        }

@kopf.on.delete('ml.example.com', 'v1', 'modeldeployments')
async def delete_model_deployment(spec, name, namespace, logger, **kwargs):
    """Handle ModelDeployment deletion"""
    
    logger.info(f"Deleting ModelDeployment {name} in namespace {namespace}")
    
    try:
        deployment_name = f"{name}-inference"
        service_name = f"{name}-service"
        hpa_name = f"{name}-hpa"
        
        # Delete Deployment
        try:
            apps_v1.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            logger.info(f"Deleted Deployment: {deployment_name}")
        except kubernetes.client.exceptions.ApiException as e:
            if e.status != 404:
                raise
        
        # Delete Service
        try:
            core_v1.delete_namespaced_service(
                name=service_name,
                namespace=namespace
            )
            logger.info(f"Deleted Service: {service_name}")
        except kubernetes.client.exceptions.ApiException as e:
            if e.status != 404:
                raise
        
        # Delete HPA if exists
        try:
            autoscaling_v1.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name,
                namespace=namespace
            )
            logger.info(f"Deleted HPA: {hpa_name}")
        except kubernetes.client.exceptions.ApiException as e:
            if e.status != 404:
                raise
        
        logger.info(f"Successfully deleted all resources for ModelDeployment {name}")
        
    except Exception as e:
        logger.error(f"Failed to delete ModelDeployment {name}: {e}")
        raise

# Health check and monitoring
@kopf.on.timer('ml.example.com', 'v1', 'modeldeployments', interval=60)
async def monitor_deployments(spec, name, namespace, status, logger, **kwargs):
    """Monitor ModelDeployment health"""
    
    try:
        deployment_name = f"{name}-inference"
        
        # Get deployment status
        deployment = apps_v1.read_namespaced_deployment_status(
            name=deployment_name,
            namespace=namespace
        )
        
        ready_replicas = deployment.status.ready_replicas or 0
        desired_replicas = deployment.spec.replicas
        
        # Update status if changed
        current_phase = status.get('phase', 'Unknown')
        new_phase = 'Running' if ready_replicas == desired_replicas else 'Updating'
        
        if current_phase != new_phase or status.get('readyReplicas') != ready_replicas:
            return {
                'phase': new_phase,
                'replicas': desired_replicas,
                'readyReplicas': ready_replicas,
                'lastUpdated': datetime.utcnow().isoformat(),
                'conditions': [{
                    'type': 'Ready',
                    'status': 'True' if new_phase == 'Running' else 'False',
                    'lastTransitionTime': datetime.utcnow().isoformat(),
                    'reason': 'HealthCheck',
                    'message': f'{ready_replicas}/{desired_replicas} replicas ready'
                }]
            }
    
    except Exception as e:
        logger.error(f"Health check failed for {name}: {e}")
        return {
            'phase': 'Failed',
            'lastUpdated': datetime.utcnow().isoformat(),
            'conditions': [{
                'type': 'Ready',
                'status': 'False',
                'lastTransitionTime': datetime.utcnow().isoformat(),
                'reason': 'HealthCheckFailed',
                'message': f'Health check failed: {str(e)}'
            }]
        }

if __name__ == "__main__":
    logger.info("Starting ML Model Deployment Operator...")
    kopf.run()