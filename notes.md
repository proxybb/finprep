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
- Each uploaded preview shows filename and shape, such as `filename.csv - 42 rows x 6 columns`.
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

## 15. Temporary upload storage and mechanical cleaning button update

### What changed

The Data workflow now keeps uploaded files in temporary server-side working storage and uses those files when the user clicks `Clean data`. The cleaned preview page now runs Stage 1 mechanical cleaning instead of showing placeholder standardized output.

### Files touched

- `.gitignore`
- `web/__init__.py`
- `web/routes.py`
- `web/templates/data.html`
- `web/templates/cleaned_data.html`
- `web/static/css/main.css`
- `tests/test_routes.py`
- `notes.md`

### Preview display change

The raw preview keeps the existing Income Statement, Balance Sheet, and Cash Flow Statement tabs, but the table styling was adjusted for easier vertical scanning. Raw preview tables no longer stretch sparse uploads across the full page, row spacing is tighter, alternating rows improve scanning, and horizontal scrolling remains available for genuinely wide files. This is a display-only change and does not alter the underlying raw DataFrame.

### Temporary upload and session design

Uploaded files that pass ingestion are saved under `data/temp_uploads/<upload_id>/` with secure filenames and a small server-side metadata file. Flask session stores only `current_upload_id`; it does not store pandas DataFrames or uploaded file contents. This temporary upload storage is working-session storage only and is not SQL persistence.

### Clean data button behavior

The `Clean data` button now uses `current_upload_id` to load the same temporary uploaded files on `/data/cleaned`. Each file is read again through `cleaning.ingest.read_uploaded_file`, then passed to `cleaning.mechanical.run_mechanical_cleaning`.

### Mechanical-only boundary

Only mechanical cleaning runs for now. The cleaned preview shows cleaned DataFrame previews, post-cleaning shape, and the mechanical audit summary, including dropped rows, dropped columns, normalized headers, missing values normalized, numeric values converted, and period labels normalized.

### Raw preview boundary

Raw preview remains raw. Uploaded labels and values are displayed as ingested: values such as `$1,200` remain `$1,200`, `Operating Income` remains `Operating Income`, `Sales` is not mapped to `revenue`, and `Operating Income` is not mapped to `ebit`.

### Known limitations

- Clean data currently runs only mechanical cleaning.
- Orientation detection is not implemented yet.
- Schema validation is not implemented yet.
- Label mapping is not implemented yet.
- Derivations are not implemented yet.
- Identity checks are not implemented yet.
- Temporary uploaded files are working-session files only.
- No SQL persistence exists yet.

### Next suggested step

Add orientation detection as the next pipeline stage after mechanical cleaning, while keeping raw preview and temporary upload storage boundaries unchanged.

## 16. Mechanical cleaning refinement update

### What changed

Mechanical cleaning was refined before committing. It now removes exact duplicate rows after basic mechanical normalization, normalizes historical actual period suffixes, preserves forecast and estimate suffixes for later validation, and keeps detailed mechanical audit data internal instead of showing it prominently on the cleaned preview page.

### Files touched

- `cleaning/audit.py`
- `cleaning/mechanical.py`
- `tests/test_mechanical.py`
- `tests/test_routes.py`
- `web/templates/cleaned_data.html`
- `web/static/css/main.css`
- `notes.md`

### Duplicate-row mechanical cleaning rule

Mechanical cleaning now drops exact full-row duplicates after basic normalization and keeps the first occurrence. This applies only when the whole row is identical. It does not drop rows just because they share the same year, and it does not drop, merge, or resolve duplicate period/year columns.

### Actual-period suffix normalization rule

Historical actual period suffixes are mechanically normalized:

- `2021A` becomes `2021`
- `2022A` becomes `2022`
- `FY2021A` becomes `2021`
- `FY 2021A` becomes `2021`

### Estimate/forecast suffix preservation rule

Forecast and estimate suffixes are preserved for later validation:

