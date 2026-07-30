/* ==========================================================================
   OCR & Document Scanner Application JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initDropzone();
    initWebcam();
    initCopyText();
    initFormSpinner();
});

/**
 * Dark Mode Theme Toggle
 */
function initThemeToggle() {
    const themeBtn = document.getElementById('themeToggleBtn');
    if (!themeBtn) return;

    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', currentTheme);
    updateThemeIcon(currentTheme);

    themeBtn.addEventListener('click', () => {
        const activeTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    if (theme === 'dark') {
        icon.className = 'bi bi-sun-fill text-warning';
    } else {
        icon.className = 'bi bi-moon-stars-fill text-primary';
    }
}

/**
 * Drag & Drop File Upload and Live Preview
 */
function initDropzone() {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('document');
    const previewContainer = document.getElementById('previewContainer');
    const previewImg = document.getElementById('imagePreview');
    const fileNameDisplay = document.getElementById('fileNameDisplay');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', (e) => {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFilePreview(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            handleFilePreview(fileInput.files[0]);
        }
    });

    function handleFilePreview(file) {
        if (fileNameDisplay) {
            fileNameDisplay.textContent = `Selected: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        }

        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                if (previewImg) previewImg.src = e.target.result;
                if (previewContainer) previewContainer.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        } else if (file.type === 'application/pdf') {
            if (previewImg) previewImg.src = 'https://cdn-icons-png.flaticon.com/512/337/337946.png';
            if (previewContainer) previewContainer.classList.remove('d-none');
        }
    }
}

/**
 * HTML5 Webcam Stream and Capture (Handles multiple sequential captures cleanly)
 */
let webcamStream = null;

function initWebcam() {
    const startWebcamBtn = document.getElementById('startWebcamBtn');
    const captureWebcamBtn = document.getElementById('captureWebcamBtn');
    const stopWebcamBtn = document.getElementById('stopWebcamBtn');
    const webcamVideo = document.getElementById('webcamVideo');
    const webcamCanvas = document.getElementById('webcamCanvas');
    const webcamModal = document.getElementById('webcamModal');

    if (!startWebcamBtn || !webcamVideo) return;

    async function startCamera() {
        if (webcamStream) return;
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } 
            });
            webcamVideo.srcObject = webcamStream;
            await webcamVideo.play();
            if (captureWebcamBtn) captureWebcamBtn.disabled = false;
        } catch (err) {
            showToast('Camera Error', 'Unable to access camera: ' + err.message, 'danger');
        }
    }

    startWebcamBtn.addEventListener('click', startCamera);

    // Also auto-start when Bootstrap modal opens
    if (webcamModal) {
        webcamModal.addEventListener('shown.bs.modal', startCamera);
        webcamModal.addEventListener('hidden.bs.modal', stopWebcamStream);
    }

    if (captureWebcamBtn) {
        captureWebcamBtn.addEventListener('click', () => {
            if (!webcamVideo || !webcamVideo.videoWidth || webcamVideo.videoWidth === 0) {
                showToast('Camera Notice', 'Camera frame is initializing. Please wait a second and press Capture again.', 'warning');
                return;
            }

            const context = webcamCanvas.getContext('2d');
            webcamCanvas.width = webcamVideo.videoWidth;
            webcamCanvas.height = webcamVideo.videoHeight;
            context.drawImage(webcamVideo, 0, 0, webcamCanvas.width, webcamCanvas.height);
            
            // Compress JPEG at 85% quality
            const imageDataUrl = webcamCanvas.toDataURL('image/jpeg', 0.85);
            
            // Verify image payload is not empty
            if (!imageDataUrl || imageDataUrl.length < 500) {
                showToast('Capture Error', 'Failed to grab camera frame. Please try again.', 'warning');
                return;
            }

            stopWebcamStream();
            
            // Close camera modal
            if (webcamModal) {
                const bsModal = bootstrap.Modal.getInstance(webcamModal);
                if (bsModal) bsModal.hide();
            }
            
            const colorModeSelect = document.getElementById('webcamColorMode');
            const selectedMode = colorModeSelect ? colorModeSelect.value : 'color';

            showLoadingOverlay("Processing Camera Document & Generating PDF...");
            
            fetch('/api/webcam-upload', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    image: imageDataUrl,
                    mode: selectedMode,
                    language: 'eng+hin'
                })
            })
            .then(res => res.json())
            .then(data => {
                hideLoadingOverlay();
                if (data.success && data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    showToast('Scan Notice', data.error || 'Failed to process camera capture.', 'warning');
                }
            })
            .catch(err => {
                hideLoadingOverlay();
                showToast('Scan Error', 'Network error: ' + err.message, 'danger');
            });
        });
    }

    if (stopWebcamBtn) {
        stopWebcamBtn.addEventListener('click', stopWebcamStream);
    }
}

function stopWebcamStream() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    const webcamVideo = document.getElementById('webcamVideo');
    if (webcamVideo) {
        webcamVideo.srcObject = null;
    }
}

/**
 * Copy Extracted Text to Clipboard
 */
function initCopyText() {
    const copyBtn = document.getElementById('copyTextBtn');
    const textElement = document.getElementById('extractedTextContent');

    if (!copyBtn || !textElement) return;

    copyBtn.addEventListener('click', () => {
        const textToCopy = textElement.innerText || textElement.textContent;
        if (!textToCopy.trim()) {
            showToast('Copy Notice', 'No text available to copy.', 'warning');
            return;
        }

        navigator.clipboard.writeText(textToCopy).then(() => {
            showToast('Copied!', 'Extracted text successfully copied to clipboard.', 'success');
        }).catch(err => {
            showToast('Error', 'Failed to copy text: ' + err, 'danger');
        });
    });
}

/**
 * Spinner Loading Overlay
 */
function initFormSpinner() {
    const uploadForm = document.getElementById('documentUploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', () => {
            showLoadingOverlay("Enhancing Document & Extracting Text...");
        });
    }
}

function showLoadingOverlay(message = "Processing...") {
    const overlay = document.getElementById('loadingOverlay');
    const msgElement = document.getElementById('loadingMessage');
    if (msgElement) msgElement.textContent = message;
    if (overlay) overlay.classList.add('active');
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}

/**
 * Dynamic Toast Alert Trigger
 */
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const bgClass = type === 'success' ? 'bg-success text-white' : 
                    type === 'danger' ? 'bg-danger text-white' : 
                    type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white';

    const toastHtml = `
        <div class="toast align-items-center ${bgClass} border-0 shadow" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong>: ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    const template = document.createElement('div');
    template.innerHTML = toastHtml.trim();
    const toastEl = template.firstChild;
    toastContainer.appendChild(toastEl);

    const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
    bsToast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}
