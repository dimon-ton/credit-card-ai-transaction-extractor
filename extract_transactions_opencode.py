#!/usr/bin/env python3
"""
Extract transaction lists from KTC credit card statement images using opencode CLI.
Processes only page 1 images (page 2 contains payment slip, no transactions).
"""

import os
import subprocess
import json
from pathlib import Path

def extract_transactions_with_opencode(image_path):
    """Extract transaction data from an image using opencode CLI."""
    prompt = """Extract all transaction data from this credit card statement image.
    For each transaction, extract:
    - Transaction Date (Trans. Date)
    - Posting Date (Posting Date)  
    - Description
    - Amount in THB
    
    Return the data in this exact format:
    DATE|POSTING_DATE|DESCRIPTION|AMOUNT
    
    Example:
    07/01/25|07/01/25|Payment-KTB Internet|-8,851.33
    18/12/24|20/12/24|SHOPEE BANGKOK TH|199.00
    
    Only return the transaction lines, no headers or explanations."""
    
    # Convert Windows path to forward slashes for compatibility
    image_path_unix = image_path.replace('\\', '/')
    
    cmd = [
        'opencode', 'run', prompt,
        '-m', 'openrouter/openai/gpt-4o-mini',
        '-f', image_path_unix
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    # Directory containing images
    image_dir = r"C:\Users\Phontan-Chang\Desktop\credit_statements\jpeg_converted"
    
    # Get all page 1 images (transaction pages)
    page1_images = sorted([f for f in os.listdir(image_dir) if f.endswith('_page_1.jpg')])
    
    print(f"Found {len(page1_images)} transaction pages to process\n")
    print("="*100)
    
    all_transactions = []
    
    for img_file in page1_images:
        img_path = os.path.join(image_dir, img_file)
        statement_name = img_file.replace('_page_1.jpg', '')
        
        print(f"\nProcessing: {statement_name}")
        print("-"*100)
        
        try:
            # Extract transactions using opencode
            result = extract_transactions_with_opencode(img_path)
            
            if result and not result.startswith('ERROR'):
                lines = result.split('\n')
                transaction_count = 0
                
                for line in lines:
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            trans_date = parts[0].strip()
                            post_date = parts[1].strip()
                            description = parts[2].strip()
                            amount = parts[3].strip()
                            
                            print(f"{trans_date:<12} {post_date:<12} {description:<50} {amount:>12}")
                            
                            all_transactions.append({
                                'statement': statement_name,
                                'transaction_date': trans_date,
                                'posting_date': post_date,
                                'description': description,
                                'amount': amount
                            })
                            transaction_count += 1
                
                print(f"\nFound {transaction_count} transactions")
            else:
                print(f"No transactions found or error: {result}")
                
        except Exception as e:
            print(f"Error processing {img_file}: {str(e)}")
    
    # Summary
    print("\n" + "="*100)
    print(f"\nTOTAL TRANSACTIONS EXTRACTED: {len(all_transactions)}")
    print("\nAll transactions have been extracted from page 1 of each statement.")
    print("(Page 2 contains payment slip information, no transactions)")
    
    # Save to CSV
    csv_path = r"C:\Users\Phontan-Chang\Desktop\credit_statements\all_transactions.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("Statement,Transaction Date,Posting Date,Description,Amount (THB)\n")
        for t in all_transactions:
            f.write(f"{t['statement']},{t['transaction_date']},{t['posting_date']},\"{t['description']}\",{t['amount']}\n")
    
    print(f"\nTransactions saved to: {csv_path}")

if __name__ == "__main__":
    main()
