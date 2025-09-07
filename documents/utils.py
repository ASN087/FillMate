import re
from docx import Document
from documents.models import Placeholder
from io import BytesIO
import tempfile  # Import tempfile for temporary file creation
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas  # Import canvas for PDF generation
from PyPDF2 import PdfReader, PdfWriter

def determine_placeholder_type(placeholder_text):
    """Determine if a placeholder is a date or text type."""
    date_keywords = ['date', 'issue_date', 'hearing_date']
    for keyword in date_keywords:
        if keyword in placeholder_text.lower():
            return 'date'
    return 'text'

def extract_example_from_placeholder(placeholder_text):
    """Extract example values from placeholders like <field (eg: example)> or <field (e.g., example)>."""
    match = re.search(r"\((?:e\.g\.|eg:)\s*(.*?)\)", placeholder_text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_placeholders_from_docx(template):
    """
    Extracts placeholders from a DOCX template and saves them in the database.
    Preserves original placeholder text while storing standardized names.
    """
    print(f"🔍 Extracting placeholders from: {template.file.path}")

    doc = Document(template.file.path)
    placeholders = set()

    # Regex pattern to match placeholders and optional examples
    placeholder_pattern = re.compile(r"<(.*?)(?:\s*\((?:e\.g\.|eg:)\s*(.*?)\))?>", re.IGNORECASE)

    for para in doc.paragraphs:
        matches = placeholder_pattern.findall(para.text)
        for match in matches:
            original_text = match[0].strip()
            example_value = match[1].strip() if match[1] else None
            
            # Create standardized name for database
            standardized_name = original_text.lower()
            standardized_name = re.sub(r'[^\w\s]', '', standardized_name)
            standardized_name = standardized_name.replace(' ', '_')
            
            placeholder_type = determine_placeholder_type(standardized_name)
            
            # Store both original and standardized versions
            placeholders.add((
                standardized_name,
                f"<{original_text}>",  # Preserve original formatting
                placeholder_type,
                example_value
            ))

    # Store extracted placeholders in the database
    for name, placeholder_text, p_type, example in placeholders:
        print(f"✅ Saving placeholder: {name} (Text: {placeholder_text}, Type: {p_type}, Example: {example})")
        Placeholder.objects.get_or_create(
            template=template,
            name=name,
            placeholder_text=placeholder_text,  # Original format
            type=p_type,
            example=example
        )
# def convert_docx_to_pdf(docx_file):
#     """
#     Converts DOCX (BytesIO) to PDF (BytesIO) using docx2pdf
#     Preserves ALL original formatting (tables, styles, etc.)
#     """
#     import tempfile
#     import os
#     from docx2pdf import convert

#     try:
#         # 1. Save DOCX to temp file
#         temp_dir = tempfile.gettempdir()
#         temp_docx = os.path.join(temp_dir, f"temp_{os.getpid()}.docx")
#         temp_pdf = temp_docx.replace('.docx', '.pdf')
        
#         with open(temp_docx, 'wb') as f:
#             f.write(docx_file.getvalue())

#         # 2. Convert to PDF
#         convert(temp_docx, temp_pdf)

#         # 3. Read PDF into memory
#         with open(temp_pdf, 'rb') as f:
#             pdf_buffer = BytesIO(f.read())
        
#         return pdf_buffer

#     except Exception as e:
#         raise Exception(f"PDF conversion failed: {str(e)}")
    
#     finally:
#         # 4. Cleanup temp files
#         for fpath in [temp_docx, temp_pdf]:
#             try:
#                 if os.path.exists(fpath):
#                     os.unlink(fpath)
#             except:
#                 pass
##############working code below - convert to pdf
# from docx2pdf import convert
# from io import BytesIO

# def convert_docx_to_pdf(docx_buffer):
#     """Convert a DOCX buffer to a PDF buffer using docx2pdf."""
#     temp_docx_path = "temp.docx"
#     temp_pdf_path = "temp.pdf"

#     # Save DOCX to a temporary file
#     with open(temp_docx_path, "wb") as f:
#         f.write(docx_buffer.getvalue())

#     # Convert DOCX to PDF
#     convert(temp_docx_path, temp_pdf_path)

#     # Read the PDF back into a buffer
#     pdf_buffer = BytesIO()
#     with open(temp_pdf_path, "rb") as f:
#         pdf_buffer.write(f.read())

#     pdf_buffer.seek(0)
#     return pdf_buffer
####convert docx to pdf -keerthi. its below
import pythoncom  # Import for COM initialization
from docx2pdf import convert
from io import BytesIO

def convert_docx_to_pdf(docx_buffer):
    """Convert a DOCX buffer to a PDF buffer using docx2pdf with COM initialization."""
    temp_docx_path = "temp.docx"
    temp_pdf_path = "temp.pdf"

    # Save DOCX to a temporary file
    with open(temp_docx_path, "wb") as f:
        f.write(docx_buffer.getvalue())

    try:
        pythoncom.CoInitialize()  # ✅ Initialize COM to prevent errors
        convert(temp_docx_path, temp_pdf_path)  # Convert DOCX to PDF
    finally:
        pythoncom.CoUninitialize()  # ✅ Uninitialize COM after conversion

    # Read the PDF back into a buffer
    pdf_buffer = BytesIO()
    with open(temp_pdf_path, "rb") as f:
        pdf_buffer.write(f.read())

    pdf_buffer.seek(0)
    return pdf_buffer

def generate_signed_pdf(original_pdf_path, signature_path):
    """
    Professional PDF signing with:
    - PyPDF2 for perfect document preservation
    - Reportlab for precise signature placement
    - Proper resource cleanup
    """
    output_buffer = BytesIO()
    temp_overlay = None  # Track temp files for cleanup
    
    try:
        # 1. Create signature overlay (Reportlab)
        overlay_packet = BytesIO()
        can = canvas.Canvas(overlay_packet, pagesize=letter)
        
        # Signature placement (adjust these values as needed)
        can.drawImage(
            signature_path,
            x=400, y=30,               # Bottom-right coordinates
            width=150, height=50,      # Reasonable signature size
            preserveAspectRatio=True,
            mask='auto'                # Handles transparent PNGs
        )
        can.save()
        
        # 2. Merge with original PDF (PyPDF2)
        original = PdfReader(original_pdf_path)
        signature_overlay = PdfReader(BytesIO(overlay_packet.getvalue())).pages[0]
        output = PdfWriter()
        
        # Add signature only to last page
        for i, page in enumerate(original.pages):
            if i == len(original.pages) - 1:
                page.merge_page(signature_overlay)
            output.add_page(page)
        
        # 3. Output to buffer
        output.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer
        
    except Exception as e:
        raise Exception(f"PDF signing failed: {str(e)}")
    finally:
        # Proper cleanup
        overlay_packet.close() if 'overlay_packet' in locals() else None
        if temp_overlay and os.path.exists(temp_overlay):
            os.unlink(temp_overlay)