import os
import json
import re
import logging
import requests
from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import google.generativeai as genai
from flask_cors import CORS
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API keys
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

if not GEMINI_API_KEY or not PERPLEXITY_API_KEY:
    logger.error("❌ Missing API Key! Check your .env file.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
CORS(app, resources={r"/upload": {"origins": "*"}})  # Allow all origins for /upload

def extract_text_from_pdff(pdf_file) -> Optional[str]:
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(pdf_file)
        extracted_text = "\n".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )
        return extracted_text.strip() if extracted_text.strip() else None
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return None

def extract_structured_data(text: str) -> Optional[Dict[str, Any]]:
    """Extracts structured data from text using Gemini AI."""
    prompt = f"""
    Extract structured data in JSON format:
    {{
      "Solar Module Specifications": {{
        "Manufacturer / Model": "",
        "VMP": "",
        "IMP": "",
        "VOC": "",
        "ISC": "",
        "Temperature Coefficient of VOC": "",
        "PTC Rating": "",
        "Module Dimension": "",
        "Panel Wattage": ""
      }},
      "Inverter Specifications": {{
        "Manufacturer / Model": "",
        "Max DC Short Circuit Current": "",
        "Continuous Output Current": ""
      }},
      "Ambient Temperature Specs": {{
        "Record Low Temp": "",
        "Ambient Temp (High Temp 2%)": "",
        "Conduit Height": "",
        "Roof Top Temp": "",
        "Conductor Temperature Rate": "",
        "Module Temperature Coefficient of VOC": ""
      }}
    }}
    TEXT:
    {text}
    **Output JSON only, no explanation.**
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        json_str = response.text.strip()[response.text.strip().find("{") : response.text.strip().rfind("}") + 1]
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error extracting structured data: {e}")
        return None

def search_with_perplexity(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Searches Perplexity AI for exact matches of extracted data."""
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    api_url = "https://api.perplexity.ai/chat/completions"

    # Construct a precise query for Perplexity
    query = f"""
    Provide detailed technical specifications for the following:
    - Solar Module: {extracted_data.get("Solar Module Specifications", {}).get("Manufacturer / Model", "")}
    - Inverter: {extracted_data.get("Inverter Specifications", {}).get("Manufacturer / Model", "")}
    - Ambient Temperature Specs: {extracted_data.get("Ambient Temperature Specs", {}).get("Record Low Temp", "")}

    Match the following extracted specifications exactly:
    {json.dumps(extracted_data, indent=2)}

    Provide:
    - Exact matches for the extracted specifications.
    - Differences (if any) between the extracted data and the actual specifications.
    - Top 3 reference URLs for verification.
    """

    try:
        response = requests.post(
            api_url, headers=headers, json={"model": "sonar-pro", "messages": [{"role": "user", "content": query}]}
        )
        response_data = response.json()

        if response.status_code == 200:
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            urls = extract_urls_from_text(content)
            return {"summary": content, "top_links": urls[:3] if urls else [], "status": "success"}
        else:
            logger.error(f"Perplexity API error: {response_data}")
            return {"error": f"❌ Perplexity API error: {response_data}", "status": "error"}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": f"❌ Search failed: {e}", "status": "error"}

def extract_urls_from_text(text: str) -> List[str]:
    """Extracts URLs from text using regex."""
    url_pattern = re.compile(r'https?://[^\s()<>]+(?:\.[^\s()<>]+)+(?:\([^\s()<>]*\)|[^\s`!()\[\]{};:\'".,<>?«»""''])*')
    return url_pattern.findall(text)

def compare_extracted_with_web_data(extracted_data: Dict[str, Any], web_summary: str) -> Dict[str, Any]:
    """Compares extracted data with web search results and identifies matches/mismatches."""
    comparison_report = {}

    # Compare each section
    for section, specs in extracted_data.items():
        comparison_report[section] = []
        for key, extracted_value in specs.items():
            # Check if the extracted value exists in the web summary
            if extracted_value and str(extracted_value).lower() in web_summary.lower():
                status = "✅ Match"
                validated_value = extracted_value  # Assume the web summary confirms the extracted value
            else:
                status = "❌ Mismatch"
                validated_value = "Not found"  # Placeholder for mismatched values

            # Add the comparison result to the report
            comparison_report[section].append({
                "Specification": key,
                "Extracted Data Value": extracted_value,
                "Validated Data from Search": validated_value,
                "Status": status
            })

    return comparison_report

@app.route('/upload', methods=['POST'])
def upload_pdf():
    """API endpoint to upload and process a PDF file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_file = request.files['file']
    extracted_text = extract_text_from_pdff(pdf_file)

    if not extracted_text:
        return jsonify({"error": "Failed to extract text from PDF"}), 400

    structured_data = extract_structured_data(extracted_text)
    if not structured_data:
        return jsonify({"error": "Failed to extract structured data"}), 400

    web_data = search_with_perplexity(structured_data)
    if web_data.get("status") == "error":
        return jsonify({"error": web_data.get("error")}), 500

    comparison_results = compare_extracted_with_web_data(structured_data, web_data["summary"])

    return jsonify({
        "structured_data": structured_data,
        "web_data": web_data,
        "comparison_results": comparison_results
    })

if __name__ == '__main__':
    app.run(debug=True)