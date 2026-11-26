
import os
import re
import json
import fitz
import pandas as pd
import pytesseract

from PIL import Image
from docx import Document


# Tesseract OCR configuration
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def make_fact(text, source, location, modality):
    """Convert extracted text into a standard evidence record."""

    text = str(text).strip()

    if not text:
        return None

    # Preserve the text without inventing facts.
    return {
        "entity": "",
        "attribute": "",
        "value": text,
        "source": os.path.basename(source),
        "location": location,
        "modality": modality,
        "extraction_quality": "MEDIUM",
        "raw_text": text
    }


def extract_pdf(path):
    facts = []

    with fitz.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            # OCR for scanned pages
            if not text:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )
                text = pytesseract.image_to_string(image).strip()

            fact = make_fact(
                text, path, f"Page {page_number}", "PDF"
            )

            if fact:
                facts.append(fact)

    return facts


def extract_image(path):
    image = Image.open(path)
    text = pytesseract.image_to_string(image)

    fact = make_fact(text, path, "Image", "IMAGE")
    return [fact] if fact else []


def extract_csv(path):
    facts = []
    df = pd.read_csv(path)

    for index, row in df.iterrows():
        text = " | ".join(
            f"{column}: {value}"
            for column, value in row.items()
            if pd.notna(value)
        )

        fact = make_fact(
            text, path, f"Row {index + 2}", "CSV"
        )

        if fact:
            facts.append(fact)

    return facts


def extract_excel(path):
    facts = []

    workbook = pd.ExcelFile(path)

    for sheet in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)

        for index, row in df.iterrows():
            text = " | ".join(
                f"{column}: {value}"
                for column, value in row.items()
                if pd.notna(value)
            )

            fact = make_fact(
                text,
                path,
                f"Sheet {sheet}, Row {index + 2}",
                "EXCEL"
            )

            if fact:
                facts.append(fact)

    return facts


def extract_docx(path):
    facts = []
    document = Document(path)

    for index, paragraph in enumerate(document.paragraphs, start=1):
        fact = make_fact(
            paragraph.text,
            path,
            f"Paragraph {index}",
            "WORD"
        )

        if fact:
            facts.append(fact)

    for table_index, table in enumerate(document.tables, start=1):
        for row_index, row in enumerate(table.rows, start=1):
            text = " | ".join(
                cell.text.strip() for cell in row.cells
            )

            fact = make_fact(
                text,
                path,
                f"Table {table_index}, Row {row_index}",
                "WORD"
            )

            if fact:
                facts.append(fact)

    return facts


def extract_json(path):
    facts = []

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    text = json.dumps(data, ensure_ascii=False, indent=2)

    fact = make_fact(text, path, "JSON document", "OTHER")

    if fact:
        facts.append(fact)

    return facts


def extract_txt(path):
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    fact = make_fact(text, path, "Text document", "OTHER")
    return [fact] if fact else []


def extract_files(file_paths):
    """Extract evidence from multiple local files."""

    all_facts = []

    for path in file_paths:
        try:
            if not os.path.isfile(path):
                print(f"File not found: {path}")
                continue

            extension = os.path.splitext(path)[1].lower()

            if extension == ".pdf":
                facts = extract_pdf(path)

            elif extension in [".png", ".jpg", ".jpeg"]:
                facts = extract_image(path)

            elif extension == ".csv":
                facts = extract_csv(path)

            elif extension in [".xlsx", ".xls"]:
                facts = extract_excel(path)

            elif extension == ".docx":
                facts = extract_docx(path)

            elif extension == ".json":
                facts = extract_json(path)

            elif extension == ".txt":
                facts = extract_txt(path)

            else:
                print(f"Unsupported file type: {path}")
                continue

            all_facts.extend(facts)

        except Exception as error:
            print(f"Error processing {path}: {error}")

    return all_facts
