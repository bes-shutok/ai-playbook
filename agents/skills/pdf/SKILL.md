---
name: "pdf"
description: "Use when tasks involve reading, creating, reviewing, or FILLING PDF files where rendering and layout matter; prefer visual checks by rendering pages (Poppler) and use Python tools such as `reportlab`, `pdfplumber`, `pypdf`, and `pikepdf` for generation, extraction, and form-fill overlays."
---


# PDF Skill

## When to use
- Read or review PDF content where layout and visuals matter.
- Create PDFs programmatically with reliable formatting.
- Validate final rendering before delivery.

## Workflow
1. Prefer visual review: render PDF pages to PNGs and inspect them.
   - Use `pdftoppm` if available.
   - If unavailable, install Poppler or ask the user to review the output locally.
2. Use `reportlab` to generate PDFs when creating new documents.
3. Use `pdfplumber` (or `pypdf`) for text extraction and quick checks; do not rely on it for layout fidelity.
4. After each meaningful update, re-render pages and verify alignment, spacing, and legibility.

## Temp and output conventions
- Use `tmp/pdfs/` for intermediate files; delete when done.
- Write final artifacts under `output/pdf/` when working in this repo.
- Keep filenames stable and descriptive.

## Dependencies (install if missing)
Prefer `uv` for dependency management.

Python packages:
```
uv pip install reportlab pdfplumber pypdf pikepdf
```
If `uv` is unavailable:
```
python3 -m pip install reportlab pdfplumber pypdf pikepdf
```
`pikepdf` is required for the form-fill merge step below (overlay onto image-only PDFs).
System tools (for rendering):
```
# macOS (Homebrew)
brew install poppler

# Ubuntu/Debian
sudo apt-get install -y poppler-utils
```

If installation isn't possible in this environment, tell the user which dependency is missing and how to install it locally.

## Environment
No required environment variables.

## Rendering command
```
pdftoppm -png $INPUT_PDF $OUTPUT_PREFIX
```

## Quality expectations
- Maintain polished visual design: consistent typography, spacing, margins, and section hierarchy.
- Avoid rendering issues: clipped text, overlapping elements, broken tables, black squares, or unreadable glyphs.
- Charts, tables, and images must be sharp, aligned, and clearly labeled.
- Use ASCII hyphens only. Avoid U+2011 (non-breaking hyphen) and other Unicode dashes.
- Citations and references must be human-readable; never leave tool tokens or placeholder strings.

## Final checks
- Do not deliver until the latest PNG inspection shows zero visual or formatting defects.
- Confirm headers/footers, page numbering, and section transitions look polished.
- Keep intermediate files organized or remove them after final approval.

## Filling existing PDF forms (flat / non-AcroForm)

Many real-world forms (bank self-certifications, government PDFs, scanned documents) are **flat**: the visible form is a raster image with an invisible text layer, and they have **no AcroForm fields** to fill. Detect this before choosing a strategy.

### Detect the form type

```python
import pypdf, pdfplumber
r = pypdf.PdfReader(path)
has_acroform = r.trailer["/Root"].get("/AcroForm") is not None
# content-stream count reveals image-only pages
contents = r.pages[0].get_contents()
image_only = not contents  # True => visible content is an image XObject, not vector text
```

- `has_acroform=True`: use a field-filling library (e.g. `pypdf` writer, `fillpdf`). Do not overlay. See the AcroForm workflow below.
- `has_acroform=False` (flat): generate a text overlay with `reportlab` and merge it onto the original page. Steps below.

### AcroForm field-fill workflow (has_acroform=True)

For forms with real fillable fields, set each widget's `/V` and verify rendering with **Poppler**, not pdfplumber.

