# PDF Document Reconstructor

Reconstructs recovered PDFs into **editable** `.docx` files, as close as possible to the lost original. Everything runs **locally and offline**: no PDF ever leaves your computer.

> **Reconstruction ≠ recovery.** The *content* (text, fonts, images, positions) is recovered from the PDF. The *internal structure* of the original DOCX (styles, fields, breaks, automatic numbering) no longer exists in the PDF and is **inferred**. The program measures how similar the result is to the original and reports where it failed.

**Status:** MVP (Phases 1–5 and validation of Phase 9) for PDFs with real text, with a graphical interface. See [Known limitations](#known-limitations-of-this-version).

---

## Installation (Windows)

Requirements: **Python 3.10 or later** ([python.org](https://www.python.org/downloads/) — check *Add python.exe to PATH*).

```bat
cd pdf_document_reconstructor
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For **visual validation** (rendering the DOCX back to PDF and comparing), you need a renderer:

| Option                   | How to install                                                                                    | Notes                                                                  |
|--------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| **LibreOffice** (default) | `winget install TheDocumentFoundation.LibreOffice` or [libreoffice.org](https://www.libreoffice.org) | Free, offline. May differ slightly from Word.                          |
| **Microsoft Word**       | `pip install docx2pdf` (Word must be installed)                                                   | The most faithful to what you see when opening the DOCX. Use `--renderer word`. |

Without either of these, the DOCX is still generated normally; only the visual comparison is skipped (and the report warns about it).

## Usage

### Command line

```bat
:: one file
python main.py document.pdf

:: whole folder (processes everything in input\ and writes to output\)
python main.py --input .\input --output .\output

:: choose the mode
python main.py document.pdf --mode editable      :: prioritizes editing
python main.py document.pdf --mode visual        :: prioritizes appearance
python main.py document.pdf --mode balanced      :: default

:: other options
python main.py document.pdf --renderer word --no-validate --keep-temp -v
```

### What is generated

```
output/document.docx                         ← the reconstructed file
reports/document/relatorio.html              ← open in a browser (quality, fonts, issues, comparison)
reports/document/relatorio.json              ← same data, for automation
reports/document/documento_reconstruido.pdf  ← the DOCX rendered back to PDF
reports/document/comparacao/                 ← original_page_01.png, reconstructed_page_01.png, difference_page_01.png
reports/document/modelo.json                 ← intermediate model (for debugging without reprocessing)
reports/document/processamento.log           ← detailed log
```

In the `difference_page_XX.png` map: **gray** = identical · **red** = present in the original but missing from the reconstruction · **blue** = extra or shifted.

If a PDF fails (corrupted, password-protected, not a PDF), the error is logged and the batch **keeps going**. In the final table, `!` marks files with serious problems: **read the report before trusting the result**.

### The three modes

| Mode                | Line spacing                      | Line breaks                         | Use for                                        |
|---------------------|-----------------------------------|-------------------------------------|------------------------------------------------|
| `balanced` (default)| "at least" X pt                   | Word reflows them                   | best compromise                                |
| `editable`          | **multiple** (1.0 / 1.15 / 1.5…)  | Word reflows them                   | comfortable editing; follows the font size     |
| `visual`            | **exact** X pt                    | **locked** to original positions    | maximum appearance; text does not reflow       |

---

## Graphical interface (PDF Reconstruction Studio)

```bat
pip install -r requirements.txt
python run_gui.py            :: or double-click iniciar_gui.bat
```

Drag the PDF in (or click *Select PDF*) → **Reconstruct PDF** → follow progress page by page → **Open document**. The interface is only the presentation layer: it calls `app.pipeline.reconstruct_pdf` through `gui/services/engine_adapter.py`, without duplicating the engine. The command line keeps working the same way.

| In the interface                   | In the engine                                                                              |
|------------------------------------|--------------------------------------------------------------------------------------------|
| Quality **Fastest**                | `balanced` mode, **without** comparing the result to the original                          |
| Quality **Balanced** (default)     | `balanced` mode, comparing with the original (requires LibreOffice or Word)                |
| Quality **Maximum fidelity**       | `visual` mode (locked lines; more faithful, less editable)                                 |
| Progress                           | page by page; steps without measurable progress use an indeterminate bar                   |
| Cancel                             | cooperative: the engine checks between steps/pages; no partial DOCX is left behind         |
| Password-protected PDF             | the GUI asks for the password; the engine receives a temporary unprotected copy (deleted at the end) |
| Scanned pages                      | the GUI warns that, without OCR (Phase 7), they are inserted as an **image** (text not editable) |

- The quality report (HTML) appears as **View quality report** on the success screen (stored in `reports/<name>/`).
- Logs: `logs/application.log` and `logs/reconstruction.log` (*Open logs* button in Settings).
- Preferences: `QSettings` · History: `data/history.json`.
- To test only the interface without actually processing anything: `set PDFRS_DEMO=1` before `python run_gui.py`.

### Languages

The interface is available in Portuguese (BR), English, Deutsch, Italiano, Español and Français, and switches instantly under *Settings → Language / Idioma* (default: the Windows language). To add another language, see `TRADUCOES.md`.

### Executable (.exe), no .bat needed

Double-click **`criar_executavel.bat`** (once; requires internet and takes a few minutes). It creates the environment, installs the libraries, packages the program with PyInstaller and creates a **"PDF Reconstruction Studio"** shortcut on the Desktop. The program is located at `dist\PDF Reconstruction Studio\PDF Reconstruction Studio.exe` (a ~400 MB folder that can be moved as a whole). Logs and history are stored in `%LOCALAPPDATA%\PDFReconstructionStudio`. To check a build: `"PDF Reconstruction Studio.exe" --selftest` (writes `selftest.log` with OK/FAILED).

`iniciar_gui.bat` looks for Python (`.venv`, `venv`, `py`, `python`), checks the dependencies and opens the program with a console window that shows any error. **Extract the ZIP before using it** (do not run from inside the ZIP). If the window does not open, check `logs\startup_error.log` and `logs\crash.log`.

---

## How it works

```
PDF → diagnosis → classification → extraction → paragraphs → DocumentModel → DOCX
    → rendering → PDF × DOCX comparison → report
```

- **Diagnosis**: per page (text, images, vectors, tables, columns, fonts, invisible OCR layer) → `TEXT_PDF`, `SCANNED_PDF`, `HYBRID_PDF` or `COMPLEX_LAYOUT_PDF`. **OCR is never used if real text is present.**
- **Paragraphs**: grouping uses vertical spacing, style, indents, alignment and the **natural line break test** (if the first word of the next line would have fit at the end of the previous one, the break was deliberate, so it is not a continuation).
- **Position**: each PDF page becomes a *section* in Word. A "cursor" simulates where Word will place each line, so the baselines land where they were (measured: **< 0.1 pt** deviation in LibreOffice).
- **Images**: the original image is extracted (without rasterizing the page), with transparency and 90° rotation handled, and inserted as an anchored object at the exact position, in front of or behind the text according to the PDF's painting order.
- **Fonts**: names are normalized (`ABCDEF+Arial-BoldMT` → Arial). If a font is not installed, it is substituted **and logged**. No substitution is silent.

## Project structure

```
main.py                       entry point (CLI)
run_gui.py / iniciar_gui.bat  entry point for the graphical interface
gui/                          interface (PySide6): ui/ screens, services/ (includes engine_adapter.py), workers/, utils/
app/
  pipeline.py                 orchestrates the flow; isolates errors per page and per file
  config.py                   ALL thresholds and the effect of each mode
  analyzer/                   Phase 1: PDF diagnosis and page classification
  extractors/                 Phase 2: text (with font, color and coordinates) and images
  models/                     Phase 3: intermediate model (document / page / text / image), in JSON
  reconstruction/             Phases 4/5: paragraphs and DOCX generation
  validation/                 DOCX rendering, visual comparison (SSIM) and report
  utils/                      geometry, fonts, issue registry, logging
tests/                        automated tests; tests/samples/ receives the PDFs generated by make_samples.py
input/  output/  reports/  temp/   (generated during use; not versioned)
```

## Similarity metric

- **Visual**: SSIM computed **only over regions with content** (otherwise the white paper would inflate the score).
- **Text**: compares the words in visual reading order.

It is an **indicator for finding problematic pages, not an absolute measure of fidelity**. Always look at the comparison images.

Results on the test samples (LibreOffice, `balanced` mode):

| Sample                                      | Visual | Text | Notes                                                                              |
|---------------------------------------------|--------|------|------------------------------------------------------------------------------------|
| simple text (justified, list, title)        | 95%    | 100% | identical line breaks                                                              |
| text + image                                | 96%    | 100% | image pixel-for-pixel identical                                                    |
| landscape                                   | 90%    | 100% |                                                                                    |
| "Word-style" PDF (title, bullets, image)    | 87%    | 99%  | missing the rule under the title (vector); 99% because the Symbol-font bullet becomes "•" |
| header/footer across 3 pages                | 93%    | 100% | pages preserved 1:1                                                                |
| two columns                                 | 97%    | 100% | columns kept via tab stops                                                         |
| table                                       | 63%    | 100% | **borders and shading not yet reconstructed** (Phase 6)                            |
| scanned (no text)                           | 96%    | —    | page inserted as a background image: **not editable** (OCR in Phase 7)             |
| rotated page (`/Rotate`)                    | 90%    | 0%   | inserted as an image: **not editable**                                             |

## Known limitations of this version

All of these appear in each document's report when they occur.

| Limitation                                                           | What happens today                                                                                           | Phase |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|-------|
| **Tables**                                                           | text aligned with tab stops; **no borders, cells or shading**                                                | 6     |
| **Scanned PDF**                                                      | page inserted as a background image; **no editable text** (`OCR_PENDENTE`)                                   | 7     |
| **Vectors** (lines, shapes, colored backgrounds, underlines)         | not reconstructed (`VETORES_NAO_RECONSTRUIDOS`)                                                              | 6/8   |
| **Columns**                                                          | native Word columns for simple cases; titles that span the columns use tab stops                              | 8     |
| **Header/footer**                                                    | detected, but kept in the page body; not turned into native Word header/footer                               | 8     |
| **Lists**                                                            | bullet and indent are correct, but it is literal text (not an automatic Word list)                           | 8     |
| **Word styles**                                                      | no `Heading 1`, `Normal`, etc.; everything is direct formatting                                              | 8     |
| **Page with `/Rotate`**                                              | inserted as an image                                                                                         | 8     |
| **Rotated text** (diagonal watermark, vertical text)                 | **not reconstructed** (`TEXTO_ROTACIONADO`)                                                                  | 8     |
| **Images** rotated at an angle that is not a multiple of 90° or mirrored | inserted without rotation (logged)                                                                       | —     |
| **Forms** (fields/checkboxes)                                        | only what tab stops can do; no editable fields                                                               | 8     |

Other notes:

- Text is never "fixed": if the PDF has a hyphen at the end of a line, it stays.
- The system only reproduces what the PDF contains. If the recovered PDF was already damaged, the report flags `PDF_REPARADO`.
- If the number of pages in the rendered DOCX differs from the original, the page-by-page comparison may become misaligned, and the report warns about it (`NUMERO_DE_PAGINAS_DIFERENTE`).

## What was (and was not) verified

- ✅ **Tested**: Linux, Python 3.12, PyMuPDF 1.28, LibreOffice. Automated tests pass; the generated DOCX files pass OOXML schema validation.
- ⚠️ **Not tested**: running **on Windows**, **Microsoft Word** as the renderer (`--renderer word`), and opening the DOCX files in Word itself. Detection of installed fonts on Windows (via the registry) is implemented but has only been exercised on Linux.
- ⚠️ Vertical positioning was **calibrated against LibreOffice**. If there is a systematic offset in Word, the adjustment lives in `app/config.py` (`exact_ascent_ratio`, `descent_ratio`) and `app/utils/fonts.py`.

## Tests

```bat
pip install -r requirements-dev.txt
python -m pytest
```

This generates the sample PDFs in `tests/samples/`. The "Word-style" case requires LibreOffice; without it, that case is skipped.

## Roadmap

| Phase | Content                                                                              | Status                    |
|-------|--------------------------------------------------------------------------------------|---------------------------|
| 1     | PDF analyzer                                                                         | ✅                         |
| 2     | Structural extraction                                                                | ✅                         |
| 3     | Intermediate model                                                                   | ✅                         |
| 4     | Basic DOCX reconstruction                                                            | ✅                         |
| 5     | Images and fonts                                                                     | ✅                         |
| 6     | **Tables** (`add_table`, merged cells, borders)                                      | next                      |
| 7     | OCR / PaddleOCR (optional dependency)                                                | pending                   |
| 8     | Complex layouts (columns, native header/footer, lists, styles, forms)                | pending                   |
| 9     | Rendering and comparison                                                             | ✅ (core)                  |
| 10    | Full reports                                                                         | basic version ready       |
| 11    | Batch                                                                                | basic version ready (`--input`) |
| 12    | Graphical interface                                                                  | ✅ (MVP)                   |

## License

This project is distributed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See the [LICENSE](LICENSE) file.

This choice is due to PyMuPDF, the library used to read PDFs, which is also AGPL-3.0. Anyone who distributes the program (or offers it as a service over a network) must make the source code available under the same license. For personal, local use there are no restrictions.

Other dependencies: python-docx (MIT), Pillow (HPND), NumPy (BSD), scikit-image (BSD). LibreOffice (MPL 2.0) is used as an external program, not bundled.
