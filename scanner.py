import cv2
import numpy as np

class DocumentScanner:
    """
    OpenCV Document Scanner Engine.
    Handles edge detection, contour finding, 4-point perspective warp, 
    auto-deskewing, and high-quality document readability enhancements.
    """
    
    @staticmethod
    def order_points(pts):
        """
        Orders coordinates in top-left, top-right, bottom-right, bottom-left sequence.
        pts: numpy array of shape (4, 2)
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Top-left has smallest sum; bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right has smallest difference (y - x); bottom-left has largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    @staticmethod
    def four_point_transform(image, pts):
        """
        Applies 4-point perspective transform to extract rectangular document.
        """
        rect = DocumentScanner.order_points(pts)
        (tl, tr, br, bl) = rect
        
        # Compute maximum width of the new warped document
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        # Compute maximum height of the new warped document
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Ensure non-zero dimensions
        maxWidth = max(maxWidth, 100)
        maxHeight = max(maxHeight, 100)
        
        # Destination coordinates for flat top-down view
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Calculate Perspective Transform Matrix and apply warp
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped

    @staticmethod
    def detect_document(image):
        """
        Detects document boundaries and performs perspective transform.
        Returns: (warped_image, boundary_contour_found)
        """
        orig = image.copy()
        height, width = image.shape[:2]
        
        # Resize image for faster contour processing while preserving aspect ratio
        ratio = height / 500.0
        resized = cv2.resize(image, (int(width / ratio), 500))
        
        # 1. Grayscale Conversion
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # 2. Gaussian Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Canny Edge Detection
        edged = cv2.Canny(blurred, 75, 200)
        
        # Dilate edges slightly to close small gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edged = cv2.dilate(edged, kernel, iterations=1)
        
        # 4. Find contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        doc_contour = None
        
        # 5. Approximate polygon to find 4-corner document contour
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            # If our approximated contour has 4 points, assume document page
            if len(approx) == 4:
                # Ensure contour takes up at least 20% of total image area
                if cv2.contourArea(c) > (resized.shape[0] * resized.shape[1] * 0.20):
                    doc_contour = approx
                    break
        
        if doc_contour is not None:
            # Rescale points back to original image scale
            pts = doc_contour.reshape(4, 2) * ratio
            warped = DocumentScanner.four_point_transform(orig, pts)
            return warped, True
        else:
            # Return full original image cleanly without harsh center-cropping
            return orig, False

    @staticmethod
    def auto_rotate(image):
        """
        Detects document skew angle and rotates image to upright position.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        
        # Threshold image
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Get coordinates of all non-zero pixels
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return image
            
        # Get minimum area bounding box and skew angle
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Ignore negligible angles
        if abs(angle) < 0.5 or abs(angle) > 45:
            return image
            
        # Rotate image around center
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    @staticmethod
    def enhance_image(image, mode='color', sharpen=True, noise_reduction=False):
        """
        Enhances readable quality of document image.
        Modes: 'color', 'adaptive', 'grayscale', 'otsu', 'none'
        """
        if mode == 'none':
            return image.copy()

        # Ensure base grayscale version exists
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Optional Noise Reduction using Median Blur
        if noise_reduction:
            gray = cv2.medianBlur(gray, 3)

        # Contrast Enhancement via CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)

        if mode == 'adaptive':
            # Adaptive Thresholding (Gaussian C) - clean black and white document view
            processed = cv2.adaptiveThreshold(
                enhanced_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 10
            )
        elif mode == 'otsu':
            # Otsu's Global Thresholding
            _, processed = cv2.threshold(enhanced_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif mode == 'grayscale':
            # High-Contrast Grayscale
            processed = enhanced_gray
        elif mode == 'color':
            # Readable Color Document (Vibrancy & Contrast boost on original color image)
            if len(image.shape) == 3:
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                l_clahe = clahe.apply(l)
                enhanced_lab = cv2.merge((l_clahe, a, b))
                processed = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            else:
                processed = enhanced_gray
        else:
            processed = image.copy()

        # Optional Sharpening Filter
        if sharpen:
            sharpen_kernel = np.array([[0, -1, 0],
                                       [-1, 5, -1],
                                       [0, -1, 0]], dtype=np.float32)
            processed = cv2.filter2D(processed, -1, sharpen_kernel)

        return processed
