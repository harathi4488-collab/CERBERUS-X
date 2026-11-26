r"""Standalone tests for the CERBERUS-X local file extractor.

Run with: .\.venv\Scripts\python.exe test_extractor.py
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import fitz
import pandas
from docx import Document
from PIL import Image, ImageDraw, ImageFont

import main
from modules.extractor import _find_tesseract, _run_ocr, extract_files


FACT_KEYS = {
    "entity",
    "attribute",
    "value",
    "source",
    "location",
    "modality",
    "extraction_quality",
    "raw_text",
}
OCR_AVAILABLE = _find_tesseract() is not None
SAMPLE_TEXT = "Rahul Kumar joining date: 10-12-2026"


def _sample_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), 76)
            except OSError:
                continue
    return ImageFont.load_default(size=48)


def _create_text_image(path: Path, image_format: str = "PNG") -> None:
    image = Image.new("RGB", (1700, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 55), SAMPLE_TEXT, fill="black", font=_sample_font())
    image.save(path, format=image_format)


class ExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="cerberus_extractor_test_"
        )
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)

    def _extract_and_display(self, path: Path) -> list[dict[str, Any]]:
        facts = extract_files([str(path)])
        self.assertTrue(facts, f"No facts or error record returned for {path.name}")
        for fact in facts:
            self.assertEqual(set(fact), FACT_KEYS)
            label = "ERROR" if fact["extraction_quality"] == "LOW" else "TEXT"
            print(
                f"  [{label}] {fact['source']} | {fact['location']} | "
                f"{fact['raw_text']}",
                flush=True,
            )
        return facts

    def test_pdf_text_and_page_locations(self) -> None:
        path = self.directory / "offer.pdf"
        with fitz.open() as document:
            document.new_page().insert_text((72, 72), SAMPLE_TEXT, fontsize=14)
            document.new_page().insert_text(
                (72, 72), "Department: Engineering", fontsize=14
            )
            document.save(path)

        print("\nPDF extraction:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(
            any(
                fact["source"] == "offer.pdf" and fact["location"] == "Page 1"
                for fact in facts
            )
        )
        self.assertTrue(
            any(
                fact["source"] == "offer.pdf" and fact["location"] == "Page 2"
                for fact in facts
            )
        )
        self.assertTrue(any(fact["value"] == "10-12-2026" for fact in facts))

    @unittest.skipUnless(
        OCR_AVAILABLE,
        "Install Tesseract OCR, add it to PATH, or set TESSERACT_CMD.",
    )
    def test_scanned_pdf_uses_ocr(self) -> None:
        image_path = self.directory / "scanned_page.png"
        _create_text_image(image_path)
        pdf_path = self.directory / "scanned.pdf"
        with fitz.open() as document:
            page = document.new_page(width=850, height=110)
            page.insert_image(page.rect, filename=str(image_path))
            document.save(pdf_path)

        print("\nScanned PDF OCR:", flush=True)
        facts = self._extract_and_display(pdf_path)
        self.assertTrue(
            any(
                fact["source"] == "scanned.pdf" and fact["location"] == "Page 1"
                for fact in facts
            )
        )
        self.assertIn("10-12-2026", " ".join(fact["raw_text"] for fact in facts))

    @unittest.skipUnless(
        OCR_AVAILABLE,
        "Install Tesseract OCR, add it to PATH, or set TESSERACT_CMD.",
    )
    def test_png_image_uses_ocr(self) -> None:
        path = self.directory / "employee.png"
        _create_text_image(path, "PNG")

        print("\nPNG image OCR:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(any(fact["modality"] == "IMAGE" for fact in facts))
        self.assertTrue(any(fact["source"] == "employee.png" for fact in facts))
        self.assertIn("10-12-2026", " ".join(fact["raw_text"] for fact in facts))

    @unittest.skipUnless(
        OCR_AVAILABLE,
        "Install Tesseract OCR, add it to PATH, or set TESSERACT_CMD.",
    )
    def test_jpg_image_uses_ocr(self) -> None:
        path = self.directory / "employee.jpg"
        _create_text_image(path, "JPEG")

        print("\nJPG image OCR:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(any(fact["modality"] == "IMAGE" for fact in facts))
        self.assertTrue(any(fact["source"] == "employee.jpg" for fact in facts))
        self.assertIn("10-12-2026", " ".join(fact["raw_text"] for fact in facts))

    def test_image_without_text_returns_error_fact(self) -> None:
        path = self.directory / "blank.png"
        Image.new("RGB", (64, 64), "white").save(path)

        with patch("modules.extractor._run_ocr", return_value=""):
            facts = self._extract_and_display(path)

        self.assertEqual(facts[0]["source"], "blank.png")
        self.assertEqual(facts[0]["extraction_quality"], "LOW")
        self.assertIn("No text was found by OCR", facts[0]["raw_text"])

    def test_csv_rows_and_column_names(self) -> None:
        path = self.directory / "employees.csv"
        pandas.DataFrame(
            [
                {"Name": "Rahul Kumar", "Joining Date": "10-12-2026"},
                {"Name": "Anita Rao", "Joining Date": "15-01-2027"},
            ]
        ).to_csv(path, index=False)

        print("\nCSV extraction:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(
            any(
                fact["attribute"] == "Joining Date"
                and fact["location"].endswith("Row 2, Column 'Joining Date'")
                for fact in facts
            )
        )
        self.assertTrue(any(fact["entity"] == "Anita Rao" for fact in facts))

    def test_xlsx_reads_all_sheets(self) -> None:
        path = self.directory / "employees.xlsx"
        with pandas.ExcelWriter(path, engine="openpyxl") as writer:
            pandas.DataFrame(
                [{"Name": "Rahul Kumar", "Department": "Engineering"}]
            ).to_excel(writer, sheet_name="Staff", index=False)
            pandas.DataFrame(
                [{"Name": "Anita Rao", "Department": "Operations"}]
            ).to_excel(writer, sheet_name="Contractors", index=False)

        print("\nXLSX extraction:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(
            any(
                fact["source"] == "employees.xlsx"
                and fact["location"]
                == "Sheet 'Staff', Row 2, Column 'Department'"
                and fact["value"] == "Engineering"
                for fact in facts
            )
        )
        self.assertTrue(
            any(
                fact["source"] == "employees.xlsx"
                and fact["location"]
                == "Sheet 'Contractors', Row 2, Column 'Department'"
                and fact["value"] == "Operations"
                for fact in facts
            )
        )

    def test_docx_paragraphs_and_tables(self) -> None:
        path = self.directory / "offer.docx"
        document = Document()
        document.add_paragraph(SAMPLE_TEXT)
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "Department"
        table.cell(0, 1).text = "Engineering"
        document.save(path)

        print("\nDOCX extraction:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(
            any(
                fact["source"] == "offer.docx"
                and fact["location"] == "Paragraph 1"
                and fact["raw_text"] == SAMPLE_TEXT
                for fact in facts
            )
        )
        self.assertTrue(
            any(
                fact["source"] == "offer.docx"
                and fact["location"] == "Table 1, Row 1"
                and fact["raw_text"] == "Department | Engineering"
                for fact in facts
            )
        )
        self.assertTrue(any(fact["value"] == "Engineering" for fact in facts))

    def test_empty_docx_returns_clear_error_fact(self) -> None:
        path = self.directory / "empty.docx"
        Document().save(path)

        facts = self._extract_and_display(path)

        self.assertEqual(facts[0]["source"], "empty.docx")
        self.assertEqual(facts[0]["extraction_quality"], "LOW")
        self.assertIn("no extractable text", facts[0]["raw_text"])

    def test_json_nested_field_paths(self) -> None:
        path = self.directory / "employee.json"
        path.write_text(
            json.dumps(
                {"employee": {"name": "Rahul Kumar", "joining_date": "10-12-2026"}}
            ),
            encoding="utf-8",
        )

        print("\nJSON extraction:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(
            any(fact["location"] == "$.employee.joining_date" for fact in facts)
        )
        self.assertTrue(any(fact["value"] == "10-12-2026" for fact in facts))

    def test_main_saves_readable_json_output(self) -> None:
        path = self.directory / "employee.json"
        path.write_text(
            json.dumps({"employee": {"name": "Rahul Kumar"}}),
            encoding="utf-8",
        )
        second_path = self.directory / "department.json"
        second_path.write_text(
            json.dumps({"department": "Engineering"}),
            encoding="utf-8",
        )
        output_directory = self.directory / "output"
        with (
            patch("main.OUTPUT_DIRECTORY", output_directory),
            patch("sys.argv", ["main.py", str(path), str(second_path)]),
        ):
            result = main.main()

        self.assertEqual(result, 0)
        output_path = output_directory / "output.json"
        self.assertTrue(output_path.is_file())
        saved_facts = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertTrue(saved_facts)
        self.assertEqual(set(saved_facts[0]), FACT_KEYS)
        self.assertEqual(
            {fact["source"] for fact in saved_facts},
            {"employee.json", "department.json"},
        )

    def test_txt_extracts_text(self) -> None:
        path = self.directory / "notes.txt"
        path.write_text(SAMPLE_TEXT, encoding="utf-8")

        print("\nTXT extraction:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(
            any(
                fact["source"] == "notes.txt"
                and fact["location"] == "Text"
                and fact["modality"] == "TEXT"
                and fact["raw_text"] == SAMPLE_TEXT
                for fact in facts
            )
        )

    def test_missing_tesseract_has_configuration_message(self) -> None:
        missing_executable = self.directory / "missing" / "tesseract.exe"
        with (
            patch.dict(
                os.environ,
                {"TESSERACT_CMD": str(missing_executable)},
                clear=True,
            ),
            patch("modules.extractor.shutil.which", return_value=None),
        ):
            with self.assertRaisesRegex(FileNotFoundError, "TESSERACT_CMD"):
                _run_ocr(None)

    def test_doc_without_libreoffice_returns_clear_error(self) -> None:
        path = self.directory / "legacy.doc"
        path.write_bytes(b"Legacy DOC placeholder")
        with patch("modules.extractor._find_libreoffice", return_value=None):
            facts = self._extract_and_display(path)

        self.assertEqual(facts[0]["source"], "legacy.doc")
        self.assertEqual(facts[0]["extraction_quality"], "LOW")
        self.assertIn("LibreOffice is unavailable", facts[0]["raw_text"])

    def test_corrupt_file_error_does_not_crash_extractor(self) -> None:
        path = self.directory / "corrupt.pdf"
        path.write_bytes(b"not a valid PDF")

        print("\nCorrupt PDF error handling:", flush=True)
        facts = self._extract_and_display(path)
        self.assertTrue(any(fact["extraction_quality"] == "LOW" for fact in facts))

    def test_missing_file_error_does_not_stop_later_files(self) -> None:
        missing_path = self.directory / "missing.pdf"
        valid_path = self.directory / "valid.json"
        valid_path.write_text(json.dumps({"status": "ready"}), encoding="utf-8")

        facts = extract_files([str(missing_path), str(valid_path)])

        self.assertTrue(
            any(
                fact["source"] == "missing.pdf"
                and fact["extraction_quality"] == "LOW"
                and "does not exist" in fact["raw_text"]
                for fact in facts
            )
        )
        self.assertTrue(
            any(fact["source"] == "valid.json" and fact["value"] == "ready" for fact in facts)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
