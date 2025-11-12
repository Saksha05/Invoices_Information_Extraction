#!/bin/bash

# ============================================================================
# Kubernetes Deployment Script for Insurance RAG Application
# Deploys the application to a local Kubernetes cluster
# Compatible with: Minikube, Kind, Docker Desktop, K3s
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

print_info "Starting pre-flight checks..."

# Check if kubectl is installed
if ! command_exists kubectl; then
    print_error "kubectl is not installed. Please install kubectl first."
    print_info "Visit: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if kubectl can connect to a cluster
if ! kubectl cluster-info &>/dev/null; then
    print_error "Cannot connect to Kubernetes cluster."
    print_info "Please ensure your cluster is running:"
    print_info "  - Minikube: minikube start"
    print_info "  - Kind: kind create cluster"
    print_info "  - Docker Desktop: Enable Kubernetes in settings"
    exit 1
fi

print_success "kubectl is installed and connected to cluster"

# Detect cluster type
CLUSTER_TYPE="unknown"
if kubectl get nodes -o jsonpath='{.items[0].metadata.name}' | grep -q "minikube"; then
    CLUSTER_TYPE="minikube"
elif kubectl get nodes -o jsonpath='{.items[0].metadata.name}' | grep -q "kind"; then
    CLUSTER_TYPE="kind"
elif kubectl get nodes -o jsonpath='{.items[0].metadata.name}' | grep -q "docker-desktop"; then
    CLUSTER_TYPE="docker-desktop"
fi

print_info "Detected cluster type: $CLUSTER_TYPE"

# ============================================================================
# Build Docker Image
# ============================================================================

print_info "Building Docker image..."

if command_exists podman; then
    print_info "Using Podman to build image..."
    podman build -t localhost/invoices_information_extraction_rag-app:latest .
    
    # For Minikube, load image into minikube
    if [ "$CLUSTER_TYPE" = "minikube" ]; then
        print_info "Loading image into Minikube..."
        podman save localhost/invoices_information_extraction_rag-app:latest | minikube image load -
    fi
    
    # For Kind, save and load image
    if [ "$CLUSTER_TYPE" = "kind" ] || kubectl get nodes -o jsonpath='{.items[0].metadata.name}' | grep -q "kind"; then
        print_info "Loading image into Kind cluster..."
        podman save localhost/invoices_information_extraction_rag-app:latest -o /tmp/rag-app.tar
        kind load image-archive /tmp/rag-app.tar --name insurance-rag
        rm -f /tmp/rag-app.tar
    fi
    
elif command_exists docker; then
    print_info "Using Docker to build image..."
    docker build -t localhost/invoices_information_extraction_rag-app:latest .
    
    # For Minikube, load image into minikube
    if [ "$CLUSTER_TYPE" = "minikube" ]; then
        print_info "Loading image into Minikube..."
        minikube image load localhost/invoices_information_extraction_rag-app:latest
    fi
    
    # For Kind, load image into kind
    if [ "$CLUSTER_TYPE" = "kind" ]; then
        print_info "Loading image into Kind cluster..."
        kind load docker-image localhost/invoices_information_extraction_rag-app:latest
    fi
else
    print_error "Neither Docker nor Podman found. Please install one of them."
    exit 1
fi

print_success "Docker image built successfully"

# ============================================================================
# Create Namespace
# ============================================================================

print_info "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

print_success "Namespace created"

# ============================================================================
# Setup Secrets
# ============================================================================

print_info "Setting up secrets..."

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Please create it from .env.example"
    print_info "Run: cp .env.example .env"
    print_info "Then edit .env and add your GOOGLE_API_KEY"
    exit 1
fi

# Source the .env file to get GOOGLE_API_KEY
source .env

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key-here" ]; then
    print_error "GOOGLE_API_KEY not set in .env file"
    print_info "Please update .env with your actual Google API key"
    exit 1
fi

