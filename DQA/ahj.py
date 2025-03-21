import fitz  # PyMuPDF
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()

GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

def extract_text_from_pdf(pdf_path):
    """Extracts text from the first page of the PDF."""
    doc = fitz.open(pdf_path)
    text = doc[0].get_text("text")
    return text


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


PDF_PATH = "C:\\Users\\Admin\\Downloads\\Machuca, Naomi-1.pdf"



    # Extract AHJ Name and Governing Codes



def validate_with_perplexity(pdf_path):
    """Validates if the governing codes are correct according to the AHJ name using Perplexity AI."""
    ahj_details = extract_ahj_and_codes(pdf_path)
    ahj_name = ahj_details.get("AHJ Name", "Unknown AHJ")
    governing_codes = ", ".join(ahj_details.get("Governing Codes", []))
    
    query = f"""
    The Authority Having Jurisdiction (AHJ) is "{ahj_name}". The governing codes mentioned are: {governing_codes}.
    
    Are these governing codes correct for this AHJ? Validate based on official sources and provide a brief explanation.
    
    Also, provide a list of **trusted sources** (such as government websites, AHJ official sites, or code authority sites) that confirm the validation.
    
    At the end of your response, return **only 'Yes' or 'No'**.
    - Return 'Yes' if the governing codes are mostly correct (even if some require confirmation).
    - Return 'No' **only if** the governing code is incorrect.
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







if __name__ == "__main__":
    print("Starting...")

    # Extract text from PDF
    validation_result = validate_with_perplexity(PDF_PATH)
    print(validation_result)



