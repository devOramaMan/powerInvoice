# Power Invoice Generator

This project generates a PDF invoice based on user data and extracted information from a PDF file. It uses **ReportLab** for PDF generation, **pdfplumber** for text extraction, and **OpenCV** for bounding box updates.

## Features
- Extracts text from specific regions of a PDF using bounding boxes.
- Dynamically replaces placeholders in the invoice template with user data.
- Generates a formatted PDF invoice.
- Allows visualization and updating of bounding boxes for text extraction.

## Requirements
- Python 3.x
- Required libraries:
  - `reportlab`
  - `pdfplumber`
  - `opencv-python`
  - `textwrap`


## Usage
```bash
 python  ./account_maker_pdf.py -h
usage: account_maker_pdf.py [-h] [--show] [--update] pdf_file

Calculate user usage and cost distribution. Example: python
./account/account_maker_pdf.py [faktura.pdf]

positional arguments:
  pdf_file      Path to the PDF invoice file to process

options:
  -h, --help    show this help message and exit
  --show, -s    Make a image with the bounding boxes
  --update, -u  Update/adapt the bounding boxes
```