# Create secret using kubectl
kubectl create secret generic insurance-rag-secrets \
    --namespace=insurance-rag \
    --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    --from-literal=POSTGRES_DB="insurance_rag" \
    --from-literal=POSTGRES_USER="postgres" \
    --from-literal=POSTGRES_PASSWORD="postgres123" \
    --from-literal=POSTGRES_HOST="postgres-service" \
    --from-literal=POSTGRES_PORT="5432" \
    --dry-run=client -o yaml | kubectl apply -f -

print_success "Secrets configured"

# ============================================================================
# Deploy Resources
# ============================================================================

print_info "Deploying ConfigMap..."
kubectl apply -f k8s/configmap.yaml

print_info "Deploying PersistentVolumes..."
kubectl apply -f k8s/postgres-pv.yaml
kubectl apply -f k8s/app-data-pv.yaml
kubectl apply -f k8s/app-logs-pv.yaml
kubectl apply -f k8s/models-pv.yaml

print_info "Deploying Services..."
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/rag-app-service.yaml

print_info "Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
print_info "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/postgres-deployment -n insurance-rag

print_success "PostgreSQL is ready"

print_info "Deploying RAG Application..."
kubectl apply -f k8s/rag-app-deployment.yaml

# Wait for RAG app to be ready
print_info "Waiting for RAG Application to be ready (this may take a few minutes for model download)..."
kubectl wait --for=condition=available --timeout=600s \
    deployment/rag-app-deployment -n insurance-rag || {
    print_warning "Deployment taking longer than expected. Checking pod status..."
    kubectl get pods -n insurance-rag
}

print_success "RAG Application is ready"

# ============================================================================
# Display Status
# ============================================================================

echo ""
print_success "=========================================="
print_success "Deployment Complete!"
print_success "=========================================="
echo ""

print_info "Checking deployment status..."
kubectl get all -n insurance-rag

echo ""
print_info "Persistent Volumes:"
kubectl get pv

echo ""
print_info "Persistent Volume Claims:"
kubectl get pvc -n insurance-rag

# ============================================================================
# Access Instructions
# ============================================================================

echo ""
print_info "=========================================="
print_info "Access Your Application"
print_info "=========================================="
echo ""

if [ "$CLUSTER_TYPE" = "minikube" ]; then
    print_info "To access the application, run:"
    echo "  minikube service rag-app-service -n insurance-rag"
    echo ""
    print_info "Or get the URL with:"
    echo "  minikube service rag-app-service -n insurance-rag --url"
    
elif [ "$CLUSTER_TYPE" = "kind" ]; then
    print_info "To access the application, use port forwarding:"
    echo "  kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501"
    echo ""
    print_info "Then open: http://localhost:8501"
    
elif [ "$CLUSTER_TYPE" = "docker-desktop" ]; then
    NODE_PORT=$(kubectl get svc rag-app-service -n insurance-rag -o jsonpath='{.spec.ports[0].nodePort}')
    print_info "Application available at: http://localhost:$NODE_PORT"
    
else
    NODE_PORT=$(kubectl get svc rag-app-service -n insurance-rag -o jsonpath='{.spec.ports[0].nodePort}')
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    print_info "Application available at: http://$NODE_IP:$NODE_PORT"
fi

echo ""
print_info "=========================================="
print_info "Useful Commands"
print_info "=========================================="
echo ""
echo "View logs:"
echo "  kubectl logs -n insurance-rag -l component=application -f"
echo ""
echo "View PostgreSQL logs:"
echo "  kubectl logs -n insurance-rag -l component=database -f"
echo ""
echo "Check pod status:"
echo "  kubectl get pods -n insurance-rag"
echo ""
echo "Describe pod:"
echo "  kubectl describe pod -n insurance-rag <pod-name>"
echo ""
echo "Execute command in pod:"
echo "  kubectl exec -it -n insurance-rag <pod-name> -- /bin/bash"
echo ""
echo "Delete all resources:"
echo "  kubectl delete namespace insurance-rag"
echo ""

print_success "Deployment script completed!"
