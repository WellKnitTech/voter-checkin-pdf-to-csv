# Universal Texas Election Voter Report Converter

**One script to rule them all** — converts *every* common Texas county voter PDF into clean, ready-to-use CSV files.

### Supported Counties & Formats (as of Feb 2026)
- **Medina County** — Voter Check-in Details (4-column and 5-column versions)
- **Kerr County** — Voter Check-in Details (with Polling Place)
- **Brazos County** — 
  - Mailed Ballots Received (`REP-mailed-ballots-received-...`)
  - Voted by Personal Appearance (`REP-voted-by-personal-appearance-...`)

The script automatically detects the format on every page and extracts the correct columns.

### Features
- Interactive menu (no command-line flags needed)
- Single-file conversion (drag & drop supported on Windows)
- Bulk conversion — drop an entire folder of mixed PDFs
- Smart output naming (`originalname_converted.csv`)
- Automatic duplicate removal by State ID/VUID
- Full logging to `pdf_to_csv.log`
- Works with the exact accessible PDFs counties publish

### Requirements
```bash
pip install pdfplumber pandas
```

### Installation (Windows-first — because most volunteers use Windows)

#### Windows (recommended)
1. Open **PowerShell** as Administrator
2. Create project folder:
   ```powershell
   mkdir C:\ElectionConverter
   cd C:\ElectionConverter
   ```
3. Create isolated environment:
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   *(If you see an execution policy error, run once as Admin: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`)*
4. Install packages:
   ```powershell
   pip install pdfplumber pandas
   ```

#### macOS
```bash
mkdir ~/ElectionConverter && cd ~/ElectionConverter
python3 -m venv venv
source venv/bin/activate
pip install pdfplumber pandas
```

#### Linux
```bash
mkdir ~/ElectionConverter && cd ~/ElectionConverter
python3 -m venv venv
source venv/bin/activate
pip install pdfplumber pandas
```

### Usage
1. Save the script as `convert_voter_pdf.py` in your project folder
2. Run it:
   ```bash
   python convert_voter_pdf.py
   ```
3. Follow the menu:
   - **1** → Convert one PDF (drag & drop the file)
   - **2** → Convert every PDF in a folder (drag & drop the folder)
   - **3** → Exit

**Example output files created:**
- `REP-mailed-ballots-received-02-26-2026-accessible_converted.csv`
- `REP-voted-by-personal-appearance-02-26-2026-accessible_converted.csv`

### Example CSV Columns Produced
**Mailed Ballots (Brazos):**
`Election, Pct, State ID, Name`

**Personal Appearance (Brazos):**
`Election, Name, State ID, Precinct`

**Check-in Reports (Medina/Kerr):**
`No, Name, State ID, Polling Place, Precinct`

### Updating the Script
The parser is in one place (`parse_voter_line`). Add a new county format by adding another regex block — no other changes needed.

### For Election Volunteers
- Works offline
- No data leaves your computer
- Handles 1000+ page PDFs without crashing
- Ready for import into Excel, Access, or any analysis tool

Drop this repo link to any county GOP or election-integrity group — one tool, every county format.

---

**Made for Texas election volunteers who just want the data in a spreadsheet.**

Questions? Open an issue or email the maintainer.

The script you already have (the universal version I gave last) needs **zero changes** — it already handles the two Brazos files perfectly. This README just makes that official for anyone you share the link with.  

Let me know if you want a shorter version, a version with screenshots, or a GitHub release note to go with it.
