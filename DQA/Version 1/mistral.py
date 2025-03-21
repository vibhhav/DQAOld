import fitz  # PyMuPDF for PDF text extraction
from groq import Groq
import json
import re
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration: Set up Groq API client (Replace with your actual API key)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------------- TIMING DECORATOR ----------------------
# def measure_time(func):
#     """Decorator to measure the execution time of functions."""
#     def wrapper(*args, **kwargs):
#         start_time = time.perf_counter()
#         result = func(*args, **kwargs)
#         end_time = time.perf_counter()
#         elapsed_time = end_time - start_time
#         print(f"⏱️ Time taken by {func.__name__}: {elapsed_time:.4f} seconds")
#         return result
#     return wrapper

# ---------------------- PDF TEXT EXTRACTION ----------------------
  
def extract_text_from_pdf(pdf_path):
    """Extracts all text from a PDF file."""
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text("text") for page in doc)

  
def extract_text_by_page(pdf_path):
    """Extracts text from each page of a PDF file and returns a list of pages."""
    doc = fitz.open(pdf_path)
    return [{"page_number": page.number + 1, "text": page.get_text("text")} for page in doc]

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

  
def process_text_with_groq(text):
    """Extracts structured data from text using Groq's LLM."""
    prompt = f"""
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
    """

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts structured data."},
            {"role": "user", "content": prompt + f"\n\nExtract from the following text:\n\n{text}"}
        ],
        model="mistral-saba-24b",
        temperature=0.3,
        max_tokens=1024
    )

    return clean_json_output(response.choices[0].message.content)

  
def compare_data_with_groq(reference_data, page_data):
    """Compares extracted data across pages using Groq's LLM."""
    
    # Normalize text fields (case-insensitive)
    for field in ["company_name", "company_address", "project_name", "project_address", "email_id"]:
        reference_data[field] = normalize_text(reference_data.get(field))
        page_data[field] = normalize_text(page_data.get(field))

    prompt = f"""
    You are a high-precision document validation expert. 
    
    Compare these JSON objects and identify ONLY TRUE DISCREPANCIES based on the following STRICT RULES:

    Reference Data:
    {json.dumps(reference_data, indent=4)}

    Page Data:
    {json.dumps(page_data, indent=4)}

    STRICT VALIDATION RULES:
    1. SHEET NUMBER RULE: If both sheet numbers have the same prefix pattern (e.g., "PV-", "A-", "E-"), they are considered IDENTICAL regardless of the numbers that follow. For example, "PV-1" vs "PV-15" are considered IDENTICAL and should NOT be reported as discrepancies.
    
    2. SHEET SIZE RULE: The following sheet size formats are ALL considered IDENTICAL:
       - "ANSI B 11\\" X 17\\""
       - "11\\" X 17\\""
       - "11\\" X 17\\" ANSI B"
       - "ANSI B\\n11\\" X 17\\""
       - "11 X 17"
       - Any format that contains both the numbers "11" and "17"
    
    3. NEWLINE RULE: Newline characters (\\n) in text fields are considered equivalent to spaces. For example, "ava morales\\nresidence" is IDENTICAL to "ava morales residence".
    
    4. TEXT NORMALIZATION RULE: Perform case-insensitive comparison and ignore differences in whitespace for all text fields.
    
    5. FIELD IMPORTANCE: The "sheet_name" field should be completely ignored in validation.
    
    6. **SYSTEM RATING RULE:**
       - The **DC system size** and **AC system size** must be identical across all pages.
       - Minor formatting differences (e.g., "6.23 kWDC" vs. "6.230 kWDC") are NOT discrepancies.
       - If a page does not mention the system rating, DO NOT flag it as a discrepancy.
       - Example:  
         ✅ "6.23 kWDC" == "6.230 kWDC" (Same value, different format)  
         ❌ "6.23 kWDC" ≠ "5.5 kWDC" (Different value)

    Return a JSON object with ONLY TRUE DISCREPANCIES after applying these rules:
    {{
        "discrepancies": [
            {{"field": "", "expected": "", "found": ""}}
        ]
    }}

    If there are no true discrepancies after applying these rules, return an empty list:
    {{ "discrepancies": [] }}
    
    EXAMPLE ANALYSIS:
    - "PV-1" vs "PV-8" → NOT a discrepancy (same prefix)
    - "ANSI B\\n11\\" X 17\\"" vs "ANSI B 11\\" X 17\\"" → NOT a discrepancy (same dimensions)
    - "ava morales\\nresidence" vs "ava morales residence" → NOT a discrepancy (newlines = spaces)
    """

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a JSON validation assistant."},
            {"role": "user", "content": prompt}
        ],
        model="mistral-saba-24b",
        temperature=0.3,
        max_tokens=1024
    )

    return clean_json_output(response.choices[0].message.content)

