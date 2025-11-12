# ✅ Kubernetes Deployment - Complete Setup

## 🎉 What's Been Created

Your Insurance RAG Application is now ready to deploy to Kubernetes! Here's everything that was created:

### 📁 Kubernetes Manifests (`k8s/` directory)

| File | Purpose | Type |
|------|---------|------|
| `namespace.yaml` | Isolates resources in `insurance-rag` namespace | Namespace |
| `secrets.yaml` | Template for sensitive data (API keys, passwords) | Secret |
| `configmap.yaml` | PostgreSQL initialization SQL script | ConfigMap |
| `postgres-pv.yaml` | 5Gi storage for PostgreSQL data | PV/PVC |
| `app-data-pv.yaml` | 10Gi storage for uploaded documents | PV/PVC |
| `app-logs-pv.yaml` | 2Gi storage for application logs | PV/PVC |
| `models-pv.yaml` | 5Gi storage for ML models cache | PV/PVC |
| `postgres-service.yaml` | Internal database service (ClusterIP) | Service |
| `rag-app-service.yaml` | External app access (NodePort 30501) | Service |
| `postgres-deployment.yaml` | PostgreSQL 16 with pgvector | Deployment |
| `rag-app-deployment.yaml` | Streamlit RAG application | Deployment |
| `kustomization.yaml` | Orchestrates all resources | Kustomization |
| `QUICK_REFERENCE.md` | Command cheat sheet | Documentation |

### 📜 Deployment Scripts

| File | Purpose |
|------|---------|
| `deploy-k8s.sh` | Automated deployment script (executable) |
| `KUBERNETES_DEPLOYMENT.md` | Complete deployment guide |

---

## 🚀 Quick Start Guide

### 1️⃣ Choose Your Kubernetes Platform

**Minikube** (Recommended):
```bash
minikube start --cpus=4 --memory=8192 --disk-size=20g
```

**Kind**:
```bash
kind create cluster --name insurance-rag
```

**Docker Desktop**:
Enable Kubernetes in Settings → Kubernetes

### 2️⃣ Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit and add your Google API key
nano .env  # or your preferred editor
```

**Update this line in `.env`:**
```bash
GOOGLE_API_KEY=your-actual-google-api-key-here
```

### 3️⃣ Build Docker Image

```bash
# Using Docker
docker build -t localhost/invoices_information_extraction_rag-app:latest .

# OR using Podman
podman build -t localhost/invoices_information_extraction_rag-app:latest .
```

### 4️⃣ Deploy to Kubernetes

**Option A: Automated (Recommended)**
```bash
./deploy-k8s.sh
```

**Option B: Manual**
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets
source .env
kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=POSTGRES_DB="insurance_rag" \
  --from-literal=POSTGRES_USER="postgres" \
  --from-literal=POSTGRES_PASSWORD="postgres123" \
  --from-literal=POSTGRES_HOST="postgres-service" \
  --from-literal=POSTGRES_PORT="5432"

# Deploy all resources
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-pv.yaml
kubectl apply -f k8s/app-data-pv.yaml
kubectl apply -f k8s/app-logs-pv.yaml
kubectl apply -f k8s/models-pv.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/rag-app-service.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/rag-app-deployment.yaml
```

### 5️⃣ Access Your Application

**Minikube:**
```bash
minikube service rag-app-service -n insurance-rag
```

**Kind:**
```bash
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501
# Then open: http://localhost:8501
```

**Docker Desktop:**
```bash
# Open: http://localhost:30501
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│         insurance-rag (Namespace)                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────────┐      ┌──────────────────┐    │
│  │  PostgreSQL      │◄─────┤   RAG App        │    │
│  │  (pgvector)      │      │   (Streamlit)    │    │
│  │                  │      │                  │    │
│  │  Port: 5432      │      │  Port: 8501      │    │
│  │  Replicas: 1     │      │  Replicas: 1     │    │
│  └────────┬─────────┘      └────────┬─────────┘    │
│           │                         │               │
│  ┌────────▼─────────┐      ┌────────▼─────────┐   │
│  │ postgres-service │      │ rag-app-service  │   │
│  │   (ClusterIP)    │      │   (NodePort)     │   │
│  └──────────────────┘      └────────┬─────────┘   │
│                                      │              │
└──────────────────────────────────────┼──────────────┘
                                       │
                                       ▼
                              External Access
                          http://localhost:30501
```

