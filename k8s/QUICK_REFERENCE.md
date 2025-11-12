# ============================================================================
# Quick Reference - Kubernetes Deployment Commands
# ============================================================================

## Prerequisites Check
kubectl version --client
kubectl cluster-info
kubectl get nodes

## Deploy Application (Quick Start)
./deploy-k8s.sh

## Manual Deployment Steps

# 1. Build image
docker build -t localhost/invoices_information_extraction_rag-app:latest .
# OR
podman build -t localhost/invoices_information_extraction_rag-app:latest .

# 2. Load image (Minikube)
minikube image load localhost/invoices_information_extraction_rag-app:latest

# 3. Create namespace
kubectl apply -f k8s/namespace.yaml

# 4. Create secrets (update .env first!)
source .env
kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=POSTGRES_DB="insurance_rag" \
  --from-literal=POSTGRES_USER="postgres" \
  --from-literal=POSTGRES_PASSWORD="postgres123" \
  --from-literal=POSTGRES_HOST="postgres-service" \
  --from-literal=POSTGRES_PORT="5432"

# 5. Deploy resources
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-pv.yaml
kubectl apply -f k8s/app-data-pv.yaml
kubectl apply -f k8s/app-logs-pv.yaml
kubectl apply -f k8s/models-pv.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/rag-app-service.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/rag-app-deployment.yaml

## Monitoring Commands

# Get all resources
kubectl get all -n insurance-rag

# Get pods
kubectl get pods -n insurance-rag

# Watch pods
kubectl get pods -n insurance-rag -w

# Get services
kubectl get svc -n insurance-rag

# Get persistent volumes
kubectl get pv
kubectl get pvc -n insurance-rag

# Check pod details
kubectl describe pod <pod-name> -n insurance-rag

# View logs
kubectl logs -n insurance-rag -l component=application -f
kubectl logs -n insurance-rag -l component=database -f

# Execute commands in pod
kubectl exec -it -n insurance-rag <pod-name> -- /bin/bash

# Check resource usage
kubectl top pods -n insurance-rag
kubectl top nodes

## Access Application

# Minikube
minikube service rag-app-service -n insurance-rag
minikube service rag-app-service -n insurance-rag --url

# Kind / Port Forward
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501

# Docker Desktop
# Access at: http://localhost:30501

## Scaling

# Scale application
kubectl scale deployment/rag-app-deployment -n insurance-rag --replicas=2

# Auto-scale
kubectl autoscale deployment rag-app-deployment \
  --namespace=insurance-rag \
  --cpu-percent=70 \
  --min=1 \
  --max=5

## Updates

# Update secret
kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="new-key" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment
kubectl rollout restart deployment/rag-app-deployment -n insurance-rag

# Check rollout status
kubectl rollout status deployment/rag-app-deployment -n insurance-rag

# Rollback deployment
kubectl rollout undo deployment/rag-app-deployment -n insurance-rag

## Troubleshooting

# Check events
kubectl get events -n insurance-rag --sort-by='.lastTimestamp'

# Debug pod
kubectl describe pod <pod-name> -n insurance-rag

# View previous logs (if crashed)
kubectl logs <pod-name> -n insurance-rag --previous

# Test connectivity
kubectl exec -n insurance-rag <rag-app-pod> -- nc -zv postgres-service 5432

# Fix PV binding (Minikube)
minikube ssh
sudo mkdir -p /mnt/data/insurance-rag/{postgres,app-data,app-logs,models}
sudo chmod -R 777 /mnt/data/insurance-rag
exit

## Cleanup

# Delete all resources
kubectl delete namespace insurance-rag

# Delete PVs
kubectl delete pv postgres-pv app-data-pv app-logs-pv models-pv

# Delete specific resources
kubectl delete deployment -n insurance-rag --all
kubectl delete svc -n insurance-rag --all
kubectl delete pvc -n insurance-rag --all

## Cluster Management

# Minikube
minikube start --cpus=4 --memory=8192
minikube stop
minikube delete

# Kind
kind create cluster --name insurance-rag
kind delete cluster --name insurance-rag

# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>
