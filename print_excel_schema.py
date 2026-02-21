import pandas as pd
import json

xl = pd.ExcelFile('TCF SALES MASTER DATA FILE.xlsx')
schema = {}
for sheet in xl.sheet_names:
    df = xl.parse(sheet)
    schema[sheet] = df.columns.tolist()

with open('excel_schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
print("Schema written to excel_schema.json")
