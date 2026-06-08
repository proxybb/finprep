# Financial Data Application Skeleton

This repository is an early Flask skeleton for a financial data cleaning and analysis application. The first implementation focus will be the data cleaning workflow.

Naming and branding are not finalized. The preserved `old_engine_files` directory is archived reference material and is not part of the active application.

## Run Locally

1. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

2. Install requirements:

   ```powershell
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the app:

   ```powershell
   python app.py
   ```

The app exposes placeholder pages for the dashboard, data workflow, companies, and analysis. Business logic, persistence, metrics, charts, and analysis features are intentionally not implemented yet.
