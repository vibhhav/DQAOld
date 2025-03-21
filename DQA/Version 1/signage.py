import os
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image

# Set Gemini API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Extract images from PDF
def extract_images_from_pdf(pdf_path, output_folder="extracted_images"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    images = convert_from_path(pdf_path)
    image_paths = []

    for i, img in enumerate(images):
        image_path = os.path.join(output_folder, f"signage_{i+1}.png")
        img.save(image_path, "PNG")
        image_paths.append(image_path)

    return image_paths

# Validate image using Gemini Vision
def validate_signage_with_gemini(image_path, expected_signage_details):
    model = genai.GenerativeModel("gemini-1.5-pro-002")

    with Image.open(image_path) as img:
        response = model.generate_content(
            [img, f"Check if this signage matches the following expected NEC-compliant signage:\n{expected_signage_details}"],
            stream=False
        )
    
    return response.text

# Run the process
def main(pdf_path, expected_signage_details):
    image_paths = extract_images_from_pdf(pdf_path)
    results = {}

    for image_path in image_paths:
        result = validate_signage_with_gemini(image_path, expected_signage_details)
        results[image_path] = result
        print(f"Validation Result for {image_path}:\n{result}\n")

if __name__ == "__main__":
    pdf_path = "C:\\Users\\Admin\Design Qualtiy Assurance\\Version 1\\File-9.pdf"  # Change this to your actual PDF path
    expected_signage_details = """
    1. 'PHOTOVOLTAIC SYSTEM AC DISCONNECT' label must be present.
    2. Warning labels should have red/yellow backgrounds with black text.
    3. 'RAPID SHUTDOWN SWITCH' must include shut-down instructions.
    4. Labels should match NEC codes: 690.54, 705.12, 690.13, 690.56(C).
    """

    main(pdf_path, expected_signage_details)
