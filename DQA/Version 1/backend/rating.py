import fitz  # PyMuPDF for PDF extraction
import google.generativeai as genai
import os
from dotenv import load_dotenv


load_dotenv()

# Initialize Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text

def validate_system_rating(pdf_path):
    """Validate the DC system rating using Gemini."""
    text = extract_text_from_pdf(pdf_path)

    prompt = f"""
        Extract the **newly installed** number of solar modules (ignore existing ones) 
        and the stated DC system rating (kWDC) from the following document text also extract the stated AC system rating (kWAC).

        The new modules should be explicitly listed as "new" or separate from "existing".

        Then, calculate the expected kWDC using:
        Expected kWDC = (Newly Installed Number of Modules × 445) / 1000
        Also calculate Efficiency = (AC System Rating / DC System Rating) * 100

        Compare the expected kWDC with the stated kWDC and return:
        - "✅ System rating is correct: X.XXX kWDC" if they match.
        - "⚠️ Discrepancy found! Stated: X.XXX kWDC, Calculated: Y.YYY kWDC" if they don't.
        - Also show the formulas and calculations used.
        - Also show the Efficiency calculated according to the AC sytem rating.

    Document Text:
    {text}
    """
    model = genai.GenerativeModel('gemini-1.5-pro-002')
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1024,
            response_mime_type="application/json"
        )
    )
    return response.text.strip()

# Example usage
pdf_path = "C:\\Users\\Admin\\Downloads\\Machuca, Naomi-1.pdf"
result = validate_system_rating(pdf_path)
print(result)
