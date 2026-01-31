#!/usr/bin/env python3
"""
Format AI transactions for Google Sheets import
Structure: วันที่ | month(hide) | รายการ | ราคา | จำนวน | รวม
"""

import csv
from datetime import datetime

def parse_date(date_str):
    """Parse DD/MM/YY format and return date components."""
    try:
        day, month, year_short = date_str.split('/')
        year = '20' + year_short  # Convert YY to YYYY
        date_obj = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
        return date_obj
    except:
        return None

def get_month_thai(date_obj):
    """Get month name in Thai."""
    months_thai = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    return months_thai[date_obj.month - 1]

def format_for_google_sheets():
    """Format AI transactions for Google Sheets."""
    
    # Read AI transactions
    ai_transactions = []
    
    with open('all_transactions.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            desc = row['Description'].upper()
            amount = float(row['Amount (THB)'].replace(',', ''))
            
            # Check if it's an AI transaction
            is_ai = False
            service_name = ''
            
            if 'OPENROUTER' in desc:
                is_ai = True
                service_name = 'OpenRouter AI'
            elif 'GOOGLE' in desc and 'CLOUD' in desc:
                is_ai = True
                service_name = 'Google Cloud'
            elif 'ANTHROPIC' in desc:
                is_ai = True
                service_name = 'Anthropic AI'
            elif 'RUNPOD' in desc:
                is_ai = True
                service_name = 'RunPod GPU'
            elif 'KIE.AI' in desc or 'KIE AI' in desc:
                is_ai = True
                service_name = 'Kie.ai'
            elif 'BUDGIEAI' in desc or 'BUDGIE AI' in desc:
                is_ai = True
                service_name = 'BudgieAI'
            elif 'DIGITALOCEAN' in desc:
                is_ai = True
                service_name = 'DigitalOcean'
            elif 'STRIPE' in desc and 'Z.AI' in desc:
                is_ai = True
                service_name = 'Z.AI Service'
            
            if is_ai and amount > 0:  # Only positive amounts (expenses)
                trans_date = row['Transaction Date']
                date_obj = parse_date(trans_date)
                
                if date_obj:
                    month_name = get_month_thai(date_obj)
                    
                    ai_transactions.append({
                        'date': trans_date,
                        'month': month_name,
                        'description': service_name,
                        'price': amount,
                        'quantity': 1,
                        'total': amount
                    })
    
    # Sort by date
    ai_transactions.sort(key=lambda x: parse_date(x['date']) or datetime.min)
    
    # Write to CSV for Google Sheets import
    output_file = 'ai_transactions_for_sheets.csv'
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # Write header in Thai
        writer.writerow(['วันที่', 'month(hide)', 'รายการ', 'ราคา', 'จำนวน', 'รวม'])
        
        for t in ai_transactions:
            writer.writerow([
                t['date'],
                t['month'],
                t['description'],
                t['price'],
                t['quantity'],
                t['total']
            ])
    
    print(f"[OK] Formatted {len(ai_transactions)} AI transactions for Google Sheets")
    print(f"[OK] Saved to: {output_file}")
    print()
    print("Sample data:")
    print("-" * 80)
    print(f"{'วันที่':<12} {'month(hide)':<12} {'รายการ':<25} {'ราคา':>10} {'จำนวน':>6} {'รวม':>10}")
    print("-" * 80)
    
    for t in ai_transactions[:5]:
        print(f"{t['date']:<12} {t['month']:<12} {t['description']:<25} {t['price']:>10.2f} {t['quantity']:>6} {t['total']:>10.2f}")
    
    if len(ai_transactions) > 5:
        print(f"... and {len(ai_transactions) - 5} more rows")
    
    print()
    print("=" * 80)
    print("To import into Google Sheets:")
    print("1. Open Google Sheets")
    print("2. File > Import")
    print("3. Upload the file 'ai_transactions_for_sheets.csv'")
    print("4. Choose 'Replace spreadsheet' or 'Append to current sheet'")
    print("=" * 80)

if __name__ == "__main__":
    format_for_google_sheets()
