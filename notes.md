# Project Notes

## 1. What was reset

The active repository implementation was reset into a clean Flask application skeleton. Existing active application files from the prior implementation were removed from the working tree before this scaffold was created.

## 2. New structure created

The new structure includes:

- `app.py`
- `web/` for the Flask app factory, routes, templates, static CSS, and minimal JavaScript
- `cleaning/` placeholder modules for the future data cleaning workflow
- `configs/` placeholder statement configuration modules
- `storage/` placeholder persistence modules
- `analysis/` placeholder module
- `data/raw/` and `data/processed/`
- `tests/` placeholder test files
- `README.md`, `requirements.txt`, and this `notes.md`

## 3. Current routes/pages

- `/` renders the dashboard placeholder.
- `/data` renders the planned data cleaning workflow layout.
- `/companies` renders a placeholder for approved company records saved to SQL later.
- `/analysis` renders a placeholder for future analysis modules.

## 4. UI direction

The UI uses a restrained internal analyst-tool style: dark navy sidebar, light content area, white cards, minimal borders, and amber accents used sparingly.

## 5. Naming decisions pending

- Final application name is not decided.
- Do not use "BRPA" as a product-facing name for now.
- Dashboard label names are temporary.
- Whether "Companies" should later be called "Saved Companies", "Company Records", or "Database" is undecided.
- Whether "Data" should later be called "Data Intake", "Upload Data", or "Data Workspace" is undecided.

## 6. Preservation note for `old_engine_files`

- `old_engine_files` was intentionally preserved as archived reference material.
- It is not part of the active application.
- It should not be imported from, modified, or deleted unless explicitly instructed later.

## 7. Known limitations

- Upload functionality is not implemented.
- Pandas cleaning logic is not implemented.
- SQL schema and persistence are not implemented.
- Metrics, charts, red flags, summaries, valuation, and AI features are not implemented.
- Tests are placeholders only because business logic does not exist yet.

## 8. Product rule

- If a missing field can be safely derived from existing table inputs, derivation is normal practice and should not be treated as a warning. The derivation should still be traceable internally.

## 9. Next suggested implementation step

Define the first data intake contract: accepted file types, required statement tabs or tables, expected column inputs, and the shape of the in-memory cleaned dataset before persistence exists.

## 10. Data intake update

### What changed

The Data area was updated from a static workflow-stage placeholder into a two-page data intake and cleaned-preview skeleton.

### Files touched

- `web/routes.py`
- `web/templates/data.html`
- `web/templates/cleaned_data.html`
- `web/static/css/main.css`
- `web/static/js/main.js`
- `notes.md`

### New route

- `/data/cleaned` renders the Cleaned Data Preview page.

### Current behavior

- `/data` shows three statement upload placeholders for Income Statement, Balance Sheet, and Cash Flow Statement.
- `/data` shows three raw preview table cards using placeholder data.
- The `Clean data` button navigates to `/data/cleaned`.
- `/data/cleaned` shows three cleaned output table cards using placeholder data.
- Table cards can expand to fullscreen and collapse without reloading the page.
- The cleaned preview page includes placeholder statuses for mechanical cleaning, orientation detection, schema validation, label mapping, derivations, and identity checks.

### Known limitations

- Upload areas are still placeholders unless actual upload handling is implemented.
- Tables use placeholder data for layout.
- Clean data button navigates to the cleaned preview page but does not run real cleaning logic yet.
- No database persistence yet.

### Next suggested step

Define the upload contract and request/response flow for accepting three statement files without implementing cleaning transformations yet.

## 11. Data page tabbed raw preview update

### What changed

The Data page layout was refined into a more compact analyst workspace. The three upload cards remain near the top, and the raw preview area is now a single tabbed card instead of three vertically stacked table cards.

### Files touched

- `web/templates/data.html`
- `web/static/css/main.css`
- `web/static/js/main.js`
- `notes.md`

### Reason for changing raw previews from vertical stack to tabs

The vertical stack would become too long once real uploaded statement data is displayed. Tabs keep the workspace shorter and make it easier to compare one statement preview at a time without moving the upload section far from view.

### Raw preview orientation decision

Raw preview tables intentionally remain in analyst-friendly financial statement orientation: line items as rows and periods as columns. The raw preview is not converted into database or canonical format at this stage.