- `2024E` remains `2024E`
- `2025F` remains `2025F`

These periods are not blocked yet because schema and period validation are later-stage responsibilities.

### User-facing audit visibility decision

The cleaned preview page no longer shows a detailed mechanical audit summary or header-change log. It shows only the neutral status `Mechanical cleaning applied.` Detailed audit/change logs remain available internally and will be surfaced later in the analyst review/user-decision flow.

### Table display adjustment

Raw and cleaned preview tables were adjusted to stay compact instead of stretching across the full card when there are few columns. The first column remains readable, columns use less empty spacing, horizontal scrolling remains available for genuinely wide files, and expand/fullscreen behavior still works without transposing the DataFrame.

### Known limitations

- Orientation detection is not implemented yet.
- Schema validation is not implemented yet.
- Forecast/estimate periods are preserved for later validation but not blocked yet.
- Label mapping is not implemented yet.
- Derivations are not implemented yet.
- Identity checks are not implemented yet.
- SQL persistence is not implemented yet.

### Next suggested step

Implement orientation detection as the next automated pipeline stage after mechanical cleaning, while continuing to leave duplicate period conflicts, unsupported forecast/estimate periods, label mapping, derivations, and identity checks to their later stages.

## 17. Mechanical cleaning final conservative refinements

### What changed

Currency parsing configuration was moved out of mechanical cleaning into
`configs/currencies.py`. The supported currency-code list is used only to strip
known currency-code noise from numeric-looking strings during mechanical parsing;
it does not perform currency conversion or semantic label mapping.

Header normalization was expanded to cover more mechanical text cleanup:
underscores, hyphens, slashes, periods, commas, and newlines become spaces,
apostrophes are removed, repeated whitespace is collapsed, and common unit
suffixes such as `$MM`, `$M`, `US Dollars`, `USD`, `millions`, and `thousands`
are removed from header labels.

Unknown uppercase tokens around numbers are now preserved. For example,
`USD 1,200` and `1,200 JOD` are parsed as numeric values, but `ABC 100` and
`XYZ 1,200` remain text.

### Known limitations

- This is parsing configuration only, not currency conversion.
- Mechanical cleaning still does not map labels such as `Sales` to `revenue` or
  `Operating Income` to `ebit`.
- Duplicate period/year columns are still preserved for later validation.
- Forecast and estimate periods such as `2024E` and `2025F` are still preserved
  for later validation.
- Orientation detection, schema validation, derivations, identity checks, SQL
  persistence, metrics, charts, summaries, red flags, valuation, and AI are not
  implemented in this stage.

### Next suggested step

Add the next pipeline stage only after the mechanical-cleaning contract is
accepted, with duplicate-period conflict handling, label mapping, validation,
and derivations remaining outside the mechanical layer.

## 18. Stage 2 orientation detection update

### What orientation detection does

Stage 2 orientation detection now runs after mechanical cleaning and before the
cleaned preview is rendered. Its target analyst format is:

`line_item | 2021 | 2022 | 2023`

This stage changes table shape only. It puts historical year periods across the
top and statement item labels down the left side when the table orientation is
clear. It does not understand accounting meaning and does not map labels.

### Why it is separate from mechanical cleaning

Mechanical cleaning remains responsible for structural cleanup such as blank
normalization, numeric parsing, header cleanup, period-label cleanup, and exact
duplicate full-row removal. Orientation detection is a separate Stage 2 pass
because transposing a table changes its shape and should be auditable as its own
pipeline decision.

### Detection rules

- Already standard: two or more simple historical year labels appear in column
  headers, and the first column mostly contains non-year text labels. The table
  is left unchanged.
- Transposed or sideways: the first column contains two or more simple
  historical year labels, and the other column headers look like statement item
  labels. The table is transposed to analyst-style orientation.
- Uncertain: if there are not enough historical year labels in either place, no
  transpose is attempted and the table is left unchanged.

