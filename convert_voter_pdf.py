import pdfplumber
import pandas as pd
import re
import logging
import sys
from pathlib import Path
from typing import List, Dict

# ====================== LOGGING SETUP ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_to_csv.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================== CORE PARSER ======================
def parse_voter_line(line: str) -> Dict[str, str] | None:
    """Parse a single line from the PDF into a voter record."""
    line = line.strip()
    if not line or len(line) < 20:
        return None

    # Skip header/metadata lines
    skip_patterns = [
        r"^No\.", r"^Name", r"^State ID", r"^Precinct",
        r"^County Name", r"^Election Name", r"^Report",
        r"^From", r"^To", r"^ePulse", r"^Voter Check-in"
    ]
    if any(re.search(p, line, re.IGNORECASE) for p in skip_patterns):
        return None

    # Robust regex for: No.  Name  StateID  Precinct
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

# ====================== CONVERSION FUNCTION ======================
def convert_single_pdf(pdf_path: Path, output_csv: Path | None = None) -> int:
    """Convert one PDF to CSV. Returns number of unique records."""
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        print(f"❌ Error: PDF not found at {pdf_path}")
        return 0

    if output_csv is None:
        output_csv = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")

    logger.info(f"Starting conversion: {pdf_path.name} → {output_csv.name}")
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

                # Progress feedback
                if page_num % 10 == 0 or page_num == total_pages:
                    print(f"   → Page {page_num}/{total_pages} processed ({len(records)} records so far)")

    except Exception as e:
        logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
        print(f"❌ Error processing {pdf_path.name}: {e}")
        return 0

    if not records:
        print(f"⚠️ No voter records found in {pdf_path.name}")
        return 0

    # Create DataFrame and deduplicate
    df = pd.DataFrame(records)
    initial = len(df)
    df = df.drop_duplicates(subset=["State ID"], keep="first")
    final = len(df)

    if initial != final:
        logger.info(f"Removed {initial - final} duplicate State IDs")

    # Save CSV
    df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info(f"✅ SUCCESS: {final} unique records saved to {output_csv.name}")
    print(f"✅ Converted {pdf_path.name} → {output_csv.name} ({final} records)")

    return final

# ====================== INTERACTIVE MENU ======================
def main():
    print("=" * 70)
    print("   ELECTION VOTER CHECK-IN PDF → CSV CONVERTER")
    print("   (Works on Medina County 2026 and any similar PDFs)")
    print("=" * 70)
    print()

    while True:
        print("What would you like to do?")
        print("   1. Convert a single PDF file")
        print("   2. Convert ALL PDF files in a folder (bulk)")
        print("   3. Exit")
        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            # === SINGLE FILE MODE ===
            pdf_str = input("\nEnter full path to the PDF file (or drag & drop): ").strip().strip('"\'')
            pdf_path = Path(pdf_str)

            if not pdf_path.exists() or not pdf_path.is_file():
                print("❌ File not found or not a file. Please try again.")
                continue

            # Ask for custom output name (optional)
            default_out = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")
            out_str = input(f"\nOutput CSV name (press Enter for default '{default_out.name}'): ").strip()
            output_csv = Path(out_str) if out_str else default_out

            convert_single_pdf(pdf_path, output_csv)

        elif choice == "2":
            # === BULK FOLDER MODE ===
            folder_str = input("\nEnter full path to the folder containing PDFs: ").strip().strip('"\'')
            folder = Path(folder_str)

            if not folder.exists() or not folder.is_dir():
                print("❌ Folder not found. Please try again.")
                continue

            # Find all PDFs
            pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
            if not pdf_files:
                print("❌ No PDF files found in that folder.")
                continue

            print(f"\nFound {len(pdf_files)} PDF file(s). Starting bulk conversion...\n")

            success_count = 0
            total_records = 0
            for pdf_path in pdf_files:
                out_path = pdf_path.with_name(f"{pdf_path.stem}_converted.csv")
                records = convert_single_pdf(pdf_path, out_path)
                if records > 0:
                    success_count += 1
                    total_records += records

            print("\n" + "=" * 50)
            print(f"🎉 BULK CONVERSION COMPLETE!")
            print(f"   {success_count}/{len(pdf_files)} files converted")
            print(f"   Total unique voter records: {total_records}")
            print("=" * 50)

        elif choice == "3":
            print("\nThank you for using the Election Data Converter!")
            print("Your log file is at: pdf_to_csv.log")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

        print("\n" + "-" * 60)  # separator for next run

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user. Goodbye!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
