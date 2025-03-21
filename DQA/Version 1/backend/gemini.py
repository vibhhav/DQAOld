import fitz  # PyMuPDF for PDF text extraction
import json
import re
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import requests
load_dotenv()

# Configure Gemini API client
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------------------- PDF TEXT EXTRACTION ----------------------

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a PDF file."""
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text("text") for page in doc)

# ---------------------- JSON HANDLING & NORMALIZATION ----------------------

def clean_json_output(text):
    """Extracts valid JSON from LLM output using regex."""
    match = re.search(r"\{.*\}", text, re.DOTALL)  # Find JSON block
    if match:
        try:
            return json.loads(match.group())  # Parse JSON
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format"}
    return {"error": "No valid JSON found"}

def normalize_text(text):
    """Converts text to lowercase and removes extra spaces for uniform comparison."""
    return text.lower().strip() if text else ""

# ---------------------- LLM PROCESSING ----------------------

def generate_with_gemini(prompt, retries=3):
    """Calls Gemini API with retries for robustness."""
    model = genai.GenerativeModel('gemini-1.5-pro-002')

    for attempt in range(retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text) if response.text else clean_json_output(response.text)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  # Wait before retrying

    return {"error": "Gemini API failed after multiple attempts"}

def process_text_with_gemini(pdf_path):
    """Extracts structured data from text using Gemini API."""
    text = extract_text_from_pdf(pdf_path)
    prompt = f"""
    You are a helpful assistant that extracts structured data.

    Extract the following details from the document:
    - Company Name
    - Company Address
    - Project Name
    - Project Address
    - Email ID
    - Phone Number
    - Date
    - Sheet Name
    - Sheet Size
    - Sheet Number
    - DC System Size (e.g., "6.230 kWDC")
    - AC System Size (e.g., "4.060 kWAC")

    If a field is missing, return "null" for that field.

    Return only a JSON object with this structure:
    {{
        "company_name": "",
        "company_address": "",
        "project_name": "",
        "project_address": "",
        "email_id": "",
        "phone_number": "",
        "date": "",
        "sheet_name": "",
        "sheet_size": "",
        "sheet_number": "",
        "dc_system_size": "",
        "ac_system_size": ""
    }}

    Extract from the following text:
    {text}
    """
    return generate_with_gemini(prompt)

# ---------------------- SYSTEM RATING VALIDATION ----------------------

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
    return generate_with_gemini(prompt)



def extract_ahj_and_codes(pdf_path):
    """Extracts the AHJ Name and Governing Codes using Gemini AI and enforces JSON output."""
    text = extract_text_from_pdf(pdf_path)
    prompt = f"""
    You are an AI assistant extracting structured data. Extract the AHJ Name and Governing Codes from the provided text.
    Return the response strictly in JSON format **without any extra text**.

    Example output:
    {{
        "AHJ Name": "FARMINGTON CITY",
        "Governing Codes": [
            "2020 NATIONAL ELECTRICAL CODE",
            "2021 INTERNATIONAL FIRE CODE"
        ]
    }}

    Text to extract from:
    {text}

    Ensure the response is valid JSON without any explanations or extra formatting.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-002')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024
            )
        )

        # Ensure response is valid JSON
        extracted_json = response.text.strip()
        if extracted_json.startswith("```json"):  # Handle code block formatting if present
            extracted_json = extracted_json[7:-3].strip()
        
        extracted_data = json.loads(extracted_json)
        return extracted_data

    except json.JSONDecodeError:
        return {"error": "Gemini AI response is not valid JSON. Try refining the prompt."}
    except Exception as e:
        return {"error": str(e)}


def validate_with_perplexity(pdf_path):
    """Validates if the governing codes are correct according to the AHJ name using Perplexity AI."""
    ahj_details = extract_ahj_and_codes(pdf_path)
    ahj_name = ahj_details.get("AHJ Name", "Unknown AHJ")
    governing_codes = ", ".join(ahj_details.get("Governing Codes", []))
    
    query = f"""
    The Authority Having Jurisdiction (AHJ) is "{ahj_name}". The governing codes mentioned are: {governing_codes}.
    
    Are these governing codes correct for this AHJ? Validate based on official sources.
    
    Also, provide a list of **trusted sources** (such as government websites, AHJ official sites, or code authority sites) that confirm the validation wih links.
    
    At the end of your response, return **only 'Correct' or 'Incorrect'**.
    - Return 'Correct' if the governing codes are mostly correct (even if some require confirmation).
    - Return 'Incorrect' **only if** one of the governing code is incorrect.
    """

    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": "Bearer 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"}
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload).json()
        answer = response["choices"][0]["message"]["content"]

        # Extract final 'Yes' or 'No' answer
        yes_no = answer.strip().split()[-1]  # Get the last word
        if yes_no not in ["Yes", "No"]:
            yes_no = "Uncertain"

        return answer, yes_no

    except Exception as e:
        return f"Error: {str(e)}", "Uncertain"




# ---------------------- USAGE ----------------------

if __name__ == "__main__":
    pdf_path = "C:\\Users\\Admin\\DQA\\Version 1\\Plan Sets\\_CAD_ AvaMorales_ML-1.pdf"  # Change this to your actual PDF path
    validation_summary = process_text_with_gemini(pdf_path)
    rating = validate_system_rating(pdf_path)
    ahj = validate_with_perplexity(pdf_path)
    
    print(json.dumps(ahj, indent=4))
    print(json.dumps(rating, indent=4))

    print(json.dumps(validation_summary, indent=4))