Forecast and estimate periods such as `2024E` and `2025F` are preserved but do
not drive confident orientation decisions yet.

### Cleaned preview behavior

The cleaned preview now shows the result of mechanical cleaning followed by
orientation detection. It displays neutral status messages only:

- `Mechanical cleaning applied.`
- `Orientation normalized.` when a table is transposed.
- `Orientation already standard.` when no transpose is needed.
- `Orientation uncertain; table left unchanged.` when the heuristic does not
  have enough evidence.

Raw preview remains raw and is not affected by mechanical cleaning or
orientation detection.

### Known limitations

- Orientation detection is heuristic and conservative.
- Uncertain tables are left unchanged.
- Forecast/estimate periods are preserved for later validation.
- Duplicate period conflicts are not resolved.
- Label mapping is not implemented.
- Schema validation is not implemented.
- Derivations are not implemented.
- Identity checks are not implemented.
- SQL persistence is not implemented.
- Metrics, charts, summaries, red flags, valuation, and AI are not implemented.

### Next suggested step

Implement schema validation as the next separate pipeline stage, while keeping
label mapping, derivations, identity checks, duplicate-period conflict
resolution, and persistence out of orientation detection.

## 19. Stage 2 orientation boundary refinement

### What changed

Orientation detection now performs a conservative leading table-boundary cleanup
before deciding whether to transpose. Leading metadata/title rows such as
`Company: DemoComp`, `Statement: Income Statement`, `Currency: USD`,
`Units: USD millions`, and `Prepared by ...` are removed only when they appear
before the actual table begins. Matching rows in the middle of a statement are
left unchanged.

When a metadata row caused pandas to treat the metadata as column headers,
orientation detection can promote a clear leading table-header row, such as
`Year | Sales | Operating Income`, before applying orientation rules. Promoted
headers receive the same mechanical header cleanup used by normal uploaded
headers.

### Company and first-column display labels

Company metadata is intentionally not stored or displayed during the cleaned
preview stage. Company name will be collected or confirmed later during the
Save Data stage.

Leading metadata rows are removed only to protect the table boundary before
orientation detection. The cleaned/oriented preview always renders the first
visible column header as blank so the user does not see internal handoff labels
such as `line_item` or source metadata such as `Company: DemoComp`.

### Period-label refinement

Mechanical period normalization now recognizes common balance-sheet style
labels:

- `as of 2021` becomes `2021`
- `As of 2021` becomes `2021`
- `as of Dec 31, 2021` becomes `2021`
- `As of December 31, 2021` becomes `2021`

This remains mechanical period-label cleanup only. It does not decide statement
type or validate accounting content.

### Known limitations

- Metadata-row removal is conservative and focused on leading metadata only.
- Unrecognized metadata formats may remain in uncertain tables.
- Orientation detection is still heuristic and leaves uncertain tables
  unchanged.
- Forecast/estimate periods are preserved for later validation.
- Duplicate period conflicts are not resolved.
- Label mapping is not implemented.
- Schema validation is not implemented.
- Derivations are not implemented.
- Identity checks are not implemented.
- SQL persistence is not implemented.
- Metrics, charts, summaries, red flags, valuation, and AI are not implemented.

### Next suggested step

Review the Stage 1 and Stage 2 handoff with representative uploads, then add
schema validation as a separate Stage 3 without mixing it into mechanical
cleaning or orientation detection.

## 20. Table-boundary cleanup split from orientation

### What changed

The Stage 2 spike was refactored so table-boundary cleanup is separate from
orientation detection. The cleaned-preview pipeline now runs:

`mechanical cleaning -> table-boundary cleanup -> orientation detection -> table preview`

`cleaning/table_boundary.py` owns leading metadata/title row removal and clear
header-row promotion when pandas parsed metadata as headers. It does not store
or preserve company metadata for preview display.

