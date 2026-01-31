#!/usr/bin/env python3
"""
Extract transaction lists from KTC credit card statement images.
Processes only page 1 images (page 2 contains payment slip, no transactions).
"""

import os
import re
from pathlib import Path
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import pytesseract

def extract_transactions_from_image(image_path):
    """Extract transaction data from an image using OCR."""
    # Open image
    image = Image.open(image_path)
    
    # Perform OCR
    text = pytesseract.image_to_string(image, lang='eng+tha')
    
    return text

def parse_transactions(text):
    """Parse transaction data from OCR text."""
    transactions = []
    
    # Look for transaction patterns (date date description amount)
    # Pattern: DD/MM/YY followed by DD/MM/YY, then description, then amount
    lines = text.split('\n')
    
    for line in lines:
        # Match transaction lines
        # Pattern: date (DD/MM/YY or DD/MM/YYYY), posting date, description, amount
        match = re.match(r'(\d{2}/\d{2}/\d{2,4})\s+(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(-?[\d,]+\.\d{2})', line.strip())
        if match:
            trans_date = match.group(1)
            post_date = match.group(2)
            description = match.group(3).strip()
            amount = match.group(4)
            
            transactions.append({
                'transaction_date': trans_date,
                'posting_date': post_date,
                'description': description,
                'amount': amount
            })
    
    return transactions

def main():
    # Directory containing images
    image_dir = r"C:\Users\Phontan-Chang\Desktop\credit_statements\jpeg_converted"
    
    # Get all page 1 images (transaction pages)
    page1_images = sorted([f for f in os.listdir(image_dir) if f.endswith('_page_1.jpg')])
    
    print(f"Found {len(page1_images)} transaction pages to process\n")
    print("="*80)
    
    all_transactions = []
    
    for img_file in page1_images:
        img_path = os.path.join(image_dir, img_file)
        statement_name = img_file.replace('_page_1.jpg', '')
        
        print(f"\nProcessing: {statement_name}")
        print("-"*80)
        
        try:
            # Extract text from image
            text = extract_transactions_from_image(img_path)
            
            # Parse transactions
            transactions = parse_transactions(text)
            
            if transactions:
                print(f"Found {len(transactions)} transactions:")
                print(f"{'Trans Date':<12} {'Post Date':<12} {'Description':<50} {'Amount':>12}")
                print("-"*80)
                
                for t in transactions:
                    print(f"{t['transaction_date']:<12} {t['posting_date']:<12} {t['description']:<50} {t['amount']:>12}")
                    all_transactions.append({
                        'statement': statement_name,
                        **t
                    })
            else:
                print("No transactions found in this statement")
                
        except Exception as e:
            print(f"Error processing {img_file}: {str(e)}")
    
    # Summary
    print("\n" + "="*80)
    print(f"\nTOTAL TRANSACTIONS EXTRACTED: {len(all_transactions)}")
    print("\nAll transactions have been extracted from page 1 of each statement.")
    print("(Page 2 contains payment slip information, no transactions)")

if __name__ == "__main__":
    main()
