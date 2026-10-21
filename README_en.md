# PDF Document Reconstructor

Reconstructs recovered PDFs into **editable** `.docx` files, as close as possible to the lost original.
Everything runs **locally and offline**: no PDF ever leaves your computer.

> **Reconstruction ≠ recovery.** The *content* (text, fonts, images, positions) is recovered from the PDF.
> The original DOCX's *internal structure* (styles, fields, breaks, automatic numbering) no longer exists in the PDF and must be
> **inferred**. The program measures how closely the result resembles the original and reports where it failed.

Status: **MVP (Phases 1–5 + Phase 9 validation)** — PDFs containing real text. See [Known limitations of this version](#known-limitations-of-this-version).

---

## Installation (Windows)

Requirements: **Python 3.10 or later** (https://www.python.org/downloads/ — check *Add python.exe to PATH*).

```bat
cd pdf_document_reconstructor
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For **visual validation** (rendering the DOCX back to PDF and comparing it), a renderer is required:

| Option | How to install | Notes |
|---|---|---|
| **LibreOffice** (default) | `winget install TheDocumentFoundation.LibreOffice` or https://www.libreoffice.org | Free and offline. May differ slightly from Word. |
| **Microsoft Word** | `pip install docx2pdf` (Word must be installed) | Most closely matches what you will see when opening the DOCX. Use `--renderer word`. |

Without either one, the DOCX is generated normally; only the visual comparison is skipped (and the report will mention this).

## Usage

```bat
:: one file
python main.py document.pdf

:: entire folder (processes everything in input\ and writes to output\)
python main.py --input .\input --output .\output

:: choose a mode
python main.py document.pdf --mode editable      :: prioritizes editability
python main.py document.pdf --mode visual        :: prioritizes appearance
python main.py document.pdf --mode balanced      :: default

:: other options
python main.py document.pdf --renderer word --no-validate --keep-temp -v
```

### Generated files

```text
output/document.docx                         ← reconstructed file
reports/document/relatorio.html                 ← open in a browser (quality, fonts, issues, comparison)
reports/document/relatorio.json                 ← same data, for automation
reports/document/document_reconstruido.pdf  ← the DOCX rendered back to PDF
reports/document/comparacao/                 ← original_page_01.png, reconstructed_page_01.png, difference_page_01.png
reports/document/modelo.json                  ← intermediate model (for debugging without reprocessing)
reports/document/processamento.log              ← detailed log
```

In the `difference_page_XX.png` map: **gray** = identical · **red** = present in the original but missing from the reconstruction ·
**blue** = extra or shifted.

If a PDF fails (corrupted, password-protected, or not a PDF), the error is recorded and batch processing **continues**.
In the final table, `!` marks files with serious issues: **read the report before trusting the result**.

### The three modes

| Mode | Line spacing | Line breaks | Purpose |
|---|---|---|---|
| `balanced` (default) | "at least" X pt | Word recalculates them | best compromise |
| `editable` | **multiple** (1.0 / 1.15 / 1.5…) | Word recalculates them | edit freely; spacing adapts to font size |
| `visual` | **exactly** X pt | **locked** at the original positions | maximum visual fidelity; text does not reflow |

---

## Graphical interface (PDF Reconstruction Studio)

```bat
pip install -r requirements.txt
python run_gui.py            :: or double-click iniciar_gui.bat
```

### Languages

The interface supports Portuguese (Brazil), English, German, Italian, Spanish, and French, and switches immediately under
*Settings → Language* (default: the Windows language). To add another language, see `TRADUCOES.md`.

### Standalone program (.exe), without a .bat file

Double-click **`criar_executavel.bat`** once (an internet connection is required; it takes a few minutes). It creates the environment, installs the
libraries, packages the program with PyInstaller, and places a **"PDF Reconstruction Studio"** shortcut on the Desktop.
The program is located at `dist\PDF Reconstruction Studio\PDF Reconstruction Studio.exe` (a folder of about 400 MB; you can move the entire folder
wherever you like). Logs and history are then stored in `%LOCALAPPDATA%\PDFReconstructionStudio`. To check a build, run:
`"PDF Reconstruction Studio.exe" --selftest` (writes `selftest.log` with OK/FAIL). Comparison with the original (Balanced mode)
still uses LibreOffice or Word installed on the computer; without either one, the document is generated normally, but without comparison.

---

`iniciar_gui.bat` searches for Python (`.venv`, `venv`, `py`, `python`), checks the dependencies, and opens the program with a
console window that displays any errors. **Extract the ZIP before use** (do not run it from inside the ZIP file).
If the window does not open, check `logs\startup_error.log` (startup errors) and `logs\crash.log` (fatal Qt crashes);
the program also displays a message box explaining the reason.

Drag and drop the PDF (or click *Select PDF*) → **Reconstruct PDF** → track progress page by page → **Open document**.
The interface is only the presentation layer: it calls `app.pipeline.reconstruct_pdf` through `gui/services/engine_adapter.py`
(the engine has not been duplicated). The command line (`python main.py ...`) continues to work as before.

| In the interface | In the engine |
|---|---|
| **Fastest** quality | `balanced` mode, **without** comparing the result with the original |
| **Balanced** quality (default) | `balanced` mode, comparing against the original (requires LibreOffice or Word) |
| **Maximum fidelity** quality | `visual` mode (locked lines; more faithful, less editable) |
| Progress | genuinely page by page; stages without measurable progress use an indeterminate bar |
| Cancel | cooperative: the engine checks between stages/pages; no partial DOCX is left behind |
| Password-protected PDF | the GUI asks for the password; the engine receives a temporary unprotected copy (deleted at the end) |
| Scanned pages | the GUI warns that, without OCR (Phase 7), they are inserted as **images** (non-editable text) |

* The quality report (HTML) appears as **View quality report** on the success screen (stored in `reports/<name>/`).
* GUI and engine logs: `logs/application.log` and `logs/reconstruction.log` (use the *Open logs* button in Settings).
* Preferences: `QSettings` · History: `data/history.json`.
* To test only the interface without actually processing files: set `PDFRS_DEMO=1` before running `python run_gui.py`.

**Changes made to the engine (backward-compatible):** `app/utils/hooks.py` (new: optional progress/cancellation hooks),
`app/pipeline.py` (optional `hooks` parameter; behavior is unchanged without it), and `app/validation/docx_renderer.py`
(LibreOffice is called with `stdin=DEVNULL` and without a window, which is necessary when running with `pythonw`).

**Cropped images:** when the PDF displays only part of a photo (clipping, or "crop image" in Word/Canva/InDesign), the DOCX uses the
visible area and Word's native crop (`a:srcRect`: the full photo remains in the file and the crop can be adjusted). Circular or
rounded-corner crops become transparent PNGs. An image that is **both** cropped and mirrored/rotated by an arbitrary angle cannot retain its crop.

**Layers (image × text):** an image drawn *after* text that it covers appears in front (as in the PDF). An image drawn *before* the
text, or within `image_text_safe_margin_pt` (16 pt) of any text, appears **behind** the text. This way, if Word uses a different font
or wraps a line differently, no words are hidden by an image. Standalone images remain in front (making them easier to edit).
To select an image that is behind text in Word: Home → Select → Selection Pane.

**Columns (2 to 3):** pages where no line crosses the gap between columns are converted to native Word columns
(`w:cols`, with column breaks and, if the PDF contains a vertical line between columns, a separator). Each column has its own
paragraphs, so lines from the left and right columns never get mixed. If a heading spans across columns, the page uses the
previous behavior (tab stops). Disable this with `Config(native_columns=False)`.

**Text width:** Word-generated PDFs typically have text that is about 1–3% narrower than the nominal font width (the `Tc` setting). The engine measures this
in Times/Arial/Courier and reproduces it as character spacing (condensing only), so Word wraps lines where the PDF did
(`Config(match_text_width=False)` disables this behavior).

---

## How it works

```text
PDF → diagnosis → classification → extraction → paragraphs → DocumentModel → DOCX
    → rendering → PDF × DOCX comparison → report
```

* **Diagnosis**: performed per page (text, images, vectors, tables, columns, fonts, invisible OCR layer) →
  `TEXT_PDF`, `SCANNED_PDF`, `HYBRID_PDF`, or `COMPLEX_LAYOUT_PDF`. **OCR is never used when real text is present.**
* **Paragraphs**: a PDF contains separate lines with coordinates. Grouping uses vertical spacing, style, indents,
  alignment, and the **natural line-break test** (if the first word of the next line *would fit* at the end of the previous one,
  the line break was deliberate, so addresses and verses do not become one block).
* **Positioning**: each PDF page becomes a Word *section* (with its own size and margins). A "cursor" simulates where Word
  will place each line and calculates the spacing before each paragraph so that baselines land where they were in the original
  (measured deviation: **< 0.1 pt** in LibreOffice).
* **Images**: the original image is extracted (without rasterizing the page), with transparency and 90° rotation handled, and
  inserted as an anchored object at the exact position, in front of or behind the text according to the PDF's paint order.
* **Fonts**: font names are normalized (`ABCDEF+Arial-BoldMT` → Arial); if a font is not installed, it is replaced **and logged**.
  No substitution happens silently.

## Project structure

```text
main.py                       entry point (CLI)
run_gui.py / iniciar_gui.bat  graphical interface entry point
 gui/                         interface (PySide6): ui/ screens, services/ (including engine_adapter.py), workers/, utils/
app/
  main.py                     command-line arguments and summary table
  pipeline.py                 orchestrates the workflow; isolates errors by page and file
  config.py                   ALL thresholds and the behavior of each mode
  analyzer/
    pdf_analyzer.py           Phase 1: analyzes the document (opens, repairs, aggregates pages)
    page_analyzer.py          page metrics (text, images, vectors, tables, columns, margins…)
    layout_analyzer.py        heuristics: number of columns, recurring headers/footers
    font_analyzer.py          document font summary
    document_classifier.py    classifies pages/document and chooses the strategy (A/B/C)
  extractors/
    text_extractor.py         Phase 2: spans with font, size, color, and coordinates; ignores invisible text
    image_extractor.py        original images (+alpha mask, CMYK, rotation, paint order)
  models/                     Phase 3: intermediate model (document / page / text / image), JSON-serializable
  reconstruction/
    paragraph_builder.py      lines → paragraphs, alignment, indents, lists, tab stops
    docx_builder.py            Phases 4/5: DOCX (sections per page, calculated spacing, anchored images)
  validation/
    docx_renderer.py          DOCX → PDF (LibreOffice or Word)
    pdf_renderer.py           page rasterization
    image_comparator.py       per-page SSIM + text similarity + difference map
    quality_report.py         HTML/JSON report
  utils/                      geometry, fonts, issue tracking (IssueLog), logging, PDF access
 tests/                        44 tests; tests/samples/ contains sample PDFs (generated by make_samples.py)
 input/ output/ reports/ temp/
```

## Similarity metric

* **Visual**: SSIM calculated **only in regions containing content** (otherwise the white page would inflate the score).
* **Text**: compares words in visual reading order (regardless of the order in which the PDF drew them).

This is a **metric for finding problematic pages, not an absolute measure of fidelity**. A shift of just 1 px can lower the SSIM score;
always inspect the comparison images.

Results on this repository's sample files (LibreOffice, `balanced` mode):

| Sample | Visual | Text | Notes |
|---|---:|---:|---|
| simple text (justified, list, heading) | 95% | 100% | identical line breaks |
| text + image | 96% | 100% | pixel-identical image |
| landscape | 90% | 100% | |
| Word-like PDF (heading, bullets, image) | 87% | 99% | missing rule under the heading (vector); 99% because the Symbol-font bullet becomes "•" |
| header/footer across 3 pages | 93% | 100% | pages preserved 1:1 |
| two columns | 97% | 100% | columns preserved using tab stops |
| table | 63% | 100% | **borders and shading have not yet been reconstructed** (Phase 6) |
| scan (no text) | 96% | — | page inserted as a background image: **not editable** (OCR in Phase 7) |
| rotated page (`/Rotate`) | 90% | 0% | inserted as an image: **not editable** |

## Known limitations of this version

All limitations are listed in each document's report when they occur.

| Limitation | Current behavior | Phase |
|---|---|---|
| **Tables** | text aligned using tab stops; **no borders, cells, or shading** | 6 |
| **Scanned PDF** | page inserted as a background image; **no editable text** (`OCR_PENDENTE`) | 7 |
| **Vectors** (lines, shapes, colored backgrounds, underlining) | not reconstructed (`VETORES_NAO_RECONSTRUIDOS`) | 6/8 |
| **Columns** | preserved using tab stops; not native Word columns | 8 |
| **Header/footer** | detected but remain in the page body; not converted into Word headers/footers | 8 |
| **Lists** | bullets and indents are correct, but are literal text (not automatic Word lists); `1.` numbering is text | 8 |
| **Word styles** | no `Heading 1`, `Normal`, etc.; everything uses direct formatting (the paragraph class is detected and stored in the model) | 8 |
| **Page with `/Rotate`** | inserted as an image | 8 |
| **Rotated text** (diagonal watermark, vertical text) | **not reconstructed** (`TEXTO_ROTACIONADO`) | 8 |
| **Images** rotated by an angle that is not a multiple of 90°, or mirrored | inserted without rotation (logged) | — |
| **Forms** (fields/boxes) | only what tab stops can reproduce; no editable fields | 8 |

Other important notes:

* Text is never "fixed": if the PDF has a hyphen at the end of a line, it remains.
* The system only reproduces what the PDF contains. If the recovered PDF was already damaged, the report marks it as `PDF_REPARADO`.
* If the number of pages in the rendered DOCX differs from the original (text overflow), index-based comparison may
  be misaligned and the report will issue a warning (`NUMERO_DE_PAGINAS_DIFERENTE`).

## What has (and has not) been verified

* ✅ **Tested**: Linux, Python 3.12, PyMuPDF 1.28, LibreOffice. All 44 automated tests pass; every generated DOCX
  passes OOXML schema validation.
* ⚠️ **Not tested**: running on **Windows**, using **Microsoft Word** as the renderer (`--renderer word`), and opening
  the DOCX files in Word itself. Detection of installed fonts on Windows (via the registry) is implemented, but has only been
  exercised on Linux (`fc-list`).
* ⚠️ Vertical positioning was **calibrated against LibreOffice**. Word may differ by fractions of a point in baseline
  positioning; if you notice a systematic offset when opening the file in Word, the settings are in `app/config.py`
  (`exact_ascent_ratio`, `descent_ratio`) and `app/utils/fonts.py` (per-font metric tables).

## Tests

```bat
pip install -r requirements-dev.txt
python -m pytest
```

Generates sample PDFs in `tests/samples/` (the Word-like sample requires LibreOffice; without it, that case is skipped).
Visual validation tests are also skipped if no renderer is available.

## Licenses

* **PyMuPDF is AGPL-3.0.** Personal and local use is unrestricted. If you distribute this program (or offer it
  as a service), you must comply with the AGPL or purchase Artifex's commercial license.
* python-docx (MIT), Pillow (HPND), NumPy (BSD), scikit-image (BSD). LibreOffice (MPL 2.0) is used as an external program.

## Roadmap

| Phase | Contents | Status |
|---|---|---|
| 1 | PDF analyzer | ✅ |
| 2 | Structural extraction | ✅ |
| 3 | Intermediate model | ✅ |
| 4 | Basic DOCX reconstruction | ✅ |
| 5 | Images and fonts | ✅ |
| 6 | **Tables** (`add_table`, merged cells, borders) | next |
| 7 | OCR / PaddleOCR (optional dependency) | |
| 8 | Complex layouts (columns, native headers/footers, lists, styles, forms) | |
| 9 | Rendering and comparison | ✅ (core) |
| 10 | Full reports | basic version ready |
| 11 | Batch processing | basic version ready (`--input`) |
| 12 | Graphical interface | |