`cleaning/orientation.py` now assumes it receives a bounded table. It only
detects already-standard tables, detects sideways tables, transposes when clear,
and leaves uncertain tables unchanged.

### Why this separation exists

Metadata and table-boundary cleanup answer where the real table starts.
Orientation detection answers whether periods are already across the top or need
to be transposed. Keeping these decisions separate makes each stage easier to
test and avoids hiding metadata parsing inside orientation heuristics.

### Display behavior

The cleaned preview always renders the first visible header as blank. Internal
handoff columns such as `line_item` remain internal and are not shown to the
user. Company name is intentionally not displayed or stored at this stage
because it will be collected or confirmed later during Save Data.

Raw preview remains raw and does not run mechanical cleaning, table-boundary
cleanup, or orientation detection.

### Known limitations

- Table-boundary cleanup is conservative and only removes leading metadata.
- Metadata-like rows in the middle of a statement are preserved.
- Unrecognized metadata formats may remain in uncertain tables.
- Company metadata is not available to downstream stages yet.
- Orientation detection is heuristic and leaves uncertain tables unchanged.
- Forecast/estimate periods are preserved for later validation.
- Duplicate period conflicts are not resolved.
- Label mapping is not implemented.
- Schema validation is not implemented.
- Derivations are not implemented.
- Identity checks are not implemented.
- SQL persistence is not implemented.

### Next suggested step

Review the cleaned preview with representative uploads, then add the Save Data
stage where the user can enter or confirm company name before any persistence,
schema validation, mapping, derivations, or identity checks are introduced.

## 21. Data workflow route and preview refinement

### What changed

The Data workflow is now split into clearer routes:

- `/data` redirects to `/data/upload`.
- `/data/upload` handles file upload and raw preview only.
- `/data/cleaned` shows cleaned, table-bounded, orientation-normalized preview
  output only.

The sidebar Data link points to `/data/upload`. The upload page is labeled as
upload/raw preview, uses the action text `Upload and preview`, and includes a
small selected-filename display next to each file input. This is client-side UI
feedback only; there is no backend preload, async upload endpoint, or JavaScript
file parsing.

### Cleaned preview behavior

Company name is still intentionally deferred to Save Data. It is not stored or
displayed in the upload/raw preview workflow or cleaned preview workflow.

Leading metadata rows such as `Company:`, `Title:`, `Statement:`, `Currency:`,
and `Units:` are removed only to protect the table boundary before orientation.
For leading rows, the first cell controls this cleanup even if other cells
contain junk text. Metadata-like rows in the middle of a statement are
preserved.

Annotation/comment columns are removed from the cleaned working table before
orientation when their headers are `notes`, `note`, `comments`, `comment`,
`remarks`, `remark`, or `extra blank col`. Raw preview still shows those columns
exactly as uploaded. This is not semantic label mapping. Later schema
validation or issue reporting may surface comments and inconsistencies
separately.

Blank or missing cells in cleaned preview are visually highlighted with a
restrained warning style. This is display-only. Missing values are not filled,
calculated, or converted into formal validation issues yet.

The cleaned preview first visible column header remains intentionally blank so
internal handoff labels such as `line_item` are not shown.

### Future async preload idea

A future version may preload files before final upload:

- user selects a file
- frontend sends it to a temporary preview endpoint
- backend ingests and stages the file
- final action confirms the staged upload

This is deferred because it adds async upload state, temporary lifecycle
handling, and abandoned-file cleanup.

### Known limitations

- Save Data is not implemented.
- SQL persistence is not implemented.
- Label mapping is not implemented.
- Schema validation is not implemented.
- Derivations are not implemented.
- Identity checks are not implemented.
- Red flags, charts, valuation, summaries, AI, and metrics are not implemented.
- Annotation/comment content is dropped from the cleaned working table for now
  rather than preserved as review issues.
- Orientation detection remains heuristic and leaves uncertain tables unchanged.
- Duplicate period conflicts are not resolved.

### Next suggested step

