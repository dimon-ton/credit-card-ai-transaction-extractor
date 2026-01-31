# Credit Card Statement AI Transaction Extractor

Automatically extracts AI-related transactions from KTC credit card statement PDFs using AI vision (Opencode + Kimi K2.5).

## Features

- **PDF to Image Conversion**: Converts credit card statement PDFs to high-quality JPEG images
- **AI-Powered Extraction**: Uses Opencode CLI with Kimi K2.5 model to extract transactions
- **AI Transaction Filtering**: Automatically identifies AI-related expenses (OpenRouter, Anthropic, Google Cloud, RunPod, etc.)
- **CSV Export**: Outputs filtered AI transactions in Google Sheets-compatible format

## Workflow

1. **Input**: Credit card statement PDFs (2511-25-01.pdf, etc.)
2. **PDF Conversion**: Convert PDFs to JPEG images (2 pages per statement)
3. **Transaction Extraction**: Use AI to extract all transactions from images
4. **AI Filtering**: Identify and filter only AI-related transactions
5. **Output**: CSV file with AI transactions ready for Google Sheets

## Usage

### Quick Start

```bash
# Run the automated workflow
python ai_workflow_brain.py

# Or use the bash script
bash batch_extract.sh
```

### Manual Steps

1. **Convert PDFs to Images**:
```bash
python pdf_converter.py
```

2. **Extract Transactions**:
```bash
bash batch_extract.sh
```

3. **Filter AI Transactions**:
```bash
python format_for_sheets.py
```

## AI Services Detected

- **OpenRouter AI** - AI API service (13 transactions, 2,616.50 THB)
- **Google Cloud** - Cloud computing (4 transactions, 861.80 THB)
- **Anthropic AI** - Claude AI service (2 transactions, 362.67 THB)
- **RunPod GPU** - GPU cloud computing (2 transactions, 663.36 THB)
- **Kie.ai** - AI service (2 transactions, 331.30 THB)
- **BudgieAI** - AI service (172.19 THB)
- **DigitalOcean** - Cloud hosting (216.86 THB)
- **Z.AI Service** - AI service (213.35 THB)

## Total AI Spending

**5,438.03 THB** (25 transactions)

## Output Format

CSV file with columns:
- `วันที่` (Date) - DD/MM/YY format
- `month(hide)` - Month name
- `รายการ` (Description) - AI service name
- `ราคา` (Price) - Amount in THB
- `จำนวน` (Quantity) - Always 1
- `รวม` (Total) - Same as price

## Requirements

- Python 3.x
- PyMuPDF (fitz)
- Opencode CLI
- Kimi K2.5 model access

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install PyMuPDF

# Install Opencode CLI
# Follow instructions at: https://opencode.ai
```

## License

MIT

## Author

Created for automated credit card statement analysis
