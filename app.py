from flask import Flask, render_template, request, session
import os
from core.cleaner import mechanical_clean, read_uploaded_file
from core.mapper import apply_statement_mappings

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-finprep")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/clean", methods=["GET", "POST"])
def clean():
    cleaned_previews = {}
    uploaded_files = {}
    errors = {}
    
    if request.method == "POST":
        statement_types = {
            "income": "Income Statement",
            "balance_sheet": "Balance Sheet",
            "cash_flow": "Cash Flow Statement",
        }
        
        for key, label in statement_types.items():
            if key in request.files:
                file = request.files[key]
                if file and file.filename:
                    df = read_uploaded_file(file, file.filename)
                    if df is not None:
                        # Pipeline: mechanical cleaning → statement mapping
                        cleaned_df = mechanical_clean(df, statement_type=key)
                        mapped_df = apply_statement_mappings(cleaned_df, statement_type=key)
                        
                        uploaded_files[key] = label
                        # Store cleaned data as HTML table preview (limit to first 20 rows)
                        cleaned_previews[key] = mapped_df.head(20).to_html(
                            classes="preview-table",
                            escape=False,
                            index=False,
                        )
                    else:
                        errors[key] = f"Could not read {label} file. Please upload a CSV or Excel file."
    
    return render_template(
        "clean.html",
        cleaned_previews=cleaned_previews,
        uploaded_files=uploaded_files,
        errors=errors,
    )


@app.route("/companies")
def companies():
    return render_template("companies.html")


@app.route("/analysis")
def analysis():
    return render_template("analysis.html")


if __name__ == "__main__":
    app.run(debug=True)

