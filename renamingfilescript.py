import os
import re
import shutil
import fitz
import json
import pytesseract
from PIL import Image
import requests

# Path to your Tesseract executable (if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' #Paste Tesseract Location Here

# Image formats and unsupported formats
image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
unsupported_formats = ['.svg', '.webp', '.heif', '.heic', '.raw', '.psd', '.eps', '.ico', '.tga']

def adobe_authenticate():
    credentials = {}
    with open(r'pdfservices-api-credentials.json', 'r') as file:  ## Paste Credentials Here
        credentials = json.load(file)
    
    client_id = credentials['client_credentials']['client_id']
    client_secret = credentials['client_credentials']['client_secret']
    ims_host = 'https://ims-na1.adobelogin.com'
    
    response = requests.post(
        f"{ims_host}/ims/token/v1",
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'openid,AdobeID,read_organization',
        },
    )
    response.raise_for_status()
    return response.json()['access_token']

def adobe_convert_to_pdf(input_path, access_token):
    with open(input_path, 'rb') as file:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/octet-stream'
        }
        response = requests.post(
            'https://pdf-services.adobe.io/operation/api/v1/pdfservices/convert_to_pdf',
            headers=headers,
            data=file,
        )
        response.raise_for_status()
        
        pdf_path = input_path.rsplit('.', 1)[0] + '.pdf'
        with open(pdf_path, 'wb') as pdf_file:
            pdf_file.write(response.content)
        return pdf_path

def convert_image_to_pdf(input_path):
    image = Image.open(input_path)
    pdf_path = input_path.rsplit('.', 1)[0] + '.pdf'
    image.convert('RGB').save(pdf_path)
    return pdf_path

def extract_text_from_pdf(input_path):
    pdf_text = ""
    with fitz.open(input_path) as pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            page_text = page.get_text()
            pdf_text += page_text + "\n"
    return pdf_text

def extract_text_from_image(input_path):
    try:
        img = Image.open(input_path)
        text = pytesseract.image_to_string(img)
        return text
    except TypeError as e:
        print(f"Error processing image {input_path}: {e}")
        return None

def extract_information_from_text(text):
    business_name_patterns = {
        "Business1": [r"Business 1", r"BUSINESS 1", r"Address of Business"],
        #Enter Business data 
    }    

    vendor_name_patterns = {
        
        "Vendor1": [r" Vendor 1 ", r"Vendor 1 Address"],
        
}

    date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
    total_amount_pattern = r'(total.*?(\$[\d,]+))'
    amount_pattern = r'\$\s*([\d,]+)'

    extracted_info = {
        'vendor_name': 'X',
        'business_name': 'X',
        'date': 'X',
        'amount': 'X'
    }

    # Extract business name based on patterns
    for business_code, patterns in business_name_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                extracted_info['business_name'] = business_code
                break
        if extracted_info['business_name'] != 'X':
            break

    # Extract vendor name based on patterns
    for vendor_code, patterns in vendor_name_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                extracted_info['vendor_name'] = vendor_code
                break
        if extracted_info['vendor_name'] != 'X':
            break

    # Extract date
    date_match = re.search(date_pattern, text)
    if date_match:
        date = date_match.group(1)
        month, day, year = date.split('/')
        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        if len(year) == 2:
            year = '20' + year
        extracted_info['date'] = f"{month}{day}{year}"
    else:
        extracted_info['date'] = 'X'

    # Extract the total amount following the word "total"
    total_matches = re.findall(total_amount_pattern, text, re.IGNORECASE)
    if total_matches:
        amounts = [match[1].replace(',', '') for match in total_matches]
        highest_amount = max([int(amount.replace('$', '').replace(',', '').strip()) for amount in amounts])
    else:
        # If no total amounts are found, fall back to all dollar amounts
        all_amounts_matches = re.findall(amount_pattern, text)
        if all_amounts_matches:
            highest_amount = max([int(amount.replace(',', '')) for amount in all_amounts_matches])
        else:
            highest_amount = None
        
    extracted_info['amount'] = f"{highest_amount}" if highest_amount else 'X'

    return extracted_info

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def rename_file(original_path, extracted_info):
    business_name = extracted_info['business_name']
    vendor_name = extracted_info['vendor_name']
    amount = extracted_info['amount']
    date = extracted_info['date']

    # Format the date as YYMM
    if date and len(date) == 8:  # Ensure date is in MMDDYYYY format
        mm = date[:2]
        yy = date[-2:]
        yy_mm = yy + mm  # Format as YYMM
    else:
        yy_mm = "YYMM"  # Default if date is not extracted or incorrectly formatted

    # Remove non-alphanumeric characters from business name and vendor name for cleaner file names
    business_name_clean = sanitize_filename(business_name)
    vendor_name_clean = sanitize_filename(vendor_name)

    # Construct new filename
    new_filename = f"{yy_mm} {business_name_clean} {vendor_name_clean} {amount}.pdf"

    # Path to the renamed file
    new_path = os.path.join(os.path.dirname(original_path), sanitize_filename(new_filename))

    # Rename the file in the same directory
    os.rename(original_path, new_path)
    print(f"Renamed {os.path.basename(original_path)} to {new_filename}")

    return new_path

