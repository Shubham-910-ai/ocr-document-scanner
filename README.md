# OCR and Document Scanner Web Application

A production-quality full-stack Computer Vision and Optical Character Recognition (OCR) web application built with **Python 3.11/3.13**, **Flask**, **OpenCV**, **pytesseract**, **Pillow**, **ReportLab**, and **Bootstrap 5**.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-blue)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR%205.0-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

---

## 🌟 Features

- 📸 **Automatic Document Edge Detection**: Finds 4-corner document boundaries using Canny edge detection and contour approximation.
- 📐 **4-Point Perspective Transformation**: Eliminates camera tilt and flattens angled photos into clean top-down rectangular view.
- ⚙️ **Image Readability Enhancements**:
  - Adaptive Gaussian Thresholding (removes shadows & glares)
  - Otsu Binarization
  - Contrast Limited Adaptive Histogram Equalization (CLAHE)
  - Sharpening kernel filter & Median noise reduction
- 🔄 **Auto-Deskew & Orientation**: Automatically detects skew angle and rotates text upright.
- 📝 **Tesseract OCR Engine Integration**:
  - Extracts text in English, Spanish, French, German, and 100+ languages
  - Calculates confidence scores, character counts, word counts, and line metrics
- 📷 **HTML5 Live Webcam Capture**: Scan physical documents directly using laptop/mobile camera.
- 📄 **Multi-Format Export Options**:
  - Download high-res processed image (PNG)
  - Download raw extracted text (TXT)
  - Download formatted PDF document with image & text report (ReportLab)
- 🌓 **Modern Responsive UI**:
  - Light & Dark mode theme persistence
  - Drag and drop file dropzone
  - Glassmorphism design aesthetics
  - Live progress spinners and toast notifications

---

## 📂 Folder Structure

```
OCR-Document-Scanner/
├── app.py              # Main Flask server, routes, webcam API, and session handlers
├── config.py           # Application configuration, file limits, and Tesseract path auto-detection
├── scanner.py          # OpenCV Computer Vision scanner engine (edge detection, warp, filters)
├── ocr.py              # Pytesseract OCR engine wrapper & text confidence analysis
├── utils.py            # PDF conversion, ReportLab PDF generator, TXT export & file validators
├── forms.py            # Flask-WTF validation forms for uploads and contact
├── requirements.txt    # Python package dependencies
├── README.md           # Documentation guide
├── uploads/            # Temporary raw uploaded image files
├── processed/          # Perspective-warped & enhanced document images
├── downloads/          # Generated TXT and PDF export documents
├── static/
│   ├── css/
│   │   └── style.css   # Custom CSS with Glassmorphism and theme variables
│   └── js/
│       └── script.js   # Client-side JS (Drag & drop, webcam, dark mode, toast alerts)
└── templates/
    ├── base.html       # Master layout template (Navbar, Dark mode, Footer)
    ├── index.html      # Landing page (Hero, Features, Workflow)
    ├── scanner.html    # Main scanning workspace (Dropzone & Webcam modal)
    ├── result.html     # Interactive results dashboard (Dual view & Metrics)
    ├── about.html      # Technical computer vision pipeline documentation
    └── contact.html    # Responsive contact form page
```

---

## 🚀 Installation & Setup

### 1. Install Tesseract OCR Engine

To enable live text extraction, install the Tesseract binary on your system:

#### **Windows**
1. Download installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
2. Run installer (default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`).
3. The application automatically detects Tesseract at standard installation paths.

#### **Linux (Ubuntu / Debian)**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng libtesseract-dev poppler-utils
```

#### **macOS**
```bash
brew install tesseract poppler
```

---

### 2. Set Up Virtual Environment & Dependencies

```bash
# Clone repository or navigate to workspace directory
cd OCR-Document-Scanner

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Run the Application

```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📷 Computer Vision Pipeline Overview

```
[Raw Photo/PDF] 
       ↓
[Grayscale Conversion] ──> [Gaussian Blur (5x5)]
       ↓
[Canny Edge Detection (75, 200)]
       ↓
[Find Contours] ──> [Approximate 4-Corner Polygon (approxPolyDP)]
       ↓
[4-Point Perspective Transform (warpPerspective)]
       ↓
[Auto-Deskew & Orientation Adjustment]
       ↓
[Adaptive Thresholding / CLAHE Contrast Boost]
       ↓
[Tesseract OCR Text Extraction & Metric Analysis]
       ↓
[Export: PNG / TXT / Searchable PDF]
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask, Flask-WTF, WTForms, Werkzeug
- **Computer Vision & Image Processing**: OpenCV (`opencv-python-headless`), NumPy, Pillow, imutils
- **OCR**: Tesseract OCR, pytesseract
- **PDF Generation**: ReportLab, pdf2image
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism), JavaScript (ES6), Bootstrap 5.3, Bootstrap Icons

---

## 🔒 Security Measures

- Maximum upload limit enforced at 16MB (`MAX_CONTENT_LENGTH`).
- File extension validation (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.pdf`).
- Pillow image validation prevents execution of malicious or corrupted files.
- CSRF Protection via Flask-WTF tokens.
