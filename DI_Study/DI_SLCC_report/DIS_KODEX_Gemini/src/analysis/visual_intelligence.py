import cv2
import pytesseract
import numpy as np
from PIL import Image
from collections import Counter
from sklearn.cluster import KMeans
import os

class VisualIntelligence:
    def __init__(self):
        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except:
            print("Warning: Tesseract not found. OCR will not work.")

    def extract_text(self, image_path: str) -> str:
        """
        Extracts text from an image using Tesseract OCR.
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return ""
            
            # Preprocessing for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # Run OCR (Korean + English)
            text = pytesseract.image_to_string(thresh, lang='kor+eng')
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def extract_dominant_colors(self, image_path: str, k: int = 3):
        """
        Extracts dominant colors using K-Means clustering.
        Returns list of (R, G, B) tuples.
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return []
            
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.reshape((img.shape[0] * img.shape[1], 3))
            
            clt = KMeans(n_clusters=k)
            clt.fit(img)
            
            colors = clt.cluster_centers_
            return [tuple(map(int, color)) for color in colors]
        except Exception as e:
            print(f"Color Analysis Error: {e}")
            return []

    def analyze_thumbnail(self, image_path: str):
        """
        Performs comprehensive analysis on a thumbnail.
        """
        if not os.path.exists(image_path):
            return {"error": "File not found"}

        return {
            "ocr_text": self.extract_text(image_path),
            "dominant_colors": self.extract_dominant_colors(image_path)
        }

if __name__ == "__main__":
    # Test with a dummy image if exists, or just print init
    vi = VisualIntelligence()
    print("Visual Intelligence Module Initialized")