def move_file_to_directory(file_path, business_name):
    output_directories = {
        "BZ1": r"C:\Users\Desktop\BZ1",
        "BZ2": r"C:\Users\Desktop\BZ2",
        "BZ3": r"C:\Users\Desktop\BZ3",
        "BZ4": r"C:\Users\Desktop\BZ4",
        "BZ5": r"C:\Users\Desktop\BZ5",
        "BZ6": r"C:\Users\Desktop\BZ6",
        "BZ7": r"C:\Users\Desktop\BZ7",
        "BZ8": r"C:\Users\Desktop\BZ8",
        "BZ9": r"C:\Users\Desktop\BZ9",
        "BZ10": r"C:\Users\Desktop\BZ10",
        "BZ11": r"C:\Users\Desktop\BZ11",
        "BZ12": r"C:\Users\Desktop\BZ12"
    }

    others_directory = r"C:\Users\Desktop\Others"
    
    # Determine destination directory based on business name
    if business_name in output_directories:
        destination_dir = output_directories[business_name]
    else:
        destination_dir = others_directory
    
    destination_path = os.path.join(destination_dir, os.path.basename(file_path))

    # Check if the destination file already exists and rename if necessary
    if os.path.exists(destination_path):
        base, extension = os.path.splitext(destination_path)
        counter = 1
        new_destination_path = f"{base}_{counter}{extension}"
        while os.path.exists(new_destination_path):
            counter += 1
            new_destination_path = f"{base}_{counter}{extension}"
        destination_path = new_destination_path

    # Move the file to the destination directory
    shutil.move(file_path, destination_path)
    print(f"Moved {file_path} to {destination_path}")

def main():
    input_directory = r"C:\Users\Desktop\Unsorted Files"

    for filename in os.listdir(input_directory):
        input_path = os.path.join(input_directory, filename)

        if any(filename.lower().endswith(image_format) for image_format in image_formats):
            try:
                print(f"Extracting text from image {input_path} using Tesseract OCR...")
                pdf_text = extract_text_from_image(input_path)
                if not pdf_text or not pdf_text.strip():
                    raise ValueError("No text found or empty text extracted, attempting conversion using Adobe API.")
                
                # Convert image to PDF if needed
                pdf_path = convert_image_to_pdf(input_path)
            except Exception as e:
                print(f"Tesseract OCR failed for {input_path}, attempting to convert using Adobe API. Error: {e}")
                access_token = adobe_authenticate()
                try:
                    pdf_path = adobe_convert_to_pdf(input_path, access_token)
                    pdf_text = extract_text_from_pdf(pdf_path)
                except Exception as adobe_error:
                    print(f"Conversion using Adobe API failed for {input_path}. Error: {adobe_error}")
                    continue  # Skip to the next file in case of an error
        elif any(filename.lower().endswith(image_format) for image_format in unsupported_formats):
            try:
                print(f"Converting unsupported image format {input_path} using Adobe API...")
                access_token = adobe_authenticate()
                pdf_path = adobe_convert_to_pdf(input_path, access_token)
                pdf_text = extract_text_from_pdf(pdf_path)
            except Exception as e:
                print(f"Conversion failed for {input_path}. Error: {e}")
                continue  # Skip to the next file in case of an error

        elif filename.lower().endswith(".pdf"):
            print(f"Extracting text from PDF {input_path}...")
            pdf_path = input_path
            pdf_text = extract_text_from_pdf(pdf_path)
        else:
            print(f"Unsupported file type: {filename}")
            continue

        extracted_info = extract_information_from_text(pdf_text)

        # Rename the file based on extracted information
        renamed_file_path = rename_file(pdf_path, extracted_info)

        # Move the renamed file to the appropriate directory
        move_file_to_directory(renamed_file_path, extracted_info['business_name'])

    print("All files renamed and moved successfully.")

if __name__ == "__main__":
    main()
