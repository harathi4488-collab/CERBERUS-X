# CERBERUS-X File Extractor

CERBERUS-X extracts text and conservative, source-located facts from local
documents and images. It does not infer facts that are not explicitly present
in the extracted text.

## Supported formats

| Format | Extraction |
| --- | --- |
| PDF | Extracts embedded text with PyMuPDF; OCRs pages without embedded text |
| JPG, JPEG, PNG | OCR with Tesseract |
| DOCX | Extracts paragraphs and table rows |
| DOC | Converts with LibreOffice, when LibreOffice is installed |
| XLSX | Reads values from all sheets |
| CSV | Reads rows and column values |
| TXT | Reads UTF-8 text files |
| JSON | Extracts scalar values with their JSON paths |

Each extracted fact has `entity`, `attribute`, `value`, `source`, `location`,
`modality`, `extraction_quality`, and `raw_text` fields. `source` is the input
filename. Locations include page, sheet/row/column, paragraph/table, or JSON
path information where applicable. When extraction fails, the extractor
returns a low-quality error fact and continues with the remaining files.

## Windows setup

1. Install Python 3.13 and make sure the Python launcher (`py`) is available.
2. Install Tesseract OCR separately. It is required for JPG/PNG OCR and scanned
   PDF pages; installing the Python package alone does not install Tesseract.
3. Optional: install LibreOffice if you need legacy `.doc` conversion. DOCX
   extraction does not require LibreOffice.
4. Open PowerShell in the project folder and create the virtual environment:

   ```powershell
   py -3.13 -m venv .venv
   ```

5. Install the pinned Python dependencies into that environment:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

No activation step is required. The commands below use the virtual environment
directly.

### Configure Tesseract

The extractor looks for Tesseract in this order:

1. The `TESSERACT_CMD` environment variable.
2. `tesseract` on `PATH`.
3. Common Windows installation directories under `ProgramFiles`,
   `ProgramFiles(x86)`, and `LOCALAPPDATA`.

If Tesseract is installed somewhere else, set its full executable path in the
current PowerShell window (adjust the path to your installation):

```powershell
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

If OCR is requested and Tesseract cannot be found, CERBERUS-X returns a clear
error fact explaining that Tesseract must be installed, added to `PATH`, or
configured with `TESSERACT_CMD`.

## Run the tests

Install Tesseract first to run all OCR tests rather than having them skipped:

```powershell
.\.venv\Scripts\python.exe test_extractor.py
```

Tests create their sample documents in temporary folders and do not overwrite
project or user documents.

## Run extraction

Pass one or more paths to the extractor. Use quotes around paths containing
spaces:

```powershell
.\.venv\Scripts\python.exe main.py "samples\offer.pdf" "samples\offer.docx" "samples\staff.xlsx" "samples\scan.jpg" "samples\notes.txt"
```

The extracted facts are printed in the terminal and saved as readable UTF-8
JSON to `output\output.json`. The `output` folder is created automatically;
the file is replaced on each run.

Example output fact:

```json
{
  "entity": null,
  "attribute": "department",
  "value": "Engineering",
  "source": "offer.docx",
  "location": "Paragraph 1",
  "modality": "WORD",
  "extraction_quality": "HIGH",
  "raw_text": "Department: Engineering"
}
```

## Extraction notes and limitations

- Text extraction preserves source names and locations; OCR quality depends on
  image resolution, contrast, orientation, and the language data installed
  with Tesseract.
- Fact parsing is intentionally conservative: it recognizes explicit
  label/value text and otherwise retains the raw extracted line without
  inventing an entity or attribute.
- Legacy `.doc` files require LibreOffice. If it is unavailable or conversion
  fails, an error fact is returned; DOCX support is unaffected.
- The project has been tested with the Python and dependency versions pinned in
  `requirements.txt` on the development Windows environment. It has not been
  tested on a separate laptop; install the external software and run the test
  command above on the target machine before relying on its OCR results.
