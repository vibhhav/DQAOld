from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from gemini import process_text_with_gemini, validate_system_rating, validate_with_perplexity
import fitz  # PyMuPDF
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import json
import re
from typing import Optional, Dict, List, Any
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load environment variables
load_dotenv()

# Configure Gemini API
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

# Google Maps API Key
GOOGLE_MAPS_API_KEY = "AIzaSyCy6gBf2bQI6RYN8E_DWMgp6RIx59_7suU"


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
    headers = {"Authorization": "Bearer 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", "Content-Type": "application/json"}
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



def extract_text_from_pdf(pdf_path):
    """Extracts text from the first page of the PDF."""
    doc = fitz.open(pdf_path)
    text = doc[0].get_text("text")
    return text

def extract_project_address(text):
    """Extracts the project address from the given text using Gemini AI."""
    prompt = f"""
    You are a helpful assistant extracting structured data.
    Extract the **Project Address** in this format:
    Example: 3312 DELANA WAY, ALVA, FL 33920, USA
    Extract from the following text:
    {text}
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
        return response.text.strip()
    except Exception as e:
        return str(e)

def get_lat_long(address):
    """Converts an address to latitude and longitude using the Google Geocoding API."""
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(geocode_url).json()
    
    if response["status"] == "OK":
        location = response["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        raise Exception(f"Failed to get location. Response: {response}")

def get_map_image(lat, lng, map_type="roadmap", zoom=21, size="600x600", filename="map_image.png"):
    """Downloads a static map image from Google Maps based on latitude and longitude."""
    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size={size}&maptype={map_type}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(map_url, stream=True)
    
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filename
    else:
        raise Exception(f"Failed to download map image. Status code: {response.status_code}")

def extract_images_from_pdf(pdf_path, page_num=0):
    """Extracts images from the specified page of the PDF."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    images = []
    
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        img_bytes = base_image["image"]
        img_ext = base_image["ext"]
        
        img_filename = f"uploads/extracted_image_{img_index}.{img_ext}"
        with open(img_filename, "wb") as img_file:
            img_file.write(img_bytes)
        
        images.append(img_filename)
    
    return images

def classify_pdf_images(image_paths):
    """Identify which images are maps or satellite views using Gemini Vision."""
    model = genai.GenerativeModel('gemini-1.5-pro-002')
    results = {"map_views": [], "satellite_views": [], "other": []}
    
    for img_path in image_paths:
        try:
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            image_parts = [{"mime_type": "image/jpeg", "data": img_data}]
            prompt = """
            Examine this image and classify it into ONE of these categories:
            1. Map View (roadmap, street map)
            2. Satellite View (aerial imagery)
            3. Other (not a map or satellite image)
            
            Respond with ONLY the category name.
            """
            
            response = model.generate_content(
                [prompt, *image_parts],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=50
                )
            )
            
            classification = response.text.strip().lower()
            if "map" in classification or "roadmap" in classification or "street map" in classification:
                results["map_views"].append(img_path)
            elif "satellite" in classification or "aerial" in classification:
                results["satellite_views"].append(img_path)
            else:
                results["other"].append(img_path)
                
        except Exception as e:
            results["other"].append(img_path)
    
    return results

def validate_map_location(pdf_map_path, address, google_map_path):
    """Validate if the PDF map is showing the correct location based on the address."""
    model = genai.GenerativeModel('gemini-1.5-pro-002')

    with open(pdf_map_path, "rb") as f1, open(google_map_path, "rb") as f2:
        pdf_img_data = f1.read()
        google_img_data = f2.read()

    image_parts = [
        {"mime_type": "image/jpeg", "data": pdf_img_data},
        {"mime_type": "image/jpeg", "data": google_img_data}
    ]

    prompt = f"""
    Task: Validate whether the extracted map or satellite image from the PDF matches the Google Maps reference image.

    **Project Address:** {address}

    ### Instructions:
    - Ignore minor color changes, shadows, and small object variations.
    - Focus on street layouts (for maps) and building placement (for satellite views).
    - Provide a structured response strictly in the format below.

    ### **Response Format (Strictly Follow This)**
    ```
    Map View Match: [0-100]%
    Satellite View Match: [0-100]%
    Key Differences: 
    - [List major differences]
    Key Similarities: 
    - [List strong matching features]
    Confidence Level: [High/Medium/Low]
    Conclusion: [Short summary of findings]
    ```
    """

    response = model.generate_content([prompt, *image_parts])
    return response.text

