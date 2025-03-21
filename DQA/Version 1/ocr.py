from mistralai import Mistral
import os

# api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key="z7gjzVHQOqQgMfNL46X5h94QRJ56inGD")

uploaded_pdf = client.files.upload(
    file={
        "file_name": "C:\\Users\\Admin\Design Qualtiy Assurance\\Version 1\\_CAD_ AvaMorales_ML-1-7_removed.pdf",
        "content": open("C:\\Users\\Admin\Design Qualtiy Assurance\\Version 1\\_CAD_ AvaMorales_ML-1-7_removed.pdf", "rb"),
    },
    purpose="ocr"
)  