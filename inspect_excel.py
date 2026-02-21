import pandas as pd
try:
    path = "TCF SALES MASTER DATA FILE.xlsx"
    xlsx = pd.ExcelFile(path)
    sheet = "Enquiry Register - From 2019"
    if sheet in xlsx.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet, nrows=1)
        print("Columns in Enquiry Register:")
        cols = df.columns.tolist()
        for i, col in enumerate(cols):
            print(f"{i}: {col}")
    else:
        print(f"Sheet '{sheet}' not found. Available: {xlsx.sheet_names}")
except Exception as e:
    print(f"Error: {e}")
