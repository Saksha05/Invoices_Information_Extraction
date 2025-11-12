# ✅ Kubernetes Deployment - SUCCESS!

## 🎉 Deployment Complete!

Your Insurance RAG Application is now running on Kubernetes (Kind cluster)!

### 📊 Deployment Status

```
✅ Kubernetes Cluster: kind-insurance-rag (Running)
✅ Namespace: insurance-rag (Created)
✅ PostgreSQL Database: Running (1/1 pods ready)
✅ RAG Application: Running (1/1 pods ready)
✅ Services: Configured
✅ Persistent Storage: Provisioned
```

### 🌐 Access Your Application

**Port forwarding is now active!**

The application is accessible at:
**http://localhost:8501**

Keep the terminal with port forwarding running, or restart it with:
```bash
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501
```

### 📝 Deployed Resources

| Resource | Name | Status | Details |
|----------|------|--------|---------|
| **Namespace** | insurance-rag | ✅ Active | Isolated environment |
| **PostgreSQL** | postgres-deployment | ✅ Running | pgvector enabled, 5Gi storage |
| **RAG App** | rag-app-deployment | ✅ Running | Streamlit UI, ML models loaded |
| **DB Service** | postgres-service | ✅ Active | ClusterIP (internal) |
| **App Service** | rag-app-service | ✅ Active | NodePort 30501 |
| **Secrets** | insurance-rag-secrets | ✅ Configured | API keys, DB credentials |
| **ConfigMap** | postgres-init-config | ✅ Configured | Database initialization |
| **PVCs** | 4 volumes | ✅ Bound | postgres, app-data, logs, models |

###  🔍 Useful Commands

**View Application Logs:**
```bash
kubectl logs -n insurance-rag -l component=application -f
```

**View Database Logs:**
```bash
kubectl logs -n insurance-rag -l component=database -f
```

**Check Pod Status:**
```bash
kubectl get pods -n insurance-rag
```

**Describe Pods:**
```bash
kubectl describe pod -n insurance-rag <pod-name>
```

**Execute Commands in Pod:**
```bash
# RAG App
kubectl exec -it -n insurance-rag deployment/rag-app-deployment -- /bin/bash

# PostgreSQL
kubectl exec -it -n insurance-rag deployment/postgres-deployment -- psql -U postgres -d insurance_rag
```

**Check Resource Usage:**
```bash
kubectl top pods -n insurance-rag
```

**Get All Resources:**
```bash
kubectl get all -n insurance-rag
```

### 🔄 Management Commands

**Restart Application:**
```bash
kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

**Scale Application:**
```bash
kubectl scale deployment/rag-app-deployment -n insurance-rag --replicas=2
```

**Update Secrets:**
```bash
source .env
kubectl create secret generic insurance-rag-secrets \
  --namespace=insurance-rag \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=POSTGRES_DB="insurance_rag" \
  --from-literal=POSTGRES_USER="postgres" \
  --from-literal=POSTGRES_PASSWORD="postgres123" \
  --from-literal=POSTGRES_HOST="postgres-service" \
  --from-literal=POSTGRES_PORT="5432" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

### 🧹 Cleanup

**Delete Everything:**
```bash
# Delete namespace (removes all resources)
kubectl delete namespace insurance-rag

# Delete the Kind cluster
kind delete cluster --name insurance-rag
```

**Delete Specific Resources:**
```bash
# Delete deployments only
kubectl delete deployment -n insurance-rag --all

# Delete services only
kubectl delete svc -n insurance-rag --all
```

### 🎯 What's Running

1. **PostgreSQL 16 with pgvector**
   - Database: insurance_rag
   - Port: 5432 (internal)
   - Storage: 5Gi (dynamically provisioned)
   - Health checks: Active

2. **RAG Application (Streamlit)**
   - ML Model: sentence-transformers/all-MiniLM-L6-v2
   - OCR: Tesseract 5.5.0
   - Port: 8501
   - Storage: Models (5Gi), Data (10Gi), Logs (2Gi)
   - Health checks: Active

### 📈 Next Steps

1. **Test the Application**:
   - Open http://localhost:8501 in your browser
   - Upload insurance documents
   - Test the RAG functionality

2. **Monitor Performance**:
   ```bash
   kubectl top pods -n insurance-rag
   ```

3. **Check Logs**:
   ```bash
   kubectl logs -n insurance-rag -l component=application -f
   ```

4. **Scale if Needed**:
   ```bash
   kubectl scale deployment/rag-app-deployment -n insurance-rag --replicas=2
   ```

### 🔧 Troubleshooting

**If pods are not starting:**
```bash
kubectl describe pod -n insurance-rag <pod-name>
kubectl logs -n insurance-rag <pod-name>
```

**If port forwarding stops:**
```bash
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501
```

**If you need to reload the Docker image:**
```bash
# Rebuild
podman build -t localhost/invoices_information_extraction_rag-app:latest .

# Save and load into Kind
podman save localhost/invoices_information_extraction_rag-app:latest -o /tmp/rag-app.tar
kind load image-archive /tmp/rag-app.tar --name insurance-rag
rm /tmp/rag-app.tar

# Restart deployment
kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

### 📚 Documentation

- **Full Deployment Guide**: `KUBERNETES_DEPLOYMENT.md`
- **Quick Reference**: `k8s/QUICK_REFERENCE.md`
- **Setup Summary**: `KUBERNETES_SETUP_SUMMARY.md`

---

## ✅ You're All Set!

**Your application is ready to use at: http://localhost:8501**

Upload your insurance documents and test the RAG functionality! 🚀

---

**Deployment Date**: November 12, 2025  
**Kubernetes**: Kind v1.33.1  
**Cluster**: insurance-rag
