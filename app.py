from flask import Flask, request, send_file, render_template_string
import pandas as pd
import io

app = Flask(__name__)

# Use the HTML above as template to serve index page:
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AutoClean: Data Cleaning Tool</title>
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #f7f9fc;
      margin: 0; padding: 0;
      display: flex; justify-content: center; align-items: center;
      height: 100vh;
      color: #333;
    }
    .container {
      background: white;
      max-width: 450px; width: 100%;
      padding: 2rem;
      border-radius: 10px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
      text-align: center;
    }
    h1 {
      margin-bottom: 1rem;
      color: #0056b3;
    }
    p.description {
      color: #555;
      margin-bottom: 2rem;
    }
    input[type="file"] {
      border: 2px dashed #0056b3;
      padding: 1.5rem;
      width: 100%;
      cursor: pointer;
      border-radius: 8px;
      transition: border-color 0.3s ease;
    }
    input[type="file"]:hover {
      border-color: #003d80;
    }
    button {
      background-color: #0056b3;
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      font-size: 1.1rem;
      margin-top: 1.5rem;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }
    button:hover {
      background-color: #003d80;
    }
    .footer {
      margin-top: 2rem;
      font-size: 0.85rem;
      color: #999;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>AutoClean</h1>
    <p class="description">Upload your messy CSV or Excel file to automatically clean it.</p>
    <form action="/upload" method="POST" enctype="multipart/form-data">
      <input type="file" name="file" accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" required />
      <button type="submit">Upload & Clean</button>
    </form>
    <div class="footer">
      &copy; 2025 AutoClean Data Analytics Project
    </div>
  </div>
</body>
</html>
"""

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Drop duplicate rows
    df = df.drop_duplicates()

    # 2. Strip whitespace from string columns
    str_cols = df.select_dtypes(include=['object']).columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # 3. Fill missing numeric values with median
    num_cols = df.select_dtypes(include=['number']).columns
    for col in num_cols:
        median_val = df[col].median()
        df[col].fillna(median_val, inplace=True)

    # 4. Fill missing categorical with mode
    for col in str_cols:
        mode_val = df[col].mode()
        if not mode_val.empty:
            df[col].fillna(mode_val[0], inplace=True)
        else:
            df[col].fillna("Unknown", inplace=True)

    # 5. Convert date columns (try parsing any column with datetime-like strings)
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass  # leave column as is if conversion fails

    return df

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    # Read uploaded file into pandas DataFrame
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return "Unsupported file format. Please upload CSV or Excel file.", 400
    except Exception as e:
        return f"Error reading file: {str(e)}", 400

    # Clean data
    cleaned_df = clean_data(df)

    # Prepare output file (CSV)
    output = io.StringIO()
    cleaned_df.to_csv(output, index=False)
    output.seek(0)

    # Send cleaned CSV back to user as attachment
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='cleaned_data.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