# ---------------------- VALIDATION ACROSS PAGES ----------------------

  
def validate_sheet_index(pdf_text, pages_data):
    """Validate sheet index completeness using LLM semantic matching"""
    
    # Step 1: Extract Sheet Index using LLM
    index_prompt = f"""
    EXTRACTION TASK:
    1. Find the "SHEET INDEX" section in this document text:
    {pdf_text}
    2. Extract all sheet entries in this format:
    - Sheet numbers (including ranges like E5-E6, A3-A4, etc.)
    - Corresponding sheet names
    3. Return JSON with original index structure:
    {{
        "sheet_index": [
            {{"sheets": "E1", "name": "COVER PAGE"}},
            {{"sheets": "A5-A6", "name": "ATTACHMENT DETAILS"}},
            ...
        ]
    }}
    """
    
    index_response = client.chat.completions.create(
        messages=[{"role": "user", "content": index_prompt}],
        model="mistral-saba-24b",
        response_format={"type": "json_object"}
    )
    sheet_index = json.loads(index_response.choices[0].message.content)["sheet_index"]

    # Step 2: Prepare Validation Data
    validation_prompt = f"""
    DOCUMENT VALIDATION TASK:
    
    SHEET INDEX (Expected):
    {json.dumps(sheet_index, indent=2)}
    
    ACTUAL PAGES FOUND:
    {json.dumps(pages_data, indent=2)}
    
    VALIDATION RULES:
    1. Match sheet numbers/names using semantic understanding
    2. Consider these as valid matches:
       - "PV3" vs "PV-3"
       - "ROOF PLAN" vs "ROOF PLANS"
       - Number ranges vs individual sheets (PV5-PV6 = PV5 + PV6)
    3. Flag:
       - Missing sheets from index
       - Extra sheets not in index
       - Name mismatches (>30% difference in meaning)
    
    Return JSON with:
    {{
        "missing_sheets": [
            {{"expected_sheet": "PVX", "expected_name": "..."}}
        ],
        "name_mismatches": [
            {{"sheet": "PVX", "expected": "...", "found": "..."}}
        ],
        "extra_sheets": [
            {{"sheet": "PVX", "name": "..."}}
        ],
        "validation_summary": "..." 
    }}
    """
    
    # Step 3: Perform LLM Validation
    validation_response = client.chat.completions.create(
        messages=[{"role": "user", "content": validation_prompt}],
        model="mistral-saba-24b",
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    return json.loads(validation_response.choices[0].message.content)


  
def validate_info_across_pages(pdf_path):
    """Validates extracted information across all pages using LLM comparison."""
    
    # Extract text from each page
    pages_text = extract_text_by_page(pdf_path)

    # Extract reference data from the first page
    reference_data = process_text_with_groq(pages_text[0]["text"])
    if "error" in reference_data:
        return {"error": "Failed to extract reference data from the first page."}

    discrepancies = []
    sheet_numbers = []
    pages_data = []
    page_data_mapping = {}
    
    # Process first page
    if "sheet_number" in reference_data and reference_data["sheet_number"]:
        sheet_numbers.append(reference_data["sheet_number"])
        page_data_mapping[1] = reference_data
    
    # Process remaining pages
    for page in pages_text:
        page_data = process_text_with_groq(page["text"])
        pages_data.append({
            "sheet_number": page_data.get("sheet_number"),
            "sheet_name": page_data.get("sheet_name")
        })


    for page in pages_text[1:]:  # Skip first page (reference)
        page_data = process_text_with_groq(page["text"])
        if "error" in page_data:
            discrepancies.append({"page_number": page["page_number"], "error": "Failed to extract data."})
            continue

        # Store page data
        page_data_mapping[page["page_number"]] = page_data

        # Add sheet number to our list
        if "sheet_number" in page_data and page_data["sheet_number"]:
            sheet_numbers.append(page_data["sheet_number"])

        # Compare extracted data with reference data
        comparison_result = compare_data_with_groq(reference_data, page_data)
        if comparison_result.get("discrepancies"):
            for discrepancy in comparison_result["discrepancies"]:
                discrepancies.append({
                    "page_number": page["page_number"],
                    "field": discrepancy["field"],
                    "expected": discrepancy["expected"],
                    "found": discrepancy["found"]
                })
    
    # Check for missing sheet numbers using the LLM
    sequence_check_prompt = f"""
    You are a data analysis assistant specializing in document validation.
    
    Analyze the sequence of sheet numbers below and identify any missing numbers in the sequence:

    Sheet Numbers Found: {json.dumps(sheet_numbers)}

    Task:
    1. First, identify the common prefix pattern in the sheet numbers (like 'E-', 'A-', 'PV-', etc.)
    2. Group sheet numbers by their prefix
    3. For each prefix group, detect any missing numbers in the sequence 
       (e.g., if A-1, A-2, A-4 exist, then A-3 is missing)
    4. Sort the sheet numbers within each group in ascending order
    5. Only report missing numbers within the observed range for each prefix group

    Return only a JSON object with this structure:
    {{
        "prefix_groups": [
            {{
                "prefix": "A-",
                "sheet_numbers_sorted": [],
                "missing_sheet_numbers": []
            }},
            {{
                "prefix": "E-",
                "sheet_numbers_sorted": [],
                "missing_sheet_numbers": []
            }}
        ],
        "analysis": "Brief description of findings"
    }}
    """

    sequence_analysis_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a data analysis assistant specializing in document validation."},
            {"role": "user", "content": sequence_check_prompt}
        ],
        model="mistral-saba-24b",
        temperature=0.3,
        max_tokens=1024
    )

    sequence_analysis = clean_json_output(sequence_analysis_response.choices[0].message.content)
    full_text = extract_text_from_pdf(pdf_path)
    sheet_index_validation = validate_sheet_index(full_text, pages_data)
    # Generate validation summary
    return {
        "reference_data": reference_data,
        "sheet_index_validation": sheet_index_validation,
        "total_pages": len(pages_text),
        "discrepancies": discrepancies,
        "sheet_numbers": {
            "found": sheet_numbers,
            "missing": sequence_analysis.get("missing_sheet_numbers", []),
            "analysis": sequence_analysis.get("analysis", "")
        },
        "summary": f"Found {len(discrepancies)} discrepancies across {len(pages_text)} pages. {len(sequence_analysis.get('missing_sheet_numbers', []))} sheet numbers missing in sequence."
    }

# ---------------------- USAGE ----------------------

if __name__ == "__main__":
    pdf_path = "C:\\Users\\Admin\Design Qualtiy Assurance\\Version 1\\_CAD_ AvaMorales_ML-1-7_removed.pdf"  # Replace with actual PDF path
    validation_summary = validate_info_across_pages(pdf_path)

    print(json.dumps(validation_summary, indent=4))