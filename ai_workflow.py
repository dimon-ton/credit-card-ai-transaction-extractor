#!/usr/bin/env python3
"""
Automated Workflow: PDF Credit Card Statements → AI Transactions CSV
Usage: python ai_workflow.py [pdf_directory]
"""

import os
import sys
import subprocess
import csv
import re
import time
from pathlib import Path
import fitz  # PyMuPDF

def print_header():
    """Print workflow header."""
    print("=" * 70)
    print("AI Transaction Extraction Workflow")
    print("=" * 70)
    print()

def convert_pdfs_to_images(input_dir, output_dir):
    """Convert all PDFs to JPEG images."""
    print("[STEP 1] Converting PDFs to JPEG images...")
    
    pdf_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.pdf')])
    
    if not pdf_files:
        print("[ERROR] No PDF files found!")
        return []
    
    print(f"[OK] Found {len(pdf_files)} PDF file(s)")
    
    os.makedirs(output_dir, exist_ok=True)
    
    converted_images = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        filename = Path(pdf_file).stem
        
        print(f"  Converting: {pdf_file}")
        
        try:
            pdf_document = fitz.open(pdf_path)
            page_count = len(pdf_document)
            
            for page_num in range(page_count):
                page = pdf_document[page_num]
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                output_path = os.path.join(output_dir, f"{filename}_page_{page_num + 1}.jpg")
                pix.save(output_path)
                converted_images.append(output_path)
            
            pdf_document.close()
            print(f"    [OK] Converted {page_count} page(s)")
            
        except Exception as e:
            print(f"    [ERROR] {e}")
    
    print(f"[OK] Total images converted: {len(converted_images)}")
    return converted_images

def extract_transactions_with_opencode(image_path, statement_id, page_num):
    """Extract transactions from image using opencode CLI."""
    prompt = """Extract all transaction data from this credit card statement. 
    Return in format: DATE|POSTING_DATE|DESCRIPTION|AMOUNT (one per line). 
    If no transactions, return NO_TRANSACTIONS only."""
    
    try:
        # Use shell=True with full command string for Windows compatibility
        cmd = f'opencode run "{prompt}" -m kimi-for-coding/k2p5 -f "{image_path}"'
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            shell=True
        )
        
        output = result.stdout.strip()
        transactions = []
        
        if output and 'NO_TRANSACTIONS' not in output:
            for line in output.split('\n'):
                line = line.strip()
                if '|' in line and re.match(r'\d{2}/\d{2}/\d{2}', line):
                    parts = line.split('|')
                    if len(parts) >= 4:
                        transactions.append({
                            'statement_id': statement_id,
                            'page': page_num,
                            'transaction_date': parts[0].strip(),
                            'posting_date': parts[1].strip(),
                            'description': parts[2].strip(),
                            'amount': parts[3].strip()
                        })
        
        return transactions
        
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []

def extract_all_transactions(images, temp_csv):
    """Extract transactions from all images."""
    print()
    print("[STEP 2] Extracting transactions from images...")
    
    all_transactions = []
    
    for idx, img_path in enumerate(images, 1):
        filename = Path(img_path).stem
        
        # Extract statement ID and page number
        match = re.match(r'(\d{4}-\d{2}-\d{2})_page_(\d+)', filename)
        if match:
            statement_id = match.group(1)
            page_num = match.group(2)
        else:
            statement_id = filename
            page_num = '1'
        
        print(f"  [{idx}/{len(images)}] Processing: {filename}")
        
        transactions = extract_transactions_with_opencode(img_path, statement_id, page_num)
        
        if transactions:
            print(f"    [OK] Found {len(transactions)} transactions")
            all_transactions.extend(transactions)
        else:
            print(f"    [INFO] No transactions or payment slip")
        
        time.sleep(1)  # Rate limiting
    
    # Save to temp CSV
    with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Statement ID', 'Page', 'Transaction Date', 'Posting Date', 'Description', 'Amount (THB)'])
        for t in all_transactions:
            writer.writerow([
                t['statement_id'], t['page'], t['transaction_date'],
                t['posting_date'], t['description'], t['amount']
            ])
    
    print(f"[OK] Extracted {len(all_transactions)} total transactions")
    return all_transactions