Review upload/raw preview and cleaned preview with representative files, then
design the Save Data step where the user confirms company name before any
persistence or validation workflow is introduced.

## 22. Table-boundary metadata API simplification

### What changed

`TableBoundaryResult` no longer exposes a `metadata` field. The table-boundary
stage now uses simple metadata-prefix detection only to decide whether leading
rows should be removed before orientation.

This is a refactor only, not a product behavior change.

### Behavior preserved

Leading metadata rows such as `Company:`, `Title:`, `Statement:`, `Currency:`,
and `Units:` are still removed from cleaned working tables to protect table
boundary detection. Metadata-like rows in the middle of a statement are still
preserved. Annotation/comment columns are still removed from the cleaned working
table before orientation. Raw preview remains raw.

Company name remains deferred to Save Data and is not stored, displayed, or
passed through the cleaned-preview route payload at this stage.

### Route payload cleanup

The cleaned-preview route no longer passes unused mechanical audit or
table-boundary payload fields to the template. Orientation status and message
remain available because they are part of the current cleaned preview display.

### Next suggested step

Continue reviewing the current upload and cleaned-preview flow with real sample
files before adding the Save Data step.

## 23. Period mapping module refactor

### What changed

Period-label normalization was moved out of `cleaning/mechanical.py` into
`cleaning/period_mapping.py`.

### Files touched

- `cleaning/mechanical.py`
- `cleaning/period_mapping.py`
- `notes.md`

### Why it changed

Period normalization is still part of the pre-orientation mechanical cleanup
pipeline, but it now lives in its own small module so future label mapping can
be added separately without mixing accounting label semantics into mechanical
cleaning.

### Current behavior

The cleaned-preview pipeline remains:

`ingestion -> mechanical cleaning -> table-boundary cleanup -> orientation detection`

Raw preview remains raw. Mechanical cleaning still normalizes obvious annual
period labels before table-boundary cleanup and orientation detection. Existing
behavior is preserved for labels such as `FY2021`, `2021A`, `as of 2021`, and
`Dec-2022`. Forecast and estimate labels such as `2024E` and `2025F` remain
preserved for later validation. Duplicate period columns remain preserved.

### Known limitations

- Label mapping is not implemented.
- Schema validation is not implemented in this refactor.
- Derivations are not implemented in this refactor.
- Identity checks are not implemented.
- SQL persistence is not implemented.
- Forecast/estimate periods are preserved but not validated here.
- Duplicate period conflicts are not resolved here.

### Next suggested step

Implement Stage 4 label mapping as a separate module and pipeline stage, keeping
period normalization before table-boundary cleanup and orientation detection.

## 24. Stage 4A-1 Balance Sheet Assets mapping backend

### What changed

Backend-only deterministic label mapping was added for Balance Sheet Assets.
The mapper receives a cleaned/oriented DataFrame, treats the first column as the
statement label, preserves row order and values, and appends mapping metadata
columns for later analysis.

### Files touched

- `cleaning/mapping.py`
- `tests/test_mapping.py`
- `notes.md`

### Why it changed

This starts Stage 4 label mapping without changing upload, raw preview,
mechanical cleaning, table-boundary cleanup, orientation, routing, UI,
validation, derivations, identity checks, rollups, or persistence.

### Current behavior

- `map_statement_rows(df, statement_type)` supports only `balance_sheet`.
- Unsupported statement types raise a clean `ValueError`.
- Balance Sheet Asset aliases map to internal canonicals such as
  `cash_and_equivalents`, `accounts_receivable`, `receivables_total`,
  `inventory`, `current_assets`, `pp_and_e`, and `total_assets`.
- Special labels are tagged as `review_only`, `deferred`, or `unmapped` instead
  of being forced into narrow canonicals.
- Each output row receives mapping metadata and an audit record with the same
  metadata.
- Input DataFrames are copied and not mutated.
- Period columns and numeric values remain unchanged.
- Duplicate canonical mappings remain as separate rows.

