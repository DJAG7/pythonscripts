# File Organizer Script

This Python script automates the process of organizing files by extracting relevant information from images and PDFs, renaming the files based on the extracted data, and moving them to the appropriate directories.

## Features

- **Text Extraction**: Extracts text from images using Tesseract OCR or the Adobe PDF Services API.
- **PDF Conversion**: Converts images to PDFs using Adobe PDF Services API if Tesseract OCR fails.
- **Information Extraction**: Extracts business names, vendor names, dates, and amounts from the text using regular expressions.
- **File Renaming**: Renames files based on the extracted information in the format `YYMM BusinessName VendorName Amount.pdf`.
- **File Organization**: Moves renamed files to directories based on the business name.

## Requirements

### Python Packages

- `fitz` (PyMuPDF): For handling PDFs.
- `PIL` (Pillow): For image processing.
- `pytesseract`: For OCR.
- `requests`: For making HTTP requests (used for Adobe API).
- `shutil`: For moving files.
- `re`: For regular expression operations.
- `os`: For file and directory operations.

### Other Dependencies

- **Tesseract OCR**: Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on your system and provide the correct path to the executable in the script.
- **Adobe PDF Services API**: Obtain credentials from Adobe and save them in a `pdfservices-api-credentials.json` file in the working directory.

## Installation

1. Install the required Python packages:
    ```bash
    pip install fitz Pillow pytesseract requests
    ```

2. Install Tesseract OCR on your system and configure the path in the script:
    ```python
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```

3. Obtain Adobe PDF Services API credentials and save them in a `pdfservices-api-credentials.json` file.

## Configuration

- **Business Name Patterns**: Update the `business_name_patterns` dictionary in the script with the correct patterns for your businesses.
- **Vendor Name Patterns**: Update the `vendor_name_patterns` dictionary in the script with the correct patterns for your vendors.
- **Output Directories**: Configure the `output_directories` dictionary with paths to the directories where you want files to be moved based on the business name.

## Usage

1. Place the files to be processed in the input directory defined in the script:
    ```python
    input_directory = r"C:\Users\Desktop\Unsorted Files"
    ```

2. Run the script:
    ```bash
    python script_name.py
    ```

3. The script will process each file in the input directory, extract the necessary information, rename the files accordingly, and move them to the appropriate directories.

## Error Handling

- If Tesseract OCR fails to extract text from an image, the script will attempt to convert the image to a PDF using Adobe's API.
- If the script cannot extract necessary information, it will skip the file and continue with the next one.

## Notes

- Ensure that the input directory contains only supported file types.
- The script handles conflicts in file names by appending a counter to the file name.
