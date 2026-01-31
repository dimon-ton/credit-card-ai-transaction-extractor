#!/usr/bin/env python3
"""
Batch Extract Transactions from All Credit Card Statement Images
Processes all .jpg files in jpeg_converted/ folder
"""

import os
import subprocess
import csv
from pathlib import Path
import re
import time

def extract_transactions_from_image(image_path):
    """Extract transaction data from an image using opencode CLI."""
    prompt = """Extract all transaction data from this credit card statement image.
    
    If this page contains a transaction list, extract each transaction with:
    - Transaction Date (Trans. Date)
    - Posting Date (Posting Date)
    - Description
    - Amount in THB
    
    Return format (one per line):
    DD/MM/YY|DD/MM/YY|DESCRIPTION|AMOUNT
    
    Example:
    07/01/25|07/01/25|Payment-KTB Internet|-8,851.33
    18/12/24|20/12/24|SHOPEE BANGKOK TH|199.00
    
    If this page contains only payment slip information (no transactions), return only: NO_TRANSACTIONS
    
    Only return transaction lines or NO_TRANSACTIONS, no other text, no markdown, no code blocks."""
    
    # Use shell=True with the command as a string
    cmd = f'opencode run "{prompt}" -m kimi-for-coding/k2p5 -f "{image_path}"'
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, shell=True)
        output = result.stdout.strip()
        
        # Clean up output - remove markdown code blocks if present
        output = re.sub(r'```[\w]*\n?', '', output)
        output = re.sub(r'\n```', '', output)
        output = output.strip()
        
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout"
    except Exception as e:
        return f"ERROR: {str(e)}"

def parse_transactions(output, statement_id, page_num):
    """Parse transaction data from opencode output."""
    transactions = []
    
    if not output or output == "NO_TRANSACTIONS" or "ERROR" in output:
        return transactions
    
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line == "NO_TRANSACTIONS":
            continue
            
        # Skip markdown formatting lines
        if line.startswith('```') or line.startswith('DATE|POSTING'):
            continue
            
        # Parse pipe-delimited format: DATE|POST_DATE|DESC|AMOUNT
        parts = line.split('|')
        if len(parts) >= 4:
            trans_date = parts[0].strip()
            post_date = parts[1].strip()
            description = parts[2].strip()
            amount = parts[3].strip()
            
            # Validate date format (DD/MM/YY)
            if re.match(r'\d{2}/\d{2}/\d{2}', trans_date):
                transactions.append({
                    'statement_id': statement_id,
                    'page': page_num,
                    'transaction_date': trans_date,
                    'posting_date': post_date,
                    'description': description,
                    'amount': amount
                })
    
    return transactions

def deduplicate_transactions(transactions):
    """Remove duplicate transactions based on all fields."""
    seen = set()
    unique_transactions = []
    
    for t in transactions:
        # Create a unique key from all fields except statement_id and page
        key = (t['transaction_date'], t['posting_date'], t['description'], t['amount'])
        if key not in seen:
            seen.add(key)
            unique_transactions.append(t)
    
    return unique_transactions

def main():
    # Directory containing images
    image_dir = r"C:\Users\Phontan-Chang\Desktop\credit_statements\jpeg_converted"
    output_csv = r"C:\Users\Phontan-Chang\Desktop\credit_statements\all_transactions.csv"
    
    # Get all jpg files
    all_images = sorted([f for f in os.listdir(image_dir) if f.endswith('.jpg')])
    
    print(f"Found {len(all_images)} images to process\n")
    print("="*100)
    
    all_transactions = []
    
    for idx, img_file in enumerate(all_images, 1):
        img_path = os.path.join(image_dir, img_file)
        
        # Extract statement ID and page number from filename
        # Format: 2511-25-01_page_1.jpg
        match = re.match(r'(\d{4}-\d{2}-\d{2})_page_(\d+)\.jpg', img_file)
        if match:
            statement_id = match.group(1)
            page_num = match.group(2)
        else:
            statement_id = img_file.replace('.jpg', '')
            page_num = '1'
        
        print(f"\n[{idx}/{len(all_images)}] Processing: {img_file} ({statement_id} - Page {page_num})")
        print("-"*100)
        
        try:
            # Extract transactions using opencode
            result = extract_transactions_from_image(img_path)
            
            if result.startswith("ERROR"):
                print(f"  [ERROR] {result}")
                continue
            
            if result == "NO_TRANSACTIONS":
                print(f"  [OK] No transactions on this page (payment slip)")
                continue
            
            # Parse transactions
            transactions = parse_transactions(result, statement_id, page_num)
            
            if transactions:
                print(f"  [OK] Found {len(transactions)} transactions:")
                for t in transactions:
                    desc = t['description'][:45] + '...' if len(t['description']) > 45 else t['description']
                    print(f"    {t['transaction_date']:<12} {t['posting_date']:<12} {desc:<48} {t['amount']:>12}")
                all_transactions.extend(transactions)
            else:
                print(f"  [WARN] No valid transactions extracted")
                
        except Exception as e:
            print(f"  [ERROR] Error processing {img_file}: {str(e)}")
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    # Deduplicate transactions
    print("\n" + "="*100)
    print(f"\nTotal transactions before deduplication: {len(all_transactions)}")
    
    unique_transactions = deduplicate_transactions(all_transactions)
    
    print(f"Total transactions after deduplication: {len(unique_transactions)}")
    
    # Save to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Statement ID', 'Page', 'Transaction Date', 'Posting Date', 'Description', 'Amount (THB)'])
        
        for t in unique_transactions:
            writer.writerow([
                t['statement_id'],
                t['page'],
                t['transaction_date'],
                t['posting_date'],
                t['description'],
                t['amount']
            ])
    
    print(f"\n[SUCCESS] Transactions saved to: {output_csv}")
    print("\n[SUCCESS] Processing complete!")

if __name__ == "__main__":
    main()
