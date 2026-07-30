# Production Dockerfile for OCR & Document Scanner Web Application
FROM python:3.11-slim

# Install system dependencies: OpenCV C++ libraries, Tesseract OCR, Hindi & English models
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement definitions and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application files
COPY . .

# Expose port
EXPOSE 5050

# Run with Gunicorn WSGI Server
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "app:app"]
