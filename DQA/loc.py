import fitz  # PyMuPDF
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv()

# Configure Gemini API
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

# Google Maps API Key
GOOGLE_MAPS_API_KEY = "AIzaSyCy6gBf2bQI6RYN8E_DWMgp6RIx59_7suU"

# PDF File Path
PDF_PATH = "C:\\Users\\Admin\\Downloads\\Raul Sanchez-1.pdf"


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
        print(f"Map image saved as {filename}")
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
        
        img_filename = f"extracted_image_{img_index}.{img_ext}"
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
                
            print(f"Classified {img_path} as: {classification}")
            
        except Exception as e:
            print(f"Error analyzing {img_path}: {str(e)}")
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

    print(f"\n--- RAW GEMINI RESPONSE ---\n{response.text}\n")  # Debugging output

    return response.text


def extract_validation_results(response_text):
    """Parses Gemini's response to extract structured Yes/No and Confidence Level."""
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



if __name__ == "__main__":
    print("Starting PDF map validation process...")
    
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(PDF_PATH)
    
    # Extract project address from text
    project_address = extract_project_address(pdf_text)
    print(f"Extracted address: {project_address}")
    
    # Get latitude and longitude
    lat, lng = get_lat_long(project_address)
    print(f"Coordinates: {lat}, {lng}")
    
    # Extract images from the PDF
    extracted_images = extract_images_from_pdf(PDF_PATH)
    print(f"Extracted {len(extracted_images)} images from PDF")
    
    # Classify which extracted images are maps or satellite views
    classified_images = classify_pdf_images(extracted_images)
    
    # Download reference maps from Google Maps
    google_map_file = "google_map_view.png"
    google_satellite_file = "google_satellite_view.png"
    get_map_image(lat, lng, map_type="roadmap", zoom=13, size="400x400", filename=google_map_file)
    get_map_image(lat, lng, map_type="satellite", zoom=21, filename=google_satellite_file)
    
    # Validate maps from PDF against Google Maps
    validation_results = {}
    
    # Validate map views
# Validate map views
# Validate map views
    # Validate map views
    if classified_images["map_views"]:
        print(f"\nValidating {len(classified_images['map_views'])} map view(s)...")
        for i, map_path in enumerate(classified_images["map_views"]):
            print(f"Validating Map #{i+1}: {map_path} (PDF) ↔ {google_map_file} (Google Maps)")

            result_text = validate_map_location(map_path, project_address, google_map_file)
            parsed_result = extract_validation_results(result_text)

            validation_results[f"map_{i+1}"] = parsed_result

            print(f"\n--- MAP VIEW #{i+1} VALIDATION RESULTS ---")
            print(f"Compared PDF Image: {map_path}")
            print(f"Compared Google Maps Image: {google_map_file}")
            print(f"Map View Match: {parsed_result['Map Match (%)']}")
            print(f"Confidence Level: {parsed_result['Confidence']}")
            print("-------------------------------------------\n")


    # Validate satellite views
    # Validate satellite views
    if classified_images["satellite_views"]:
        print(f"\nValidating {len(classified_images['satellite_views'])} satellite view(s)...")
        for i, sat_path in enumerate(classified_images["satellite_views"]):
            print(f"Validating Satellite #{i+1}: {sat_path} (PDF) ↔ {google_satellite_file} (Google Maps)")

            result_text = validate_map_location(sat_path, project_address, google_satellite_file)
            parsed_result = extract_validation_results(result_text)

            validation_results[f"satellite_{i+1}"] = parsed_result

            print(f"\n--- SATELLITE VIEW #{i+1} VALIDATION RESULTS ---")
            print(f"Compared PDF Image: {sat_path}")
            print(f"Compared Google Maps Image: {google_satellite_file}")
            print(f"Satellite View Match: {parsed_result['Satellite Match (%)']}")
            print(f"Confidence Level: {parsed_result['Confidence']}")
            print("-------------------------------------------\n")


