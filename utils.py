import os
import cv2
import numpy as np
from PIL import Image
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from config import Config

def ensure_directories():
    """Create uploads, processed, downloads, and tessdata directories if missing."""
    for folder in [Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER, Config.DOWNLOAD_FOLDER, Config.TESSDATA_DIR]:
        os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    """Check if uploaded filename has valid extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def validate_image_file(file_path):
    """Verify image file can be successfully opened and is not corrupted."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def process_pdf_input(pdf_path):
    """
    Converts the first page of a PDF file to a high-resolution PNG image.
    Uses pypdfium2 as primary zero-dependency renderer, falling back to pdf2image.
    """
    # 1. Primary Method: pypdfium2 (Pure Python, no poppler executable required)
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        if len(pdf) > 0:
            page = pdf[0]
            # Render page at high resolution 300 DPI (scale=3)
            image = page.render(scale=3).to_pil()
            output_filename = os.path.splitext(os.path.basename(pdf_path))[0] + "_pdf_page1.png"
            output_path = os.path.join(Config.UPLOAD_FOLDER, output_filename)
            image.save(output_path, "PNG")
            return output_path
    except Exception as e:
        print(f"pypdfium2 conversion attempt error: {e}")

    # 2. Secondary Method: pdf2image
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        if images:
            output_filename = os.path.splitext(os.path.basename(pdf_path))[0] + "_pdf_page1.png"
            output_path = os.path.join(Config.UPLOAD_FOLDER, output_filename)
            images[0].save(output_path, "PNG")
            return output_path
    except Exception as e:
        print(f"pdf2image fallback conversion error: {e}")
        
    return None

def generate_pdf_export(image_path, text_content, output_path):
    """
    Generates a PDF document containing the scanned document image 
    and formatted extracted text using ReportLab.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#0D6EFD"),
        spaceAfter=12,
        alignment=0
    )
    
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#212529"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    text_style = ParagraphStyle(
        'ExtractedBodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#333333")
    )
    
    # Header
    story.append(Paragraph("Scanned Document & OCR Report", title_style))
    story.append(Spacer(1, 10))
    
    # Include Image if available
    if image_path and os.path.exists(image_path):
        try:
            story.append(Paragraph("Scanned Document View", section_style))
            img = Image.open(image_path)
            w, h = img.size
            max_w, max_h = 480.0, 320.0
            scale = min(max_w / w, max_h / h)
            img_w, img_h = w * scale, h * scale
            
            story.append(RLImage(image_path, width=img_w, height=img_h))
            story.append(Spacer(1, 15))
        except Exception as e:
            print(f"Error adding image to PDF: {e}")
            
    # Include Extracted Text
    story.append(Paragraph("Extracted Text Content", section_style))
    story.append(Spacer(1, 6))
    
    if text_content and text_content.strip():
        formatted_text = text_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        story.append(Paragraph(formatted_text, text_style))
    else:
        story.append(Paragraph("<i>No readable text was extracted from this document.</i>", text_style))
        
    doc.build(story)
    return output_path

def generate_txt_export(text_content, output_path):
    """Saves extracted text to a .txt file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text_content if text_content else "")
    return output_path
