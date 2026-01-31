#!/usr/bin/env python3
"""
AI Transaction Workflow - Using Opencode as Brain
Extracts transactions and identifies AI-related ones in a single step
"""

import os
import sys
import subprocess
import csv
import re
import time
from pathlib import Path
import fitz  # PyMuPDF
from datetime import datetime

def print_header():
    """Print workflow header."""
    print("=" * 70)
    print("AI Transaction Extraction Workflow")
    print("Using Opencode as AI Brain")
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

def extract_and_identify_ai_transactions(image_path, statement_id, page_num):
    """Use opencode to extract transactions AND identify AI ones."""
    prompt = """Extract all transaction data from this credit card statement.
    
For each transaction, identify if it's AI-related (OpenRouter, Anthropic, Google Cloud, RunPod, Kie.ai, BudgieAI, DigitalOcean, AI services, etc.).

Return ONLY AI-RELATED transactions in this exact format (one per line):
DATE|POSTING_DATE|DESCRIPTION|AMOUNT|SERVICE_NAME

Examples:
19/05/25|20/05/25|ANTHROPIC ANTHROPIC.COMUS USD 5.35|182.70|Anthropic AI
01/09/25|02/09/25|OPENROUTER, INC OPENROUTER.AIUS USD 5.80|191.91|OpenRouter AI

If no AI transactions found, return: NO_AI_TRANSACTIONS

Important:
- Only return AI-related transactions
- Use service names like: "OpenRouter AI", "Anthropic AI", "Google Cloud", "RunPod GPU", "Kie.ai", "BudgieAI", "DigitalOcean", etc.
- Do not include regular purchases, gas, food, etc."""
    
    try:
        # Use shell command for Windows compatibility
        cmd = f'opencode run "{prompt}" -m kimi-for-coding/k2p5 -f "{image_path}"'
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            shell=True
        )
        
        output = result.stdout.strip()
        
        # Clean up markdown if present
        output = re.sub(r'```[\w]*\n?', '', output)
        output = re.sub(r'\n```', '', output)
        output = output.strip()
        
        transactions = []
        
        if output and 'NO_AI' not in output.upper():
            for line in output.split('\n'):
                line = line.strip()
                # Match format: DATE|POSTING_DATE|DESCRIPTION|AMOUNT|SERVICE
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 5 and re.match(r'\d{2}/\d{2}/\d{2}', parts[0]):
                        transactions.append({
                            'statement_id': statement_id,
                            'page': page_num,
                            'transaction_date': parts[0].strip(),
                            'posting_date': parts[1].strip(),
                            'description': parts[2].strip(),
                            'amount': parts[3].strip(),
                            'service': parts[4].strip()
                        })
        
        return transactions
        
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []

def process_all_images(images):
    """Process all images and extract AI transactions."""
    print()
    print("[STEP 2] Extracting AI transactions using opencode brain...")
    
    all_ai_transactions = []
    
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
        
        print(f"  [{idx}/{len(images)}] Analyzing: {filename}")
        
        transactions = extract_and_identify_ai_transactions(img_path, statement_id, page_num)
        
        if transactions:
            print(f"    [OK] Found {len(transactions)} AI transaction(s):")
            for t in transactions:
                print(f"      - {t['service']}: {t['amount']} THB ({t['transaction_date']})")
            all_ai_transactions.extend(transactions)
        else:
            print(f"    [INFO] No AI transactions")
        
        time.sleep(1)  # Rate limiting
    
    print(f"[OK] Total AI transactions found: {len(all_ai_transactions)}")
    return all_ai_transactions

def save_and_summarize(transactions, output_file):
    """Save AI transactions and generate summary."""
    print()
    print("[STEP 3] Saving results and generating summary...")
    
    if not transactions:
        print("[INFO] No AI transactions to save")
        return
    
    # Save to CSV
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Statement ID', 'Page', 'Transaction Date', 'Posting Date', 'Description', 'Service', 'Amount (THB)'])
        
        for t in transactions:
            writer.writerow([
                t['statement_id'], t['page'], t['transaction_date'],
                t['posting_date'], t['description'], t['service'], t['amount']
            ])
    
    print(f"[OK] Saved to: {output_file}")
    print()
    
    # Generate summary
    service_totals = {}
    total_amount = 0
    
    for t in transactions:
        service = t['service']
        try:
            amount = float(t['amount'].replace(',', ''))
            if service not in service_totals:
                service_totals[service] = {'count': 0, 'total': 0}
            service_totals[service]['count'] += 1
            service_totals[service]['total'] += amount
            total_amount += amount
        except:
            pass
    
    # Print summary
    print("=" * 70)
    print("AI TRANSACTION SUMMARY")
    print("=" * 70)
    print()
    
    for service, data in sorted(service_totals.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"{service:.<50} {data['count']:>3} txns  {data['total']:>10,.2f} THB")
    
    print()
    print("-" * 70)
    total_count = sum(d['count'] for d in service_totals.values())
    print(f"{'TOTAL':.<50} {total_count:>3} txns  {total_amount:>10,.2f} THB")
    print("=" * 70)

def main():
    """Main workflow function."""
    print_header()
    
    # Get input directory
    input_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    # Setup output
    output_dir = 'workflow_output'
    jpeg_dir = os.path.join(output_dir, 'jpeg_converted')
    output_csv = os.path.join(output_dir, 'ai_transactions.csv')
    
    # Step 1: Convert PDFs to images
    images = convert_pdfs_to_images(input_dir, jpeg_dir)
    
    if not images:
        print("[ERROR] No images converted!")
        return
    
    # Step 2: Extract AI transactions using opencode brain
    ai_transactions = process_all_images(images)
    
    # Step 3: Save and summarize
    save_and_summarize(ai_transactions, output_csv)
    
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
    print("  4. Choose import option")
    print()

if __name__ == "__main__":
    main()
