import os
import uuid
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from config import Config
from forms import DocumentUploadForm, ContactForm
from scanner import DocumentScanner
from ocr import OCREngine
from utils import (
    ensure_directories, allowed_file, validate_image_file, 
    process_pdf_input, generate_pdf_export, generate_txt_export
)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload, processed, and download storage directories exist
ensure_directories()

# In-memory session store for scan results (id -> result_dict)
SCAN_STORE = {}

@app.context_processor
def inject_globals():
    """Make global configuration available across Jinja templates."""
    return {
        'supported_languages': Config.SUPPORTED_LANGUAGES,
        'tesseract_available': OCREngine.is_tesseract_available()
    }

@app.route('/')
def index():
    """Home Page Landing Route."""
    return render_template('index.html')

@app.route('/scanner', methods=['GET'])
def scanner():
    """Scanner Workspace Route."""
    form = DocumentUploadForm()
    # Retrieve recent history from session
    history_ids = session.get('scan_history', [])
    recent_scans = [SCAN_STORE[sid] for sid in history_ids if sid in SCAN_STORE][-5:]
    return render_template('scanner.html', form=form, recent_scans=recent_scans)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle File Uploads and Computer Vision / OCR Processing."""
    form = DocumentUploadForm()
    
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Upload Error: {error}", "danger")
        return redirect(url_for('scanner'))
        
    file = form.document.data
    if not file or file.filename == '':
        flash("No file selected for upload.", "warning")
        return redirect(url_for('scanner'))
        
    if not allowed_file(file.filename):
        flash("Unsupported file format. Please upload JPG, PNG, BMP, TIFF, or PDF.", "danger")
        return redirect(url_for('scanner'))
        
    filename = secure_filename(file.filename)
    scan_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1].lower()
    
    raw_saved_path = os.path.join(Config.UPLOAD_FOLDER, f"{scan_id}_raw{ext}")
    file.save(raw_saved_path)
    
    # Handle PDF files by converting 1st page to PNG
    if ext == '.pdf':
        image_path = process_pdf_input(raw_saved_path)
        if not image_path:
            flash("Failed to extract image from uploaded PDF document.", "danger")
            return redirect(url_for('scanner'))
    else:
        image_path = raw_saved_path
        if not validate_image_file(image_path):
            flash("Uploaded file is corrupted or not a valid image.", "danger")
            return redirect(url_for('scanner'))

    # Load image with OpenCV
    input_image = cv2.imread(image_path)
    if input_image is None:
        flash("Error loading image for processing.", "danger")
        return redirect(url_for('scanner'))

    # 1. Computer Vision Pipeline: Boundary Detection & Perspective Warp
    warped_image, contour_found = DocumentScanner.detect_document(input_image)
    
    # 2. Auto-rotate / Deskew (if requested)
    if form.auto_rotate.data:
        warped_image = DocumentScanner.auto_rotate(warped_image)
        
    # 3. Readability Enhancements & Thresholding
    enhancement_mode = form.enhancement_mode.data
    processed_image = DocumentScanner.enhance_image(
        warped_image,
        mode=enhancement_mode,
        sharpen=form.sharpen.data,
        noise_reduction=form.noise_reduction.data
    )

    # Save processed image to disk
    processed_filename = f"{scan_id}_scanned.png"
    processed_path = os.path.join(Config.PROCESSED_FOLDER, processed_filename)
    cv2.imwrite(processed_path, processed_image)
    
    # Save original preview image
    orig_filename = f"{scan_id}_orig.png"
    orig_path = os.path.join(Config.UPLOAD_FOLDER, orig_filename)
    cv2.imwrite(orig_path, input_image)

    # 4. Perform Tesseract OCR
    ocr_language = form.language.data
    ocr_res = OCREngine.process_ocr(processed_image, lang=ocr_language)

    # Prepare Scan Result Payload
    result_payload = {
        'id': scan_id,
        'filename': filename,
        'orig_filename': orig_filename,
        'scanned_filename': processed_filename,
        'contour_found': contour_found,
        'enhancement_mode': enhancement_mode,
        'language': Config.SUPPORTED_LANGUAGES.get(ocr_language, ocr_language),
        'text': ocr_res.get('text', ''),
        'confidence': ocr_res.get('confidence', 0.0),
        'char_count': ocr_res.get('char_count', 0),
        'word_count': ocr_res.get('word_count', 0),
        'line_count': ocr_res.get('line_count', 0),
        'tesseract_installed': ocr_res.get('tesseract_installed', True),
        'ocr_error': ocr_res.get('error')
    }

    # Store in memory SCAN_STORE & session history
    SCAN_STORE[scan_id] = result_payload
    history = session.get('scan_history', [])
    if scan_id not in history:
        history.append(scan_id)
        session['scan_history'] = history

    flash("Document processed successfully!", "success")
    return redirect(url_for('result', scan_id=scan_id))


@app.route('/api/webcam-upload', methods=['POST'])
def webcam_upload():
    """API endpoint for HTML5 Webcam capture payload (base64 image)."""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
            
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
            
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'error': 'Failed to decode webcam frame'}), 400
            
        scan_id = str(uuid.uuid4())[:8]
        raw_path = os.path.join(Config.UPLOAD_FOLDER, f"{scan_id}_webcam.png")
        cv2.imwrite(raw_path, img)
        
        enhancement_mode = data.get('mode', 'color')
        ocr_language = data.get('language', 'eng+hin')
        
        # Process document with selected color mode pipeline
        warped, contour_found = DocumentScanner.detect_document(img)
        warped = DocumentScanner.auto_rotate(warped)
        processed = DocumentScanner.enhance_image(warped, mode=enhancement_mode, sharpen=True, noise_reduction=False)
        
        processed_filename = f"{scan_id}_scanned.png"
        processed_path = os.path.join(Config.PROCESSED_FOLDER, processed_filename)
        cv2.imwrite(processed_path, processed)
        
        orig_filename = f"{scan_id}_orig.png"
        orig_path = os.path.join(Config.UPLOAD_FOLDER, orig_filename)
        cv2.imwrite(orig_path, img)
        
        # Execute OCR with bilingual support
        ocr_res = OCREngine.process_ocr(processed, lang=ocr_language)
        
        result_payload = {
            'id': scan_id,
            'filename': 'Camera_Capture.png',
            'orig_filename': orig_filename,
            'scanned_filename': processed_filename,
            'contour_found': contour_found,
            'enhancement_mode': enhancement_mode,
            'language': Config.SUPPORTED_LANGUAGES.get(ocr_language, ocr_language),
            'text': ocr_res.get('text', ''),
            'confidence': ocr_res.get('confidence', 0.0),
            'char_count': ocr_res.get('char_count', 0),
            'word_count': ocr_res.get('word_count', 0),
            'line_count': ocr_res.get('line_count', 0),
            'tesseract_installed': ocr_res.get('tesseract_installed', True),
            'ocr_error': ocr_res.get('error')
        }
        
        SCAN_STORE[scan_id] = result_payload
        history = session.get('scan_history', [])
        if scan_id not in history:
            history.append(scan_id)
            session['scan_history'] = history
            
        return jsonify({
            'success': True,
            'redirect_url': url_for('result', scan_id=scan_id)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/result/<scan_id>')
def result(scan_id):
    """OCR and Document Scan Result Dashboard Route."""
    scan_data = SCAN_STORE.get(scan_id)
    if not scan_data:
        flash("Scan result not found or expired.", "warning")
        return redirect(url_for('scanner'))
        
    return render_template('result.html', result=scan_data)


@app.route('/download/<file_type>/<scan_id>')
def download(file_type, scan_id):
    """Download handler for Scanned Image, TXT, or ReportLab PDF."""
    scan_data = SCAN_STORE.get(scan_id)
    if not scan_data:
        flash("Requested file was not found.", "danger")
        return redirect(url_for('scanner'))
        
    text_content = scan_data.get('text', '')
    scanned_image_path = os.path.join(Config.PROCESSED_FOLDER, scan_data['scanned_filename'])
    
    if file_type == 'image':
        return send_from_directory(
            Config.PROCESSED_FOLDER, 
            scan_data['scanned_filename'], 
            as_attachment=True,
            download_name=f"scanned_doc_{scan_id}.png"
        )
    elif file_type == 'txt':
        txt_filename = f"extracted_text_{scan_id}.txt"
        txt_path = os.path.join(Config.DOWNLOAD_FOLDER, txt_filename)
        generate_txt_export(text_content, txt_path)
        return send_from_directory(
            Config.DOWNLOAD_FOLDER,
            txt_filename,
            as_attachment=True,
            download_name=txt_filename
        )
    elif file_type == 'pdf':
        pdf_filename = f"scanned_report_{scan_id}.pdf"
        pdf_path = os.path.join(Config.DOWNLOAD_FOLDER, pdf_filename)
        generate_pdf_export(scanned_image_path, text_content, pdf_path)
        return send_from_directory(
            Config.DOWNLOAD_FOLDER,
            pdf_filename,
            as_attachment=True,
            download_name=pdf_filename
        )
    else:
        flash("Invalid download request type.", "warning")
        return redirect(url_for('result', scan_id=scan_id))


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded raw preview image files."""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@app.route('/processed/<filename>')
def serve_processed(filename):
    """Serve processed scanned document image files."""
    return send_from_directory(Config.PROCESSED_FOLDER, filename)


@app.route('/about')
def about():
    """About Page Route."""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Page Route."""
    form = ContactForm()
    if form.validate_on_submit():
        flash("Thank you for your message! Our team will get back to you shortly.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)


# Custom Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', content="<div class='container py-5 text-center'><h2>404 - Page Not Found</h2><p>The requested URL was not found on this server.</p><a href='/' class='btn btn-primary mt-3'>Back to Home</a></div>"), 404

@app.errorhandler(413)
def request_entity_too_large(e):
    flash("Uploaded file exceeds the maximum 16MB limit.", "danger")
    return redirect(url_for('scanner'))

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('base.html', content="<div class='container py-5 text-center'><h2>500 - Internal Server Error</h2><p>An unexpected server error occurred.</p><a href='/' class='btn btn-primary mt-3'>Back to Home</a></div>"), 500

if __name__ == '__main__':
    print(f"Starting OCR & Document Scanner Web Application...")
    print(f"Tesseract binary detected: {OCREngine.is_tesseract_available()}")
    app.run(debug=True, host='0.0.0.0', port=5050)