### Known limitations

- Liabilities and equity mapping are not implemented.
- Income statement and cash flow mapping are not implemented.
- Mapping is not wired into Flask routes or the cleaned preview pipeline.
- Schema validation, derivations, identity checks, rollups, and SQL persistence
  are not implemented.
- Matching is exact after small deterministic label normalization; there is no
  fuzzy matching.

### Next suggested step

Review the Balance Sheet Assets mapping rules against representative uploads,
then implement the next scoped mapping slice separately without wiring mapping
into routes until the backend contract is accepted.

## 25. Stage 4A-2 Balance Sheet Liabilities mapping backend

### What changed

Backend-only deterministic label mapping was extended from Balance Sheet Assets
to include Balance Sheet Liabilities. The existing public mapper and metadata
contract were preserved.

### Files touched

- `cleaning/mapping.py`
- `tests/test_mapping.py`
- `notes.md`

### Why it changed

This adds the next Balance Sheet mapping slice without implementing equity,
income statement mapping, cash flow mapping, route wiring, UI changes,
validation, derivations, identity checks, rollups, or persistence.

### Current behavior

- `map_statement_rows(df, statement_type)` still supports only
  `balance_sheet`.
- The mapper still copies input DataFrames, uses the first column as the label
  column, preserves original labels, preserves period values, keeps row order,
  and does not drop or deduplicate rows.
- Liability aliases now map or tag metadata for `accounts_payable`,
  `payables_total`, `accrued_expenses`, `current_liabilities`, and
  `total_liabilities`.
- Broader or composite payable labels are marked `review_only`.
- Accrual labels are marked `deferred` while carrying `accrued_expenses`
  canonical metadata for future analysis.
- Debt, leases, provisions, tax liabilities, deferred revenue, and contract
  liabilities are deferred and not included as primary liability canonicals.
- Accounting-equation totals such as total liabilities and equity are marked
  `review_only` and are not mapped to `total_liabilities`.
- Matching remains exact after deterministic label normalization only.

### Known limitations

- Equity mapping is not implemented.
- Income statement and cash flow mapping are not implemented.
- Mapping is still not wired into Flask routes or the cleaned preview pipeline.
- Schema validation, derivations, identity checks, rollups, and SQL persistence
  are not implemented.
- No fuzzy matching or synonym inference exists.

### Next suggested step

Review the combined Balance Sheet Assets and Liabilities mapping rules against
representative uploads, then implement Balance Sheet Equity mapping as the next
separate backend-only slice.

## 26. Stage 4A-3 Balance Sheet Equity mapping backend

### What changed

Backend-only deterministic Balance Sheet mapping was extended to include Equity
labels. The existing mapper signature and metadata fields were preserved.

### Files touched

- `cleaning/mapping.py`
- `tests/test_mapping.py`
- `notes.md`

### Why it changed

This completes the initial backend-only Balance Sheet mapping coverage across
assets, liabilities, and equity without wiring mapping into routes, changing
preview behavior, adding validation, deriving values, checking identities,
rolling up rows, or persisting data.

### Current behavior

- `map_statement_rows(df, statement_type)` still supports only
  `balance_sheet`.
- Only explicit total equity labels auto-map to `total_equity`.
- Owner-only equity labels such as shareholders equity, stockholders equity,
  and equity attributable to owners of the parent are `review_only` because
  they may exclude non-controlling interests.
- Equity components such as retained earnings, share capital, treasury stock,
  and accumulated other comprehensive income are deferred.
- Non-controlling interest and minority interest labels are deferred.
- Accounting-equation totals such as total equity and liabilities are
  `review_only` and are not mapped to `total_equity`.
- The mapper still copies input DataFrames, preserves period values and signs,
  preserves row order, keeps duplicate canonical mappings, and does exact
  deterministic matching only.

### Known limitations

