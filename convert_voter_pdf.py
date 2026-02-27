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

# ====================== FLEXIBLE PARSER (supports both formats) ======================
def parse_voter_line(line: str) -> Dict[str, str] | None:
    line = line.strip()
    if not line or len(line) < 20:
        return None

    # Skip headers
    skip_patterns = [
        r"^No\.", r"^Name", r"^State ID", r"^Polling Place", r"^Precinct",
        r"^County Name", r"^Election Name", r"^Report", r"^From", r"^To",
        r"^ePulse", r"^Voter Check-in", r"^Website Post Report"
    ]
    if any(re.search(p, line, re.IGNORECASE) for p in skip_patterns):
        return None

    # Updated regex: captures optional Polling Place between State ID and Precinct
    # Works for both 4-column and 5-column PDFs
    pattern = r'^\s*(\d{1,4})\s+(.+?)\s+(\d{9,12})\s*(.*?)\s+(S\s+[\w\.\-]+)'
    match = re.search(pattern, line)
    if match:
        polling_place = match.group(4).strip() if match.group(4) else ""
        return {
            "No": match.group(1).strip(),
            "Name": match.group(2).strip(),
            "State ID": match.group(3).strip(),
            "Polling Place": polling_place,
            "Precinct": match.group(5).strip()
        }
    return None

# ====================== CONVERSION FUNCTION ======================
def convert_single_pdf(pdf_path: Path, output_csv: Path | None = None) -> int:
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        print(f"❌ Error: PDF not found at {pdf_path}")
        return 0

    if output_csv is None:
        output_csv = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")

    logger.info(f"Starting: {pdf_path.name} → {output_csv.name}")
    records: List[Dict[str, str]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not text:
                    continue
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                for line in lines:
                    parsed = parse_voter_line(line)
                    if parsed:
                        records.append(parsed)

                if page_num % 10 == 0 or page_num == total_pages:
                    print(f"   → Page {page_num}/{total_pages}  ({len(records)} records so far)")

    except Exception as e:
        logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
        print(f"❌ Error processing {pdf_path.name}: {e}")
        return 0

    if not records:
        print(f"⚠️ No voter records found in {pdf_path.name}")
        return 0

    df = pd.DataFrame(records)
    initial = len(df)
    df = df.drop_duplicates(subset=["State ID"], keep="first")
    final = len(df)

    if initial != final:
        logger.info(f"Removed {initial - final} duplicate State IDs")

    df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info(f"✅ SUCCESS: {final} records → {output_csv.name}")
    print(f"✅ Converted {pdf_path.name} → {output_csv.name} ({final} records)")

    return final

# ====================== INTERACTIVE MENU ======================
def main():
    print("=" * 75)
    print("   ELECTION VOTER CHECK-IN PDF → CSV CONVERTER")
    print("   Supports Medina County, Kerr County, and similar reports")
    print("=" * 75)
    print()

    while True:
        print("Choose an option:")
        print("   1. Convert a single PDF file")
        print("   2. Convert ALL PDFs in a folder (bulk)")
        print("   3. Exit")
        choice = input("\nEnter 1, 2, or 3: ").strip()

        if choice == "1":
            # Single file
            pdf_str = input("\nDrag & drop the PDF here or paste full path: ").strip().strip('"\'')
            pdf_path = Path(pdf_str)

            if not pdf_path.is_file():
                print("❌ File not found. Try again.")
                continue

            default_out = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")
            out_str = input(f"Output filename (Enter for default '{default_out.name}'): ").strip()
            output_csv = Path(out_str) if out_str else default_out

            convert_single_pdf(pdf_path, output_csv)

        elif choice == "2":
            # Bulk folder
            folder_str = input("\nDrag & drop the folder or paste full path: ").strip().strip('"\'')
            folder = Path(folder_str)

            if not folder.is_dir():
                print("❌ Folder not found.")
                continue

            pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
            if not pdf_files:
                print("❌ No PDF files found in folder.")
                continue

            print(f"\nFound {len(pdf_files)} PDF(s). Converting...\n")
            success = 0
            total_records = 0

            for pdf_path in pdf_files:
                out_path = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")
                records = convert_single_pdf(pdf_path, out_path)
                if records > 0:
                    success += 1
                    total_records += records

            print("\n" + "=" * 60)
            print(f"🎉 BULK CONVERSION FINISHED!")
            print(f"   {success}/{len(pdf_files)} files converted")
            print(f"   Total unique voter records: {total_records}")
            print("=" * 60)

        elif choice == "3":
            print("\nThank you for using the Election Data Converter!")
            print("Log saved to: pdf_to_csv.log")
            break
        else:
            print("❌ Please enter 1, 2, or 3.")

        print("\n" + "-" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
