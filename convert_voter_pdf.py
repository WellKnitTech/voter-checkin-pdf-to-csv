import pdfplumber
import pandas as pd
import re
import logging
import sys
from pathlib import Path
from typing import List, Dict

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_to_csv.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================== UNIVERSAL PARSER (all 4 formats) ======================
def parse_voter_line(line: str) -> Dict[str, str] | None:
    line = line.strip()
    if not line or len(line) < 15:
        return None

    # Skip headers
    if any(h in line.upper() for h in ["NO.", "NAME", "STATE ID", "POLLING PLACE", "PRECINCT", "VUID", "PCT", "SELECTED ELECTION", "VOTED BY PERSONAL APPEARANCE", "MAILED BALLOTS"]):
        return None

    # Pattern 1: Check-in (Medina/Kerr) - No, Name, State ID, [Polling Place], Precinct
    m = re.search(r'^\s*(\d{1,4})\s+(.+?)\s+(\d{9,12})\s*(.*?)\s+(S\s+[\w\.\-]+)', line)
    if m:
        return {
            "No": m.group(1).strip(),
            "Name": m.group(2).strip(),
            "State ID": m.group(3).strip(),
            "Polling Place": m.group(4).strip() if m.group(4).strip() else "",
            "Precinct": m.group(5).strip()
        }

    # Pattern 2: Mailed Ballots - Election, Pct, VUID, Voter Name
    m = re.search(r'^(2026 REPUBLICAN PRIMARY)\s+(\d{1,3})\s+(\d{9,12})\s+(.+)$', line)
    if m:
        return {
            "Election": m.group(1).strip(),
            "Pct": m.group(2).strip(),
            "State ID": m.group(3).strip(),
            "Name": m.group(4).strip()
        }

    # Pattern 3: Personal Appearance - Election, Name, State ID, Precinct
    m = re.search(r'^(2026 REPUBLICAN PRIMARY)\s+(.+?)\s+(\d{9,12})\s+(\d{1,3})$', line)
    if m:
        return {
            "Election": m.group(1).strip(),
            "Name": m.group(2).strip(),
            "State ID": m.group(3).strip(),
            "Precinct": m.group(4).strip()
        }

    return None

# ====================== CONVERSION ======================
def convert_single_pdf(pdf_path: Path, output_csv: Path | None = None) -> int:
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return 0

    if output_csv is None:
        output_csv = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")

    print(f"Processing: {pdf_path.name}")
    records: List[Dict[str, str]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not text:
                    continue
                lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
                for line in lines:
                    parsed = parse_voter_line(line)
                    if parsed:
                        records.append(parsed)

                if page_num % 10 == 0 or page_num == len(pdf.pages):
                    print(f"   → Page {page_num}/{len(pdf.pages)}  ({len(records)} records)")

    except Exception as e:
        print(f"❌ Error reading {pdf_path.name}: {e}")
        return 0

    if not records:
        print(f"⚠️ No records found in {pdf_path.name}")
        return 0

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["State ID"], keep="first")   # safe for all formats

    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"✅ Saved {len(df)} records → {output_csv.name}\n")
    return len(df)

# ====================== MENU ======================
def main():
    print("=" * 80)
    print("   UNIVERSAL ELECTION REPORT CONVERTER")
    print("   (Medina, Kerr, Mailed Ballots, Personal Appearance)")
    print("=" * 80)

    while True:
        print("\n1. Convert single PDF")
        print("2. Convert all PDFs in a folder (bulk)")
        print("3. Exit")
        choice = input("\nChoose 1-3: ").strip()

        if choice == "1":
            path_str = input("\nDrag & drop PDF or paste path: ").strip().strip('"\'')
            pdf_path = Path(path_str)
            if not pdf_path.is_file():
                print("❌ File not found")
                continue
            default_out = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")
            out_name = input(f"Output name (Enter for default): ").strip()
            out_path = Path(out_name) if out_name else default_out
            convert_single_pdf(pdf_path, out_path)

        elif choice == "2":
            folder_str = input("\nDrag & drop folder or paste path: ").strip().strip('"\'')
            folder = Path(folder_str)
            if not folder.is_dir():
                print("❌ Folder not found")
                continue
            pdfs = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
            if not pdfs:
                print("❌ No PDFs found")
                continue
            print(f"\nFound {len(pdfs)} PDFs – starting bulk conversion...\n")
            total = 0
            for p in pdfs:
                out = p.with_name(f"{p.stem}_converted.csv")
                total += convert_single_pdf(p, out)
            print(f"\n🎉 FINISHED! Total records across all files: {total}")

        elif choice == "3":
            print("\nThank you – log saved to pdf_to_csv.log")
            break
        else:
            print("Please enter 1, 2, or 3")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
