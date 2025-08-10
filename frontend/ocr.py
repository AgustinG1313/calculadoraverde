import pytesseract
from PIL import Image
import tempfile
import re
import os
from typing import List, Dict
from pdf2image import convert_from_path

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Release-24.08.0-0\poppler-24.08.0\Library\bin"  
def pdf_to_img(pdf_path):
    return convert_from_path(pdf_path, poppler_path=r"C:\path\to\poppler-xx\bin")

try:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
except:
    # Si falla, asumimos que está en PATH
    pass
def process_invoice(file_path: str) -> dict:
    try:
        text = ""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            # Convertir PDF usando la ruta especificada
            images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
            for i, image in enumerate(images):
                text += pytesseract.image_to_string(image) + "\n\n"
        else:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
        
        total_kwh = extract_kwh(text)
        desglose = extract_items(text)

        return {
            "total_kwh": total_kwh,
            "desglose": desglose,
            "raw_text": text
        }
    except Exception as e:
        raise ValueError(f"Error al procesar archivo: {str(e)}")

def extract_kwh(text: str) -> int:
    """
    Extrae el consumo de kWh del texto OCR.
    
    Args:
        text (str): Texto extraído por OCR
        
    Returns:
        int: Consumo en kWh (0 si no se encuentra)
    """
    try:
        # Busca patrones como "Consumo: 250 kWh" o "250kWh"
        pattern = re.compile(r"(\d{3,4})\s*kWh?", re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            return int(matches[-1])  # Toma el último match
        
        # Busca números de 3-4 dígitos como fallback
        numbers = re.findall(r"\b\d{3,4}\b", text)
        return int(numbers[-1]) if numbers else 0
    except Exception:
        return 0

def extract_items(text: str) -> List[Dict]:
    """
    Extrae conceptos e importes de la factura.
    
    Args:
        text (str): Texto extraído por OCR
        
    Returns:
        List[Dict]: Lista de items con concepto e importe
    """
    items = []
    try:
        # Patrón mejorado para capturar conceptos e importes
        pattern = re.compile(
            r"([A-Z][A-Z\s]+[A-Z])\s+([\d\.,]+)|"  # Concepto en mayúsculas
            r"(Consumo\s+.+?)\s+([\d\.,]+)|"       # Concepto de consumo
            r"(Total)\s+([\d\.,]+)",               # Total
            re.IGNORECASE
        )
        
        for match in pattern.finditer(text):
            concepto = (match.group(1) or match.group(3) or match.group(5)).strip()
            importe_str = (match.group(2) or match.group(4) or match.group(6))
            importe_str = importe_str.replace(".", "").replace(",", ".")
            
            try:
                importe = float(importe_str)
                items.append({
                    "concepto": concepto,
                    "importe": importe
                })
            except ValueError:
                continue
                
    except Exception as e:
        print(f"Error al extraer items: {str(e)}")
    
    return items