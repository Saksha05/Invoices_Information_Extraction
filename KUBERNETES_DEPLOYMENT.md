# 🚀 Kubernetes Deployment Guide - Insurance RAG Application

Complete guide for deploying the Insurance RAG Application to a local Kubernetes cluster.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supported Kubernetes Platforms](#supported-kubernetes-platforms)
3. [Quick Start](#quick-start)
4. [Manual Deployment](#manual-deployment)
5. [Architecture Overview](#architecture-overview)
6. [Configuration](#configuration)
7. [Accessing the Application](#accessing-the-application)
8. [Monitoring and Debugging](#monitoring-and-debugging)
9. [Scaling](#scaling)
10. [Cleanup](#cleanup)
11. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Required Tools

- **kubectl** (v1.25+) - [Installation Guide](https://kubernetes.io/docs/tasks/tools/)
- **Docker** or **Podman** - For building container images
- **Local Kubernetes Cluster** - Choose one:
  - [Minikube](https://minikube.sigs.k8s.io/docs/start/)
  - [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Kubernetes enabled)
  - [K3s](https://k3s.io/)

### System Requirements

- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM
- **Storage**: 20GB+ free disk space
- **OS**: macOS, Linux, or Windows (WSL2)

### Verify Installation

```bash
# Check kubectl
kubectl version --client

# Check cluster connection
kubectl cluster-info

# Check available nodes
kubectl get nodes
```

---

## 🎯 Supported Kubernetes Platforms

### 1. **Minikube** (Recommended for Development)

```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Verify
minikube status
```

### 2. **Kind** (Kubernetes in Docker)

```bash
# Create cluster
kind create cluster --name insurance-rag

# Verify
kind get clusters
kubectl cluster-info --context kind-insurance-rag
```

### 3. **Docker Desktop**

1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Enable Kubernetes
4. Click "Apply & Restart"

### 4. **K3s** (Lightweight Kubernetes)

```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Check status
sudo systemctl status k3s
```

---

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Clone the repository
cd /path/to/Invoices_Information_Extraction

# 2. Create .env file from template
cp .env.example .env

# 3. Edit .env and add your Google API key
nano .env  # or use your preferred editor

# 4. Run the deployment script
./deploy-k8s.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Build Docker image
- ✅ Create namespace
- ✅ Setup secrets
- ✅ Deploy all resources
- ✅ Wait for pods to be ready
- ✅ Display access instructions

### Option 2: Using Kustomize

```bash
# 1. Set your API key
export GOOGLE_API_KEY="your-actual-api-key"

# 2. Deploy with kustomize
kubectl apply -k k8s/

# 3. Check status
kubectl get all -n insurance-rag
```

---

## 📝 Manual Deployment

If you prefer step-by-step manual deployment:

### Step 1: Build Docker Image

```bash
# Using Docker
docker build -t localhost/invoices_information_extraction_rag-app:latest .

# OR using Podman
podman build -t localhost/invoices_information_extraction_rag-app:latest .
```

### Step 2: Load Image into Cluster (if needed)

**For Minikube:**
```bash
# Docker
minikube image load localhost/invoices_information_extraction_rag-app:latest

# Podman
podman save localhost/invoices_information_extraction_rag-app:latest | minikube image load -
```

**For Kind:**
```bash
kind load docker-image localhost/invoices_information_extraction_rag-app:latest
```

**For Docker Desktop / K3s:**
No action needed - images are available directly

### Step 3: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 4: Create Secrets

```bash
# Create from .env file
source .env

kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=POSTGRES_DB="insurance_rag" \
  --from-literal=POSTGRES_USER="postgres" \
  --from-literal=POSTGRES_PASSWORD="postgres123" \
  --from-literal=POSTGRES_HOST="postgres-service" \
  --from-literal=POSTGRES_PORT="5432"
```

### Step 5: Deploy Resources

```bash
# ConfigMap
kubectl apply -f k8s/configmap.yaml

# Persistent Volumes
kubectl apply -f k8s/postgres-pv.yaml
kubectl apply -f k8s/app-data-pv.yaml
kubectl apply -f k8s/app-logs-pv.yaml
kubectl apply -f k8s/models-pv.yaml

# Services
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/rag-app-service.yaml

# Deployments
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/rag-app-deployment.yaml
```

### Step 6: Wait for Deployment

```bash
# Watch deployment progress
kubectl get pods -n insurance-rag -w

# Wait for PostgreSQL
kubectl wait --for=condition=available --timeout=300s \
  deployment/postgres-deployment -n insurance-rag

# Wait for RAG App
kubectl wait --for=condition=available --timeout=600s \
  deployment/rag-app-deployment -n insurance-rag
```

---

## 🏗️ Architecture Overview

### Kubernetes Resources

```
insurance-rag (namespace)
├── Deployments
│   ├── postgres-deployment (1 replica)
│   └── rag-app-deployment (1 replica)
├── Services
│   ├── postgres-service (ClusterIP - Headless)
│   └── rag-app-service (NodePort - 30501)
├── ConfigMaps
│   └── postgres-init-config
├── Secrets
│   └── insurance-rag-secrets
└── PersistentVolumes
    ├── postgres-pv → postgres-pvc
    ├── app-data-pv → app-data-pvc
    ├── app-logs-pv → app-logs-pvc
    └── models-pv → models-pvc
```

### Component Details

| Component | Image | Replicas | Resources |
|-----------|-------|----------|-----------|
| PostgreSQL | `pgvector/pgvector:pg16` | 1 | 512Mi-2Gi RAM, 0.5-2 CPU |
| RAG App | `localhost/...rag-app:latest` | 1 | 2Gi-8Gi RAM, 1-4 CPU |

### Volume Mounts

| Volume | Size | Mount Path | Purpose |
|--------|------|------------|---------|
| postgres-pv | 5Gi | `/var/lib/postgresql/data` | Database storage |
| app-data-pv | 10Gi | `/app/data` | Uploaded documents |
| app-logs-pv | 2Gi | `/app/logs` | Application logs |
| models-pv | 5Gi | `/app/models` | ML model cache |

---

## ⚙️ Configuration

### Environment Variables

Managed via `insurance-rag-secrets` Secret:

```yaml
GOOGLE_API_KEY: "your-api-key"
POSTGRES_DB: "insurance_rag"
POSTGRES_USER: "postgres"
POSTGRES_PASSWORD: "postgres123"
POSTGRES_HOST: "postgres-service"
POSTGRES_PORT: "5432"
```

### Updating Secrets

```bash
# Update API key
kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="new-api-key" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

### Resource Limits

Adjust in deployment YAML files:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

---

## 🌐 Accessing the Application

### Minikube

```bash
# Option 1: Open in browser automatically
minikube service rag-app-service -n insurance-rag

# Option 2: Get URL and open manually
minikube service rag-app-service -n insurance-rag --url
# Output: http://192.168.49.2:30501
```

### Kind

```bash
# Port forward to localhost
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501

# Access at: http://localhost:8501
```

### Docker Desktop

```bash
# Application available at NodePort
# http://localhost:30501
```

### K3s (or generic cluster)

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Access at: http://$NODE_IP:30501
echo "http://$NODE_IP:30501"
```

---

## 📊 Monitoring and Debugging

### Check Pod Status

```bash
# List all pods
kubectl get pods -n insurance-rag

# Detailed pod information
kubectl describe pod <pod-name> -n insurance-rag

# Watch pods in real-time
kubectl get pods -n insurance-rag -w
```

### View Logs

```bash
# RAG Application logs
kubectl logs -n insurance-rag -l component=application -f

# PostgreSQL logs
kubectl logs -n insurance-rag -l component=database -f

# Specific pod logs
kubectl logs -n insurance-rag <pod-name> -f

# Previous pod logs (if crashed)
kubectl logs -n insurance-rag <pod-name> --previous
```

### Execute Commands in Pods

```bash
# RAG App container
kubectl exec -it -n insurance-rag <rag-app-pod> -- /bin/bash

# PostgreSQL container
kubectl exec -it -n insurance-rag <postgres-pod> -- psql -U postgres -d insurance_rag

# Check Tesseract
kubectl exec -n insurance-rag <rag-app-pod> -- tesseract --version
```

### Health Checks

```bash
# Check deployment status
kubectl get deployments -n insurance-rag

# Check endpoints
kubectl get endpoints -n insurance-rag

# Check events
kubectl get events -n insurance-rag --sort-by='.lastTimestamp'
```

### Resource Usage

```bash
# CPU and Memory usage
kubectl top pods -n insurance-rag

# Node resources
kubectl top nodes
```

---

## 📈 Scaling

### Scale RAG Application

```bash
# Scale to 2 replicas
kubectl scale deployment/rag-app-deployment -n insurance-rag --replicas=2

# Verify scaling
kubectl get pods -n insurance-rag -l component=application
```

**Note:** PostgreSQL should remain at 1 replica for data consistency.

### Auto-scaling (HPA)

```bash
# Create Horizontal Pod Autoscaler
kubectl autoscale deployment rag-app-deployment \
  --namespace=insurance-rag \
  --cpu-percent=70 \
  --min=1 \
  --max=5

# Check HPA status
kubectl get hpa -n insurance-rag
```

---

## 🧹 Cleanup

### Delete Everything

```bash
# Delete entire namespace (removes all resources)
kubectl delete namespace insurance-rag

# Delete PersistentVolumes (manual cleanup)
kubectl delete pv postgres-pv app-data-pv app-logs-pv models-pv
```

### Delete Specific Resources

```bash
# Delete deployments only
kubectl delete deployment -n insurance-rag --all

# Delete services only
kubectl delete svc -n insurance-rag --all

# Delete PVCs
kubectl delete pvc -n insurance-rag --all
```

### Stop Kubernetes Cluster

**Minikube:**
```bash
minikube stop
minikube delete  # Completely remove cluster
```

**Kind:**
```bash
kind delete cluster --name insurance-rag
```

**Docker Desktop:**
Settings → Kubernetes → Disable

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **Pods in ImagePullBackOff**

```bash
# Check image availability
kubectl describe pod <pod-name> -n insurance-rag

# For Minikube: Reload image
minikube image load localhost/invoices_information_extraction_rag-app:latest

# For Kind: Reload image
kind load docker-image localhost/invoices_information_extraction_rag-app:latest
```

#### 2. **Pods in CrashLoopBackOff**

```bash
# Check logs
kubectl logs <pod-name> -n insurance-rag

# Check previous logs
kubectl logs <pod-name> -n insurance-rag --previous

# Check events
kubectl describe pod <pod-name> -n insurance-rag
```

#### 3. **PersistentVolume Not Binding**

```bash
# Check PV status
kubectl get pv

# Check PVC status
kubectl get pvc -n insurance-rag

# For Minikube: SSH and create directories
minikube ssh
sudo mkdir -p /mnt/data/insurance-rag/{postgres,app-data,app-logs,models}
sudo chmod -R 777 /mnt/data/insurance-rag
exit
```

#### 4. **Database Connection Errors**

```bash
# Verify PostgreSQL is running
kubectl get pods -n insurance-rag -l component=database

# Check PostgreSQL logs
kubectl logs -n insurance-rag -l component=database

# Test connection from app pod
kubectl exec -n insurance-rag <rag-app-pod> -- \
  nc -zv postgres-service 5432
```

#### 5. **Application Not Accessible**

```bash
# Check service
kubectl get svc -n insurance-rag

# Check endpoints
kubectl get endpoints -n insurance-rag

# For Minikube: Ensure tunnel is running
minikube tunnel  # In separate terminal

# For Kind: Ensure port-forward is active
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501
```

#### 6. **Slow Model Loading**

The first startup takes 5-10 minutes to download ML models. Check progress:

```bash
# Watch logs
kubectl logs -n insurance-rag -l component=application -f | grep -i "model\|download"

# Check if models are cached
kubectl exec -n insurance-rag <rag-app-pod> -- ls -la /app/models
```

---

## 📚 Additional Resources

### Kubernetes Documentation
- [Kubectl Reference](https://kubernetes.io/docs/reference/kubectl/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Debugging Pods](https://kubernetes.io/docs/tasks/debug/debug-application/)

### Local Kubernetes
- [Minikube Docs](https://minikube.sigs.k8s.io/docs/)
- [Kind Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)

### Application-Specific
- [PostgreSQL pgvector](https://github.com/pgvector/pgvector)
- [Streamlit Deployment](https://docs.streamlit.io/knowledge-base/deploy)
- [Google Gemini API](https://ai.google.dev/docs)

---

## 🎯 Next Steps

1. **Production Deployment**: Consider managed Kubernetes (GKE, EKS, AKS)
2. **Ingress Controller**: Set up Nginx Ingress for proper routing
3. **SSL/TLS**: Configure certificates for HTTPS
4. **Monitoring**: Add Prometheus + Grafana
5. **CI/CD**: Automate with GitHub Actions or GitLab CI
6. **Backup**: Set up database backup strategies
7. **High Availability**: Configure multi-replica deployments with load balancing

---

## 📞 Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review pod logs: `kubectl logs -n insurance-rag <pod-name>`
- Check events: `kubectl get events -n insurance-rag`

---

**Happy Deploying! 🚀**
