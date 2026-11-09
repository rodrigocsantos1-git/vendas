import urllib.request
import ssl
import pandas as pd
import io

SHEET_ID = "1V84XN7tx2jicDcC4YDrMPwBrJFaa-a7z7dkFoCgDoNE"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
XLSX_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

def fetch_google_sheet():
    ctx = ssl.create_default_context()
    req = urllib.request.Request(CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            content = resp.read()
            df = pd.read_csv(io.BytesIO(content))
            return df, None
    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    df, err = fetch_google_sheet()
    if err:
        print("Erro ao acessar planilha:", err)
    else:
        print("Planilha obtida com sucesso!")
        print("Colunas:", df.columns.tolist())
        print("Linhas:", len(df))
        print(df.head())
