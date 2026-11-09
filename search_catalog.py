import pdfplumber
import re
import json

prods_info = [
    {"codigo": "2832", "descricao": "TODODIA SAB BARRA NOZ PECA 5X90G"},
    {"codigo": "72147", "descricao": "TODODIA SAB BARRA ALECR SALVIA 5X90G"},
    {"codigo": "214468", "descricao": "TODODIA SAB BAR J ROSA FLOR CAJU 5X90G"},
    {"codigo": "2829", "descricao": "TODODIA SAB BARRA MACADA 5X90G"},
    {"codigo": "87512", "descricao": "TODODIA SAB BARRA AMORA VERM JABUT 5X90G"},
    {"codigo": "7733", "descricao": "TODODIA SAB BARRA TAMAR CANEL 5X90G"},
    {"codigo": "121969", "descricao": "TODODIA SAB BARRA CAMOMILA LAVANDA 5X90"},
    {"codigo": "205939", "descricao": "TODODIA SAB BAR MORANG E BAU DOU 5X90G"},
    {"codigo": "95560", "descricao": "ESSENCIAL SUPREME MASC DEO PARFUM 100ML"},
    {"codigo": "76423", "descricao": "ESSENCIAL EXC DEO PARFUM FEM 100ML 2020"},
    {"codigo": "72468", "descricao": "KMAX MASC DEO PARFUM 100ML"},
    {"codigo": "108401", "descricao": "KAIAK URBE MASC DES COL 100ML"},
    {"codigo": "180469", "descricao": "TODODIA DES HID CORP ILU DOUR ACER 150ML"},
    {"codigo": "146888", "descricao": "ESSENCIAL DES SPRAY EXCLU FEM 100ML"},
    {"codigo": "17049", "descricao": "ESSENCIAL OUD VANIL DEO PARFU FEM 100ML"},
    {"codigo": "92796", "descricao": "MMBB SABONETE EM BARRA 2X100G"},
    {"codigo": "21307", "descricao": "TODODIA OLEO DES HID COR CERE 120ML"},
    {"codigo": "18978", "descricao": "TODODIA RF SAB LIQ CEREJA E AVELA 300ML"},
    {"codigo": "174169", "descricao": "ESSENCIAL HID MAOS EXCL RAM 40G"},
    {"codigo": "102412", "descricao": "NATURE COLONIA PULACORDA 100ML"},
    {"codigo": "147418", "descricao": "LUMINA COND MASC NUTRICAO 250ML"},
    {"codigo": "135049", "descricao": "MMBB CLASSICO HIDRA CORP 100ML"},
    {"codigo": "194826", "descricao": "LUNA HID FASCINANTE FEM MAOS 40G"},
    {"codigo": "194822", "descricao": "ESSENCIAL HID ATO FEM MAOS 40G"},
    {"codigo": "140689", "descricao": "MMBB HID PPBB CLAS 100ML"},
    {"codigo": "189409", "descricao": "TODODIA DES ROLLON MANGA ROSA 70ML"},
    {"codigo": "102417", "descricao": "NATURE SAB LIQUIDO 250ML"},
    {"codigo": "174614", "descricao": "TODODIA HID DES CEREJA NEGRA 400ML"},
    {"codigo": "114464", "descricao": "TODODIA SAB BARRA SORT 2 5X90G"}
]

with pdfplumber.open("Catalogo.pdf") as pdf:
    pages_text = [p.extract_text() or "" for p in pdf.pages]

print(f"Loaded {len(pages_text)} pages.")

results = {}

for p in prods_info:
    code = p['codigo']
    desc = p['descricao']
    matched_pages = []
    
    # 1. Search code
    pat = rf'\({code}\)|\b{code}\b'
    for idx, t in enumerate(pages_text):
        if re.search(pat, t):
            matched_pages.append((idx + 1, "code", t))
            
    results[code] = {
        "item": p,
        "matched_pages": matched_pages
    }

print("\n=== MATCHED BY CODE ===")
for code, data in results.items():
    mp = data['matched_pages']
    if mp:
        pages_str = ", ".join([str(p[0]) for p in mp])
        print(f"Code {code} ({data['item']['descricao']}): Pages {pages_str}")
    else:
        print(f"Code {code} ({data['item']['descricao']}): NOT FOUND BY CODE")
