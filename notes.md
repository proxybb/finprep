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
