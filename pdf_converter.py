#!/usr/bin/env python3
"""
PDF to JPEG Converter
Converts all PDF pages to JPEG images.
Uses PyMuPDF (fitz) for better cross-platform compatibility.
"""

import os
from pathlib import Path
import fitz  # PyMuPDF

def convert_pdf_to_jpeg(pdf_path, output_folder):
    """Convert all PDF pages to JPEG images."""
    pdf_name = Path(pdf_path).stem
    
    # Open PDF
    pdf_document = fitz.open(pdf_path)
    total_pages = len(pdf_document)
    
    if total_pages == 0:
        print(f"  Warning: PDF has no pages")
        pdf_document.close()
        return [], 0
    
    jpeg_paths = []
    # Convert all pages (including last page)
    for page_num in range(total_pages):
        page = pdf_document[page_num]
        
        # Render page to image (2x zoom for better quality)
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        
        # Save as JPEG
        jpeg_filename = f"{pdf_name}_page_{page_num + 1}.jpg"
        jpeg_path = os.path.join(output_folder, jpeg_filename)
        pix.save(jpeg_path)
        jpeg_paths.append(jpeg_path)
        print(f"  Saved: {jpeg_filename}")
    
    pdf_document.close()
    return jpeg_paths, total_pages

def main():
    # Get current directory
    current_dir = os.getcwd()
    
    # Create output folder
    output_folder = os.path.join(current_dir, "jpeg_converted")
    os.makedirs(output_folder, exist_ok=True)
    
    print(f"Working directory: {current_dir}")
    print(f"Output folder: {output_folder}")
    print("-" * 60)
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process:\n")
    
    total_jpegs = 0
    
    # Process each PDF
    for pdf_file in sorted(pdf_files):
        pdf_path = os.path.join(current_dir, pdf_file)
        print(f"Processing: {pdf_file}")
        
        try:
            jpeg_paths, pages_converted = convert_pdf_to_jpeg(pdf_path, output_folder)
            
            if jpeg_paths:
                print(f"  Converted {pages_converted} page(s) to JPEG")
                total_jpegs += pages_converted
            print()
            
        except Exception as e:
            print(f"  Error processing {pdf_file}: {str(e)}\n")
            continue
    
    print("-" * 60)
    print("Processing complete!")
    print(f"Total JPEG images created: {total_jpegs}")
    print(f"Images saved to: {output_folder}")

if __name__ == "__main__":
    main()
