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
   - Replace the `google_api_key` variable in `app.py` with your key

## Usage

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
