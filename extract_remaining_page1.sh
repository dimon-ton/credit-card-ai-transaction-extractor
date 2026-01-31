#!/bin/bash

for i in 2511-25-03 2511-25-04 2511-25-05 2511-25-06 2511-25-07 2511-25-08 2511-25-09 2511-25-10 2511-25-11 2511-25-12 2511-26-01; do
  echo "Processing ${i}_page_1.jpg"
  opencode run "Extract all transaction data from this credit card statement page. Return the data in CSV format with columns: Transaction Date, Posting Date, Description, Amount (THB). If no transaction data is found, state that." -m openrouter/openai/gpt-4o-mini -f "C:/Users/Phontan-Chang/Desktop/credit_statements/workflow_output/jpeg_converted/${i}_page_1.jpg"
  echo ""
done