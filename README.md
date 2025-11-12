# Invoice Reader App

A modern web application that extracts structured data from invoice images using OCR (Optical Character Recognition) and AI-powered text analysis.

## Features

- 🖼️ **Image Upload**: Drag & drop or click to upload invoice images
- 🔍 **OCR Processing**: Uses Tesseract OCR to extract text from images
- 🤖 **AI Analysis**: Uses Google's Gemini AI to structure the extracted data
- 📊 **JSON Output**: Returns structured invoice data in JSON format
- 🎨 **Modern UI**: Beautiful, responsive web interface
- 📱 **Mobile Friendly**: Works on all devices

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system
- Google AI API key

## Installation

1. **Clone or download the project files**

2. **Install Tesseract OCR**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up Google AI API**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Create a `.env` file in the project root:
     ```bash
     GOOGLE_API_KEY=your_api_key_here
     ```

## Usage

### Option 1: Docker Compose (Recommended)

1. **Start the application**:
   ```bash
   podman-compose up -d
   # or with docker
   docker-compose up -d
   ```

2. **Check container status**:
   ```bash
   podman-compose ps
   ```

3. **Open your browser** and go to `http://localhost:8501`

4. **Upload and process invoices** through the Streamlit interface

5. **View logs** (if needed):
   ```bash
   podman-compose logs -f
   ```

6. **Stop the application**:
   ```bash
   podman-compose down
   ```

### Option 2: Local Python

1. **Start the application**:
   ```bash
   python invoice.py
   ```

2. **Open your browser** and go to `http://localhost:5000`

3. **Upload an invoice image**:
   - Drag and drop an image file onto the upload area
   - Or click the upload area to browse and select a file

4. **Extract data**:
   - Click the "Extract Invoice Data" button
   - Wait for processing (this may take a few moments)
   - View the structured JSON output

## API Endpoints

- `GET /` - Main application interface
- `POST /upload` - Upload and process image (returns grayscale conversion status)
- `POST /details` - Extract and structure invoice data (returns JSON)

## Supported Image Formats

- JPEG/JPG
- PNG
- BMP
- TIFF
- GIF

## Docker Compose Commands

### Basic Operations
```bash
# Start containers in detached mode
podman-compose up -d

# Start with rebuild
podman-compose up -d --build

# Check container status
podman-compose ps

# View logs (all containers)
podman-compose logs -f

# View logs (specific service)
podman-compose logs -f rag-app
podman-compose logs -f postgres

# Stop containers
podman-compose down

# Stop and remove volumes (⚠️ DELETES ALL DATA)
podman-compose down -v
```

### Troubleshooting
```bash
# Restart a specific service
podman-compose restart rag-app

# Remove corrupted PostgreSQL data
podman-compose down
rm -rf ./data/postgres/pgdata
podman-compose up -d

# View container resource usage
podman stats

# Access PostgreSQL shell
podman exec -it insurance-postgres psql -U postgres -d insurance_rag
```

## Output Format

The application returns structured JSON data containing:
- Invoice number
- Date
- Vendor information
- Customer information
- Line items
- Totals
- Tax information
- And other relevant invoice fields

## Troubleshooting

### Common Issues

1. **Tesseract not found**:
   - Ensure Tesseract is installed and in your system PATH
   - On Windows, you may need to add the Tesseract installation directory to PATH

2. **Google API errors**:
   - Verify your API key is correct
   - Check your API quota and billing status
   - Ensure the API key has access to Gemini models

3. **Image processing errors**:
   - Try with a clearer, higher resolution image
   - Ensure the image contains readable text
   - Check that the image format is supported

### Performance Tips

- Use high-quality, well-lit images for better OCR results
- Ensure text in the image is clear and not blurry
- For large images, consider resizing them before upload

## Security Notes

- The API key is currently hardcoded in the application
- For production use, consider using environment variables
- Never commit API keys to version control

## License

This project is for educational and personal use. Please ensure you comply with Google's API terms of service.

## Kubernetes Deployment

### Prerequisites
- `kubectl` installed
- `kind` (Kubernetes in Docker) installed
- `podman` or `docker` installed

### Quick Start Commands

#### 1. Start the Cluster
```bash
kind create cluster --name insurance-rag
```

#### 2. Deploy the Application
```bash
./deploy-k8s.sh
```

#### 3. Access the Application
```bash
kubectl port-forward -n insurance-rag svc/rag-app-service 8501:8501
```
Then open http://localhost:8501 in your browser.

---

### Management Commands

#### Check Pod Status
```bash
kubectl get pods -n insurance-rag
```

#### View Application Logs
```bash
# Current logs
kubectl logs -n insurance-rag -l component=application --tail=100 -f

# Previous pod logs (if crashed)
kubectl logs -n insurance-rag deployment/rag-app-deployment --previous
```

#### Check PostgreSQL Logs
```bash
kubectl logs -n insurance-rag -l component=database --tail=50
```

#### Verify Services
```bash
kubectl get svc -n insurance-rag
```

#### Check Storage Volumes
```bash
kubectl get pvc -n insurance-rag
```

#### Restart Deployment (if needed)
```bash
kubectl rollout restart deployment/rag-app-deployment -n insurance-rag
```

#### Stop Port Forwarding
Press `Ctrl+C` in the terminal where port-forward is running

#### Delete the Cluster (cleanup)
```bash
kind delete cluster --name insurance-rag
```

For detailed deployment instructions, see [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md).

---

## Contributing

Feel free to submit issues and enhancement requests! 

``` 
