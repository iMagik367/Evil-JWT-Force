import pytesseract
import cv2


def extract_from_pix_qr(image_path):
    """Extrai texto de QR Code ou Pix Copia-e-Cola via OCR"""
    # Carrega a imagem
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
    # Converte para escala de cinza para melhorar OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text.strip() 