### Persistent Storage

```
Host Machine                    Kubernetes
─────────────                   ──────────

/mnt/data/insurance-rag/
  ├── postgres/       ────►     postgres-pv  (5Gi)
  ├── app-data/       ────►     app-data-pv  (10Gi)
  ├── app-logs/       ────►     app-logs-pv  (2Gi)
  └── models/         ────►     models-pv    (5Gi)
```

---

## 🔍 Monitoring Commands

```bash
# Check all resources
kubectl get all -n insurance-rag

# View pods
kubectl get pods -n insurance-rag

# View logs (RAG App)
kubectl logs -n insurance-rag -l component=application -f

# View logs (PostgreSQL)
kubectl logs -n insurance-rag -l component=database -f

# Check pod details
kubectl describe pod <pod-name> -n insurance-rag

# Resource usage
kubectl top pods -n insurance-rag
```

---

## 🎯 Key Features

### ✅ Security
- Non-root user (UID 1001)
- Secrets management
- Network isolation
- Read-only filesystems where applicable

### ✅ Reliability
- Health checks (liveness, readiness, startup)
- Init containers for dependency management
- Persistent storage for data durability
- Proper resource limits

### ✅ Performance
- Resource requests/limits
- CPU: 1-4 cores per app
- Memory: 2-8 GB per app
- Efficient model caching

### ✅ Observability
- Structured logging
- Health check endpoints
- Event tracking
- Resource monitoring

---

## 🔧 Common Tasks

### Update Application

```bash
# Rebuild image
docker build -t localhost/invoices_information_extraction_rag-app:latest .

# For Minikube: Reload image
minikube image load localhost/invoices_information_extraction_rag-app:latest

# Restart deployment
kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

### Scale Application

```bash
# Scale to 2 replicas
kubectl scale deployment/rag-app-deployment -n insurance-rag --replicas=2
```

### Update Secrets

```bash
kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="new-api-key" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

### Clean Up

```bash
# Delete everything
kubectl delete namespace insurance-rag
kubectl delete pv postgres-pv app-data-pv app-logs-pv models-pv
```

---

## 📚 Documentation

- **`KUBERNETES_DEPLOYMENT.md`** - Complete deployment guide with troubleshooting
- **`k8s/QUICK_REFERENCE.md`** - Command cheat sheet
- **`deploy-k8s.sh`** - Automated deployment script

---

## ⚠️ Important Notes

### 🔐 Secrets Management

**DO NOT commit actual secrets to Git!**

The `k8s/secrets.yaml` file contains placeholders only. For production:

1. Use `kubectl create secret` with actual values
2. Or use Kustomize `secretGenerator`
3. Or use external secret management (Vault, Sealed Secrets)

### 💾 Data Persistence

- Data persists across pod restarts
- PersistentVolumes use `hostPath` (local development only)
- For production, use cloud storage (EBS, GCE PD, Azure Disk)

### 🚀 First Deployment

The first deployment takes **5-10 minutes** because:
1. Downloading ML models (~1-2 GB)
2. Installing dependencies
3. Database initialization

Subsequent restarts are faster due to caching.

---

## 🎓 Next Steps

1. **Deploy**: Run `./deploy-k8s.sh`
2. **Test**: Upload insurance documents
3. **Monitor**: Watch logs and resource usage
4. **Scale**: Increase replicas as needed
5. **Production**: Consider managed Kubernetes (GKE, EKS, AKS)

---

## 📞 Need Help?

1. Check `KUBERNETES_DEPLOYMENT.md` for detailed troubleshooting
2. View logs: `kubectl logs -n insurance-rag <pod-name>`
3. Check events: `kubectl get events -n insurance-rag`

---

**Ready to deploy? Run `./deploy-k8s.sh` and you're all set! 🚀**
