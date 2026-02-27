```markdown
# Voter Check-In PDF to CSV Converter

**Convert official election voter check-in PDFs into clean, usable CSV files in seconds.**

Works perfectly on the 86-page Medina County, Texas 2026 Joint Primary Election “Voter Check-in Details with Signatures” report and any similar county PDFs.

## Why This Tool Exists
Election officials often release data only as scanned PDFs. This script turns them into spreadsheets you can open in Excel, Google Sheets, or any analysis tool — with zero manual typing.

## Features
- Extracts **No.**, **Name**, **State ID**, **Precinct**
- Automatically removes duplicate State IDs
- Full processing log (`pdf_to_csv.log`)
- 100% offline — nothing is sent anywhere
- Works on Windows, macOS, and Linux

## Quick Start (5 minutes)

### 1. Create a virtual environment
**Windows**
```cmd
mkdir voter-converter
cd voter-converter
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**
```bash
mkdir voter-converter
cd voter-converter
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install pdfplumber pandas
```

### 3. Save the script
Create a file named `convert_voter_pdf.py` and paste the code from below.

### 4. Run it
```bash
python convert_voter_pdf.py
```
(or `python3 convert_voter_pdf.py` on macOS/Linux)

Your CSV will appear as `medina_county_voter_checkins_2026_primary.csv`.

## The Script (`convert_voter_pdf.py`)

```python
import pdfplumber
import pandas as pd
import re
import logging
import sys
from pathlib import Path
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_to_csv.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_voter_line(line: str) -> Dict[str, str] | None:
    line = line.strip()
    if not line or len(line) < 20:
        return None
    skip_patterns = [
        r"^No\.", r"^Name", r"^State ID", r"^Precinct",
        r"^County Name", r"^Election Name", r"^Report",
        r"^From", r"^To", r"^ePulse", r"^Voter Check-in"
    ]
    if any(re.search(p, line, re.IGNORECASE) for p in skip_patterns):
        return None
    pattern = r'^\s*(\d{1,4})\s+(.+?)\s+(\d{9,12})\s+(S\s+[\w\.\-]+)'
    match = re.search(pattern, line)
    if match:
        return {
            "No": match.group(1).strip(),
            "Name": match.group(2).strip(),
            "State ID": match.group(3).strip(),
            "Precinct": match.group(4).strip()
        }
    return None

def convert_pdf_to_csv(pdf_path: str, output_csv: str = "medina_county_voter_checkins_2026_primary.csv") -> int:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    logger.info(f"Starting extraction from {pdf_path}")
    records: List[Dict[str, str]] = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not text:
                    continue
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                for line in lines:
                    parsed = parse_voter_line(line)
                    if parsed:
                        records.append(parsed)
                if page_num % 10 == 0 or page_num == len(pdf.pages):
                    logger.info(f"Processed page {page_num}/{len(pdf.pages)} - {len(records)} records found")
    except Exception as e:
        logger.error(f"Error during PDF processing: {e}", exc_info=True)
        raise
    
    if not records:
        logger.warning("No voter records parsed.")
        return 0
    
    df = pd.DataFrame(records)
    initial_count = len(df)
    df = df.drop_duplicates(subset=["State ID"], keep="first")
    final_count = len(df)
    
    if initial_count != final_count:
        logger.info(f"Removed {initial_count - final_count} duplicate records")
    
    df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info(f"Success: {final_count} unique records saved to {output_csv}")
    return final_count

if __name__ == "__main__":
    pdf_file = "voter_check_in_details00.pdf"  # Change only if your filename differs
    try:
        count = convert_pdf_to_csv(pdf_file)
        print(f"\nConversion complete! {count} voter records saved.")
    except Exception as e:
        print(f"Failed: {e}")
```

## requirements.txt
```
pdfplumber
pandas
```

## How to Use with Your Own PDF
1. Put your PDF in the same folder.
2. Edit the line `pdf_file = "yourfile.pdf"` at the bottom of the script.
3. Run it.

## License
This project is MIT — use it, share it, improve it freely.

---

**Made for election volunteers and transparency groups.**  
Star the repo if it helps you!
