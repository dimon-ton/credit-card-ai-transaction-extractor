#!/bin/bash
# Automated Workflow: PDF Credit Card Statements → AI Transactions CSV
# Usage: ./ai_transaction_workflow.sh [pdf_directory]

set -e  # Exit on error

# Configuration
INPUT_DIR="${1:-.}"  # Default to current directory if not specified
OUTPUT_DIR="workflow_output"
JPEG_DIR="$OUTPUT_DIR/jpeg_converted"
CSV_FILE="$OUTPUT_DIR/ai_transactions.csv"

# Colors for output (using ASCII instead of Unicode)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "AI Transaction Extraction Workflow"
echo "========================================"
echo ""

# Step 1: Check for PDF files
echo "[STEP 1] Checking for PDF files..."
PDF_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -name "*.pdf" | wc -l)

if [ "$PDF_COUNT" -eq 0 ]; then
    echo "${RED}[ERROR] No PDF files found in $INPUT_DIR${NC}"
    exit 1
fi

echo "[OK] Found $PDF_COUNT PDF file(s)"

# Step 2: Create output directories
echo ""
echo "[STEP 2] Creating output directories..."
mkdir -p "$JPEG_DIR"
echo "[OK] Created: $OUTPUT_DIR"

# Step 3: Convert PDFs to JPEG
echo ""
echo "[STEP 3] Converting PDFs to JPEG images..."

for pdf_file in "$INPUT_DIR"/*.pdf; do
    if [ -f "$pdf_file" ]; then
        filename=$(basename "$pdf_file" .pdf)
        echo "  Converting: $filename.pdf"
        
        # Use Python with PyMuPDF to convert PDF to images
        python3 << EOF
import fitz
import os

pdf_path = "$pdf_file"
output_dir = "$JPEG_DIR"
filename = "$filename"

try:
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        output_path = os.path.join(output_dir, f"{filename}_page_{page_num + 1}.jpg")
        pix.save(output_path)
    pdf_document.close()
    print(f"    [OK] Converted {len(pdf_document)} page(s)")
except Exception as e:
    print(f"    [ERROR] {e}")
EOF
    fi
done

# Count converted images
IMAGE_COUNT=$(find "$JPEG_DIR" -name "*.jpg" | wc -l)
echo "[OK] Converted $IMAGE_COUNT images"

# Step 4: Extract transactions using opencode
echo ""
echo "[STEP 4] Extracting transactions from images..."

# Create temporary file for all transactions
TEMP_FILE=$(mktemp)
echo "Statement ID,Page,Transaction Date,Posting Date,Description,Amount (THB)" > "$TEMP_FILE"

# Process each image
for img_file in "$JPEG_DIR"/*.jpg; do
    if [ -f "$img_file" ]; then
        filename=$(basename "$img_file")
        
        # Extract statement ID and page number
        if [[ $filename =~ ([0-9]{4}-[0-9]{2}-[0-9]{2})_page_([0-9]+)\.jpg ]]; then
            statement_id="${BASH_REMATCH[1]}"
            page_num="${BASH_REMATCH[2]}"
        else
            statement_id="${filename%.jpg}"
            page_num="1"
        fi
        
        echo "  Processing: $filename"
        
        # Use opencode to extract transactions
        result=$(opencode run "Extract all transaction data from this credit card statement. Return in format: DATE|POSTING_DATE|DESCRIPTION|AMOUNT (one per line). If no transactions, return NO_TRANSACTIONS only." -m kimi-for-coding/k2p5 -f "$img_file" 2>/dev/null)
        
        # Parse and save transactions
        if echo "$result" | grep -qE '^[0-9]{2}/[0-9]{2}/[0-9]{2}\|'; then
            echo "$result" | grep -E '^[0-9]{2}/[0-9]{2}/[0-9]{2}\|' | while IFS='|' read -r trans_date post_date description amount; do
                # Clean up fields
                trans_date=$(echo "$trans_date" | xargs)
                post_date=$(echo "$post_date" | xargs)
                description=$(echo "$description" | xargs)
                amount=$(echo "$amount" | xargs)
                
                # Add to temp file
                echo "\"$statement_id\",\"$page_num\",\"$trans_date\",\"$post_date\",\"$description\",\"$amount\"" >> "$TEMP_FILE"
            done
            echo "    [OK] Transactions extracted"
        else
            echo "    [INFO] No transactions or payment slip"
        fi
        
        # Small delay to avoid rate limiting
        sleep 1
    fi
done

# Step 5: Filter AI transactions
echo ""
echo "[STEP 5] Filtering AI-related transactions..."

python3 << EOF
import csv
import re

input_file = "$TEMP_FILE"
output_file = "$CSV_FILE"

# AI service keywords
ai_keywords = [
    'OPENROUTER', 'ANTHROPIC', 'RUNPOD', 'KIE.AI', 'KIE AI',
    'BUDGIEAI', 'BUDGIE AI', 'DIGITALOCEAN', 'STRIPE.*Z\\.AI',
    'GOOGLE.*CLOUD'
]

ai_transactions = []

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        desc = row['Description'].upper()
        
        # Check if it's an AI transaction
        is_ai = False
        for keyword in ai_keywords:
            if re.search(keyword, desc):
                is_ai = True
                break
        
        if is_ai:
            try:
                amount = float(row['Amount (THB)'].replace(',', ''))
                if amount > 0:  # Only expenses (positive amounts)
                    ai_transactions.append(row)
            except:
                pass

# Write AI transactions to CSV
with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
    if ai_transactions:
        writer = csv.DictWriter(f, fieldnames=ai_transactions[0].keys())
        writer.writeheader()
        writer.writerows(ai_transactions)

print(f"[OK] Found {len(ai_transactions)} AI transactions")
EOF

# Step 6: Generate summary
echo ""
echo "[STEP 6] Generating summary..."

python3 << EOF
import csv
from datetime import datetime

# Read AI transactions
ai_services = {}
total_amount = 0

with open("$CSV_FILE", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
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
print("")
print("=" * 70)
print("AI TRANSACTION SUMMARY")
print("=" * 70)
print("")

for service, data in sorted(ai_services.items(), key=lambda x: x[1]['total'], reverse=True):
    print(f"{service:.<50} {data['count']:>3} txns  {data['total']:>10,.2f} THB")

print("")
print("-" * 70)
print(f"{'TOTAL':.<50} {sum(d['count'] for d in ai_services.values()):>3} txns  {total_amount:>10,.2f} THB")
print("=" * 70)
EOF

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "========================================"
echo "WORKFLOW COMPLETE"
echo "========================================"
echo ""
echo "Output files:"
echo "  - All transactions: $TEMP_FILE (deleted)"
echo "  - AI transactions: $CSV_FILE"
echo "  - Converted images: $JPEG_DIR/"
echo ""
echo "To import into Google Sheets:"
echo "  1. Open Google Sheets"
echo "  2. File > Import"
echo "  3. Upload: $CSV_FILE"
echo "  4. Choose 'Replace spreadsheet' or 'Append to current sheet'"
echo ""