1. **Use partial names when mutating widgets via the writer.** After `writer.append(reader)`, each widget's `/T` is the *partial* name (`f_1[0]`), not the fully-qualified path (`topmostSubform[0].Page1[0].f_1[0]`) that `reader.get_fields()` reports. Match on partial names or the fill silently no-ops. Or use `writer.update_page_form_field_values(page, {fq_name: value}, auto_regenerate=True)`, which accepts fully-qualified names and regenerates appearances.
2. **Checkboxes need both `/V` and `/AS`.** Set `/V` to the on-state name AND `/AS` to the same name (`/AS` is what the renderer reads; `/V` alone may not show the check). Read the on-state from the widget's `/AP /N` keys (e.g. `['/1']` means on-state is `/1`), not by guessing `/Yes`.
3. **`/Sig` (signature) widgets cannot hold typed text.** Leave them for wet or digital-ID signing; fill the surrounding "Print name of signer" / "Date" text fields instead.
4. **Map fields to labels via rect geometry, not field order.** Use `pdfplumber` words with `top = page_height - rect[3]` and find the label *above* each widget rect. A label-printing-order swap (e.g. "7 Reference" typeset above "8 DOB" while the row's left cell is 7) misleads if you trust reading order; the rect is ground truth.
5. **Verify rendering with Poppler, NEVER pdfplumber.** pdfplumber does not extract text from form-field appearance streams, so it reports every filled value as MISSING even when the value renders correctly. Set `AcroForm /NeedAppearances = True` for safety, then confirm with:
   - `pdftotext -layout <filled.pdf> -` (Poppler, same engine as macOS Preview) — grep for each value.
   - `pdftoppm -png -r 200` + a dark-pixel count on the checkbox bbox (border-only ≈ 3-6% dark; checked ≈ 8-25%).

### Overlay workflow for flat forms

1. **Map field geometry from the text layer, then VERIFY by rendering.** Use `pdfplumber` to locate labels and cell boxes. Form fields are usually **grids of labeled boxes** (rects with `width>100, height>15`), not label+underline pairs. Detect the box below each label and place the value **vertically centered inside that box**, not "just above the nearest line" (that heuristic lands values in the wrong grid row).
2. **Build the overlay** with `reportlab`. Convert `pdfplumber` top-origin coordinates to `reportlab` bottom-origin: `rl_y = page_height - plumber_top`. Vertically center text in a box: baseline at `box_mid_top + font_size*0.3`.
3. **Merge with `pikepdf`, NOT `pypdf.merge_page`, on image-only PDFs.** `pypdf.merge_page` renders the overlay **twice** on pages whose visible content is a single image XObject (the text extracts once but renders doubled/intertwined). Use:
   ```python
   import pikepdf
   orig = pikepdf.Pdf.open(original)
   over = pikepdf.Pdf.open(overlay)
   orig.pages[0].add_overlay(over.pages[0])
   out = pikepdf.Pdf.new(); out.pages.append(orig.pages[0]); out.save(filled)
   ```
4. **Verify placement at high DPI (400) on the FIRST sign of trouble, not after several rounds.** A 150-DPI render hides misplacement and doubling defects. On any reported misplacement, immediately render at 400 DPI and crop the offending region before re-mapping coordinates. Do not iterate on geometry from text extraction alone.
5. **Confirm each value lands in a blank zone.** Before merging, check the candidate box has no original text (`pdfplumber` word-at-region query); after merging, re-extract and confirm overlay text is clean (not interleaved with form text).

### macOS-protected source paths

A source PDF under `~/Documents`, `~/Desktop`, or `~/Downloads` may be unreadable via the shell (`Operation not permitted`) even with the sandbox disabled, because macOS TCC restricts those folders per-app. Workarounds, in order of preference:
- Copy the file into the workspace with **Finder via `osascript`** (Finder has its own TCC entitlement):
  ```bash
  osascript -e 'tell application "Finder" to duplicate (POSIX file "/Users/<user>/Documents/form.pdf") to (POSIX file "<workspace_dir>") with replacing'
  ```
- If only reading is needed, the agent's `Read` tool may have a separate entitlement even when Bash does not.

### Personal-data forms (AEOI/CRS, KYC, tax)

These forms require identity data (name, DOB, tax ID, address). Do not hardcode values from the model's prior knowledge. Pull values from a gitignored facts file or ask the user, and record a single source of truth there for future sessions. Leave signature lines blank for wet-signing unless explicitly told otherwise.
