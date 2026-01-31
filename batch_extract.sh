#!/bin/bash
# Batch extract transactions from all credit card statement images
# This script processes each image file one by one

IMAGE_DIR="jpeg_converted"
OUTPUT_FILE="all_transactions.csv"

# Create CSV header
echo "Statement ID,Page,Transaction Date,Posting Date,Description,Amount (THB)" > "$OUTPUT_FILE"

# Counter
count=0
total=$(ls -1 "$IMAGE_DIR"/*.jpg 2>/dev/null | wc -l)

echo "Found $total images to process"
echo "========================================"

# Process each image
for img_file in "$IMAGE_DIR"/*.jpg; do
    count=$((count + 1))
    filename=$(basename "$img_file")
    
    # Extract statement ID and page number
    if [[ $filename =~ ([0-9]{4}-[0-9]{2}-[0-9]{2})_page_([0-9]+)\.jpg ]]; then
        statement_id="${BASH_REMATCH[1]}"
        page_num="${BASH_REMATCH[2]}"
    else
        statement_id="${filename%.jpg}"
        page_num="1"
    fi
    
    echo ""
    echo "[$count/$total] Processing: $filename ($statement_id - Page $page_num)"
    echo "----------------------------------------"
    
    # Run opencode to extract transactions
    result=$(opencode run "Extract all transaction data from this credit card statement. Format: DATE|POSTING_DATE|DESCRIPTION|AMOUNT (one per line). If no transactions, return NO_TRANSACTIONS only." -m kimi-for-coding/k2p5 -f "$img_file" 2>&1)
    
    # Check if result contains transactions
    if echo "$result" | grep -q "NO_TRANSACTIONS"; then
        echo "  [OK] No transactions on this page (payment slip)"
    elif echo "$result" | grep -qE '[0-9]{2}/[0-9]{2}/[0-9]{2}\|'; then
        # Extract transaction lines
        echo "$result" | grep -E '^[0-9]{2}/[0-9]{2}/[0-9]{2}\|' | while IFS='|' read -r trans_date post_date description amount; do
            # Clean up fields
            trans_date=$(echo "$trans_date" | xargs)
            post_date=$(echo "$post_date" | xargs)
            description=$(echo "$description" | xargs)
            amount=$(echo "$amount" | xargs)
            
            # Add to CSV
            echo "\"$statement_id\",\"$page_num\",\"$trans_date\",\"$post_date\",\"$description\",\"$amount\"" >> "$OUTPUT_FILE"
            echo "    $trans_date | $post_date | ${description:0:40} | $amount"
        done
        echo "  [OK] Transactions extracted"
    else
        echo "  [WARN] No valid transactions found"
    fi
    
    # Small delay
    sleep 1
done

echo ""
echo "========================================"
echo "Processing complete!"
echo "Transactions saved to: $OUTPUT_FILE"