def extract_validation_results(response_text):
    """Parses Gemini's response to extract structured validation results."""
    lines = response_text.split("\n")
    
    def get_value(label, default="Unknown"):
        for line in lines:
            if line.lower().startswith(label.lower()):
                value = line.split(":")[-1].strip()
                return value if value else default
        return default

    return {
        "Map Match (%)": get_value("Map View Match"),
        "Satellite Match (%)": get_value("Satellite View Match"),
        "Key Differences": get_value("Key Differences", "Not provided"),
        "Key Similarities": get_value("Key Similarities", "Not provided"),
        "Confidence": get_value("Confidence Level"),
        "Conclusion": get_value("Conclusion", "Not provided"),
    }

def validate_location(pdf_path):
    """Full location validation process for a PDF file."""
    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Extract project address from text
        project_address = extract_project_address(pdf_text)
        
        # Get latitude and longitude
        try:
            lat, lng = get_lat_long(project_address)
            coordinates = {"latitude": lat, "longitude": lng}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get coordinates: {str(e)}",
                "address": project_address
            }
        
        # Extract images from the PDF
        extracted_images = extract_images_from_pdf(pdf_path)
        
        # Classify which extracted images are maps or satellite views
        classified_images = classify_pdf_images(extracted_images)
        
        # Download reference maps from Google Maps
        google_map_file = "uploads/google_map_view.png"
        google_satellite_file = "uploads/google_satellite_view.png"
        
        map_file = get_map_image(lat, lng, map_type="roadmap", zoom=13, size="400x400", filename=google_map_file)
        satellite_file = get_map_image(lat, lng, map_type="satellite", zoom=21, filename=google_satellite_file)
        
        # Validate maps from PDF against Google Maps
        validation_results = {
            "map_validations": [],
            "satellite_validations": []
        }
        
        # Validate map views
        if classified_images["map_views"]:
            for i, map_path in enumerate(classified_images["map_views"]):
                result_text = validate_map_location(map_path, project_address, google_map_file)
                parsed_result = extract_validation_results(result_text)
                
                validation_results["map_validations"].append({
                    "pdf_image": map_path,
                    "google_image": google_map_file,
                    "results": parsed_result
                })

        # Validate satellite views
        if classified_images["satellite_views"]:
            for i, sat_path in enumerate(classified_images["satellite_views"]):
                result_text = validate_map_location(sat_path, project_address, google_satellite_file)
                parsed_result = extract_validation_results(result_text)
                
                validation_results["satellite_validations"].append({
                    "pdf_image": sat_path,
                    "google_image": google_satellite_file,
                    "results": parsed_result
                })
        
        return {
            "success": True,
            "address": project_address,
            "coordinates": coordinates,
            "reference_maps": {
                "map": google_map_file,
                "satellite": google_satellite_file
            },
            "extracted_images": {
                "map_views": classified_images["map_views"],
                "satellite_views": classified_images["satellite_views"],
                "other": classified_images["other"]
            },
            "validation_results": validation_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.route("/validate-pdf", methods=["POST"])
def validate_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    file.save(file_path)  # Save the uploaded file

    
    extracted_text = extract_text_from_pdff(file)

    if not extracted_text:
        return jsonify({"error": "Failed to extract text from PDF"}), 400

    structured_data = extract_structured_data(extracted_text)
    if not structured_data:
        return jsonify({"error": "Failed to extract structured data"}), 400

    web_data = search_with_perplexity(structured_data)
    if web_data.get("status") == "error":
        return jsonify({"error": web_data.get("error")}), 500

    comparison_results = compare_extracted_with_web_data(structured_data, web_data["summary"])
    # Run all validation functions
    extracted_data = process_text_with_gemini(file_path)
    system_rating_validation = validate_system_rating(file_path)
    ahj_validation, ahj_correct = validate_with_perplexity(file_path)
    location_validation = validate_location(file_path)

    # Combine all results into a single response
    response = {
        "structured_data": structured_data,
        "web_data": web_data,
        "comparison_results": comparison_results,
        "extracted_data": extracted_data,
        "system_rating_validation": system_rating_validation,
        "ahj_validation": {
            "details": ahj_validation,
            "is_correct": ahj_correct  # "Yes", "No", or "Uncertain"
        },
        "location_validation": location_validation
    }

    return jsonify(response)  # Return combined response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)