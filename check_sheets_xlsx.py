import urllib.request
import ssl
import openpyxl
import io

url = "https://docs.google.com/spreadsheets/d/1V84XN7tx2jicDcC4YDrMPwBrJFaa-a7z7dkFoCgDoNE/export?format=xlsx"
ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

with urllib.request.urlopen(req, context=ctx) as resp:
    data = resp.read()
    print("XLSX Bytes received:", len(data))
    
    with open("planilha_google.xlsx", "wb") as f:
        f.write(data)

wb = openpyxl.load_workbook("planilha_google.xlsx")
print("Sheet names:", wb.sheetnames)

for sname in wb.sheetnames:
    sheet = wb[sname]
    print(f"\n--- Sheet '{sname}': max_row={sheet.max_row}, max_column={sheet.max_column} ---")
    for r in range(1, min(20, sheet.max_row + 1)):
        row_vals = [sheet.cell(r, c).value for c in range(1, min(15, sheet.max_column + 1))]
        if any(v is not None for v in row_vals):
            print(f"Row {r}: {row_vals}")