- Income statement and cash flow mapping are not implemented.
- Mapping is still not wired into Flask routes or the cleaned preview pipeline.
- Schema validation, derivations, identity checks, rollups, and SQL persistence
  are not implemented.
- Equity component analysis and non-controlling interest handling are deferred.
- No fuzzy matching or synonym inference exists.

### Next suggested step

Review representative Balance Sheet uploads against the combined asset,
liability, and equity mappings, then decide whether to wire Balance Sheet
mapping into an internal backend pipeline step or implement the next statement
mapping slice separately.

## 27. Single-statement upload workflow verification

### What changed

Route tests were expanded to lock the existing behavior that one uploaded
statement is enough for upload/raw preview and cleaned preview workflows.

### Files touched

- `tests/test_routes.py`
- `notes.md`

### Why it changed

Users need to be able to upload only one statement, especially a Balance Sheet,
without being blocked by missing Income Statement or Cash Flow Statement files.
The route implementation already skipped missing upload slots and processed
only saved uploaded statements, so no route or template changes were needed.

### Current behavior

- `/data/upload` accepts only Income Statement, only Balance Sheet, only Cash
  Flow Statement, or any combination of those files.
- Missing statement slots are ignored during ingestion and are shown as neutral
  empty preview states.
- At least one valid uploaded file creates temporary upload metadata for the
  current session.
- Posting no files leaves the page in the no-upload preview state and does not
  create a current upload id.
- `/data/cleaned` runs the existing pipeline only for uploaded statements:
  ingestion, mechanical cleaning, table-boundary cleanup, and orientation
  detection.
- Unsupported uploaded files still show clean ingestion errors for the affected
  statement slot.
- Raw preview remains raw and label mapping is still not wired into routes.

### Known limitations

- Cleaned preview still shows neutral empty tabs for missing statements.
- Temporary uploaded files are still working-session files only.
- Mapping, schema validation, derivations, identity checks, rollups, and SQL
  persistence are still not wired into the workflow.

### Next suggested step

Review the single-statement workflow manually with representative Balance Sheet
uploads, then decide whether the next backend step should wire Balance Sheet
mapping internally or keep expanding statement mapping coverage first.

## 28. Balance Sheet mapping wired into cleaned backend flow

### What changed

The cleaned preview backend now applies Balance Sheet label mapping after the
existing cleaned pipeline finishes ingestion, mechanical cleaning,
table-boundary cleanup, and orientation detection.

### Files touched

- `web/routes.py`
- `web/templates/cleaned_data.html`
- `tests/test_routes.py`
- `notes.md`

### Why it changed

Balance Sheet asset, liability, and equity mapping already existed as backend
logic. This wires that mapper into the cleaned Balance Sheet flow only, so the
mapped DataFrame and metadata columns can be inspected before any later schema,
identity, derivation, rollup, or persistence work.

### Current behavior

- Raw preview remains raw and does not run mapping.
- `/data/cleaned` runs mapping only for uploaded Balance Sheet files.
- Income Statement and Cash Flow cleaned previews continue through the existing
  cleaning, table-boundary, and orientation pipeline without mapping.
- Balance Sheet cleaned preview now includes the mapping metadata columns
  appended by `map_statement_rows`.
- Cleaned preview status copy now indicates label mapping is Balance Sheet only.
- Original labels, row order, duplicate rows, and period values are preserved.
- If Balance Sheet mapping raises a clean error, the cleaned page renders an
  error for that statement instead of returning a 500.

### Known limitations

- Income Statement and Cash Flow mapping are not implemented or wired.
- Schema validation, derivations, identity checks, rollups, and SQL persistence
  are not implemented.
- Mapping metadata is shown directly in the cleaned preview table for this
  backend proof step.
- Mapping audit records are not surfaced separately yet.

### Next suggested step

Review Balance Sheet cleaned previews with representative uploads, then decide
whether to add a review-oriented display for mapping metadata or keep the next
step backend-only.