def filter_ai_transactions(input_csv, output_csv):
    """Filter AI-related transactions."""
    print()
    print("[STEP 3] Filtering AI-related transactions...")
    
    ai_keywords = [
        'OPENROUTER', 'ANTHROPIC', 'RUNPOD', 'KIE.AI', 'KIE AI',
        'BUDGIEAI', 'BUDGIE AI', 'DIGITALOCEAN', 'STRIPE.*Z\.AI',
        'GOOGLE.*CLOUD'
    ]
    
    ai_transactions = []
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            desc = row['Description'].upper()
            
            is_ai = any(re.search(keyword, desc) for keyword in ai_keywords)
            
            if is_ai:
                try:
                    amount = float(row['Amount (THB)'].replace(',', ''))
                    if amount > 0:  # Only expenses
                        ai_transactions.append(row)
                except:
                    pass
    
    # Save AI transactions
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        if ai_transactions:
            writer = csv.DictWriter(f, fieldnames=ai_transactions[0].keys())
            writer.writeheader()
            writer.writerows(ai_transactions)
    
    print(f"[OK] Found {len(ai_transactions)} AI transactions")
    return ai_transactions

def generate_summary(ai_transactions):
    """Generate spending summary."""
    print()
    print("[STEP 4] Generating summary...")
    print()
    
    ai_services = {}
    total_amount = 0
    
    for row in ai_transactions:
        desc = row['Description'].upper()
        amount = float(row['Amount (THB)'].replace(',', ''))
        
        # Identify service
        if 'OPENROUTER' in desc:
            service = 'OpenRouter AI'
        elif 'ANTHROPIC' in desc:
            service = 'Anthropic AI'
        elif 'RUNPOD' in desc:
            service = 'RunPod GPU'
        elif 'KIE.AI' in desc or 'KIE AI' in desc:
            service = 'Kie.ai'
        elif 'BUDGIEAI' in desc or 'BUDGIE AI' in desc:
            service = 'BudgieAI'
        elif 'DIGITALOCEAN' in desc:
            service = 'DigitalOcean'
        elif 'STRIPE' in desc and 'Z.AI' in desc:
            service = 'Z.AI Service'
        elif 'GOOGLE' in desc and 'CLOUD' in desc:
            service = 'Google Cloud'
        else:
            service = 'Other AI Service'
        
        if service not in ai_services:
            ai_services[service] = {'count': 0, 'total': 0}
        
        ai_services[service]['count'] += 1
        ai_services[service]['total'] += amount
        total_amount += amount
    
    # Print summary
    print("=" * 70)
    print("AI TRANSACTION SUMMARY")
    print("=" * 70)
    print()
    
    for service, data in sorted(ai_services.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"{service:.<50} {data['count']:>3} txns  {data['total']:>10,.2f} THB")
    
    print()
    print("-" * 70)
    total_count = sum(d['count'] for d in ai_services.values())
    print(f"{'TOTAL':.<50} {total_count:>3} txns  {total_amount:>10,.2f} THB")
    print("=" * 70)

def main():
    """Main workflow function."""
    print_header()
    
    # Get input directory
    input_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    # Setup output directories
    output_dir = 'workflow_output'
    jpeg_dir = os.path.join(output_dir, 'jpeg_converted')
    temp_csv = os.path.join(output_dir, 'all_transactions_temp.csv')
    output_csv = os.path.join(output_dir, 'ai_transactions.csv')
    
    # Step 1: Convert PDFs to images
    images = convert_pdfs_to_images(input_dir, jpeg_dir)
    
    if not images:
        print("[ERROR] No images converted!")
        return
    
    # Step 2: Extract all transactions
    all_transactions = extract_all_transactions(images, temp_csv)
    
    if not all_transactions:
        print("[ERROR] No transactions extracted!")
        return
    
    # Step 3: Filter AI transactions
    ai_transactions = filter_ai_transactions(temp_csv, output_csv)
    
    # Step 4: Generate summary
    if ai_transactions:
        generate_summary(ai_transactions)
    else:
        print("[INFO] No AI transactions found")
    
    # Cleanup
    if os.path.exists(temp_csv):
        os.remove(temp_csv)
    
    print()
    print("=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70)
    print()
    print(f"Output file: {output_csv}")
    print()
    print("To import into Google Sheets:")
    print("  1. Open Google Sheets")
    print("  2. File > Import")
    print(f"  3. Upload: {output_csv}")
    print("  4. Choose 'Replace spreadsheet' or 'Append to current sheet'")
    print()

if __name__ == "__main__":
    main()