### Current behavior

- `/data` shows three placeholder upload cards for Income Statement, Balance Sheet, and Cash Flow Statement.
- The Raw Preview card includes tabs for Income Statement, Balance Sheet, and Cash Flow Statement.
- Only one raw preview table is visible at a time.
- Tab switching happens with minimal JavaScript and no page reload.
- Raw preview tables use placeholder data with line items as rows and periods as columns.
- Table expand and collapse behavior still works for the active tab.
- The `Clean data` button still navigates to `/data/cleaned`.

### Known limitations

- Upload cards are still placeholders.
- Raw preview tables still use placeholder data.
- Clean data button still navigates to `/data/cleaned` without running real cleaning.
- No real ingestion, cleaning, or persistence exists yet.

### Next suggested step

Define the front-end upload states for each statement card: empty, selected, invalid file type, ready to preview, and failed to parse.

## 12. Stage 1 mechanical cleaning update

### What changed

Stage 1 mechanical cleaning was implemented for in-memory pandas DataFrames. The new cleaning layer makes uploaded-style tabular data structurally parseable without applying accounting meaning, semantic mapping, validation, derivation, persistence, or UI upload handling.

### Files touched

- `cleaning/mechanical.py`
- `cleaning/audit.py`
- `tests/test_mechanical.py`
- `notes.md`

### Mechanical cleaning standard

Mechanical cleaning is limited to safe, structural transformations that do not require accounting knowledge or interpretation of statement meaning. It can make obvious formatting cleanup decisions, but it must preserve unmapped line items and avoid canonical financial-field decisions.

### What mechanical cleaning does

- Drops fully blank rows and columns.
- Treats null values and obvious blank-like strings as blank for dropping.
- Strips leading/trailing whitespace from strings.
- Collapses repeated internal whitespace to one space.
- Converts obvious blank-like values such as `-`, `N/A`, `None`, and `NULL` to `None`.
- Converts clear numeric-looking strings, including currency symbols, comma separators, currency prefixes, and parenthetical negatives.
- Normalizes header text mechanically by lowercasing, replacing `&` with `and`, normalizing spaces, and removing safe unit/currency suffix noise.
- Normalizes obvious period labels such as `FY2023`, `FY 2023`, `Dec-2022`, and `December 2022`.
- Preserves quarter labels such as `Q1 2023`.
- Returns an audit log summarizing dropped rows, dropped columns, normalized headers, missing-value conversions, numeric conversions, and period-label conversions.

### What mechanical cleaning explicitly does not do

- It does not decide that `sales` means `revenue`.
- It does not decide that `operating income` means `ebit`.
- It does not map labels to canonical financial fields.
- It does not derive missing fields.
- It does not validate accounting equations.
- It does not change statement meaning.
- It does not drop unmapped line items.
- It does not detect statement orientation.
- It does not persist data to SQL.

### Current behavior

- `run_mechanical_cleaning(df)` returns a dictionary with `cleaned_df` and `audit_log`.
- `cleaned_df` is a mechanically cleaned pandas DataFrame.
- `audit_log` is a serializable dictionary with summary counts and header-normalization entries.
- Mechanical string-formatting changes are not warnings.
- Test coverage now validates real mechanical behavior instead of placeholder assertions.

### Known limitations

- Mechanical cleaning is not yet wired to the `/data` upload UI.
- Orientation detection is not implemented yet.
- Schema validation is not implemented yet.
- Label mapping is not implemented yet.
- Safe derivations are not implemented yet.
- No SQL persistence exists yet.
- The audit log is intentionally lightweight and does not yet record every individual cell-level formatting change.

### Next suggested step

Define the in-memory handoff contract from mechanical cleaning to orientation detection, including the expected DataFrame shape and audit payload shape.

## 13. File ingestion update

### What changed

A raw file ingestion layer was added for CSV and Excel uploads. It reads supported file-like objects into pandas DataFrames and raises clean user-facing exceptions for unsupported, empty, or unreadable files.

### Files touched

- `cleaning/ingest.py`
- `tests/test_ingest.py`
- `tests/test_mechanical.py`
- `notes.md`

### Mechanical boundary verification

The mechanical cleaning tests now explicitly confirm that label formatting normalization does not become financial label mapping:

- `Sales` may normalize to `sales`.
- `Sales` must not normalize to `revenue`.
- `Operating Income` may normalize to `operating income`.
- `Operating Income` must not normalize to `ebit`.

Label mapping remains a later-stage responsibility for `cleaning/mapping.py`.

### Ingestion standard

Ingestion only reads uploaded-style files into raw pandas DataFrames. It does not mechanically clean values, normalize labels, map financial meanings, derive fields, detect orientation, validate schemas, check identities, or persist data.

### Supported file types

- `.csv`
- `.xlsx`
- `.xls`

Extension detection is case-insensitive.

### Current behavior

- `get_file_extension(filename)` returns a lowercase extension.
- `is_supported_file(filename)` returns `True` only for supported CSV and Excel extensions.
- `read_uploaded_file(file, filename=None)` reads a file-like object into a raw DataFrame based on the filename extension.
- CSV ingestion uses `pandas.read_csv`.
- Excel ingestion uses `pandas.read_excel`.
- Pandas default NA parsing is disabled during ingestion so values such as `NA` stay raw until mechanical cleaning handles them.
- Unsupported, empty, and unreadable files raise clean ingestion exceptions instead of exposing raw pandas tracebacks.
- Tests cover CSV, XLSX, unsupported extensions, case-insensitive extension detection, empty/unreadable inputs, and the ingestion boundary.

### Known limitations

- Ingestion is not yet wired to the `/data` UI.
- Uploaded files are not saved permanently.
- Mechanical cleaning is separate.
- Orientation detection is not implemented yet.
- Schema validation is not implemented yet.
- Label mapping is not implemented yet.
- Safe derivations are not implemented yet.
- Identity checks are not implemented yet.
- No SQL persistence exists yet.

### Next suggested step

Wire the `/data` upload form to ingestion only, returning raw preview DataFrames while leaving mechanical cleaning as a separate explicit step.

## 14. Data upload raw preview update

### What changed

The `/data` page now accepts uploaded statement files and renders raw preview tables in the existing tabbed Raw Preview area. The upload path uses `cleaning.ingest.read_uploaded_file` and does not run mechanical cleaning or later-stage financial workflow logic.

### Files touched

- `web/routes.py`
- `web/templates/data.html`
- `web/static/css/main.css`
- `tests/test_routes.py`
- `notes.md`

### New `/data` upload-preview behavior

- `/data` renders normally with no uploaded files.
- The page uses one upload form for Income Statement, Balance Sheet, and Cash Flow Statement files.
- Each statement upload card has a real file input.
- `POST /data` reads each provided file into a raw pandas DataFrame.
- Raw previews render in the existing Income Statement, Balance Sheet, and Cash Flow Statement tabs.
- Each uploaded preview shows filename and shape, such as `filename.csv · 42 rows × 6 columns`.
- Preview tables show the first 50 rows by default.
- If one file fails ingestion, that statement shows a clean error while the page remains usable.
- The existing `Clean data` button remains visible and continues placeholder navigation to `/data/cleaned`.

### Supported upload formats

- CSV
- XLSX
- XLS

### Raw preview boundary confirmation

Raw preview preserves uploaded values and labels as ingested. It does not run mechanical cleaning, orientation detection, schema validation, label mapping, derivations, identity checks, deduplication, conflict handling, persistence, or analysis features.

Examples covered by route tests:

- `$1,200` remains `$1,200` in raw preview.
- `Operating Income` remains `Operating Income`.
- `Operating Income` is not normalized to `operating income`.
- `Operating Income` is not mapped to `ebit`.

### Current limitations

- Uploaded files are previewed but not saved permanently.
- Mechanical cleaning is implemented but not yet connected to the UI.
- The `Clean data` button does not run cleaning yet.
- Orientation detection is not implemented yet.
- Schema validation is not implemented yet.
- Label mapping is not implemented yet.
- Safe derivations are not implemented yet.
- Identity checks are not implemented yet.
- Deduplication and conflict handling are not implemented yet.
- No SQL persistence exists yet.

### Next suggested step

Connect the `Clean data` action to mechanical cleaning for the uploaded in-memory previews, while still keeping orientation detection, schema validation, label mapping, derivations, identity checks, deduplication, persistence, and analysis features out of that step.
