import pdfplumber
import re
import json

with pdfplumber.open("Catalogo.pdf") as pdf:
    pages_text = {}
    for i in range(len(pdf.pages)):
        pages_text[i+1] = pdf.pages[i].extract_text() or ""

def search_text(term, max_results=5):
    matches = []
    for p_num, text in pages_text.items():
        if term.lower() in text.lower():
            matches.append((p_num, text))
    return matches

prods = [
    ("2832", "TODODIA SAB BARRA NOZ PECA 5X90G"),
    ("72147", "TODODIA SAB BARRA ALECR SALVIA 5X90G"),
    ("214468", "TODODIA SAB BAR J ROSA FLOR CAJU 5X90G"),
    ("2829", "TODODIA SAB BARRA MACADA 5X90G"),
    ("87512", "TODODIA SAB BARRA AMORA VERM JABUT 5X90G"),
    ("7733", "TODODIA SAB BARRA TAMAR CANEL 5X90G"),
    ("121969", "TODODIA SAB BARRA CAMOMILA LAVANDA 5X90"),
    ("205939", "TODODIA SAB BAR MORANG E BAU DOU 5X90G"),
    ("95560", "ESSENCIAL SUPREME MASC DEO PARFUM 100ML"),
    ("76423", "ESSENCIAL EXC DEO PARFUM FEM 100ML 2020"),
    ("72468", "KMAX MASC DEO PARFUM 100ML"),
    ("108401", "KAIAK URBE MASC DES COL 100ML"),
    ("180469", "TODODIA DES HID CORP ILU DOUR ACER 150ML"),
    ("146888", "ESSENCIAL DES SPRAY EXCLU FEM 100ML"),
    ("17049", "ESSENCIAL OUD VANIL DEO PARFU FEM 100ML"),
    ("92796", "MMBB SABONETE EM BARRA 2X100G"),
    ("21307", "TODODIA OLEO DES HID COR CERE 120ML"),
    ("18978", "TODODIA RF SAB LIQ CEREJA E AVELA 300ML"),
    ("174169", "ESSENCIAL HID MAOS EXCL RAM 40G"),
    ("102412", "NATURE COLONIA PULACORDA 100ML"),
    ("147418", "LUMINA COND MASC NUTRICAO 250ML"),
    ("135049", "MMBB CLASSICO HIDRA CORP 100ML"),
    ("194826", "LUNA HID FASCINANTE FEM MAOS 40G"),
    ("194822", "ESSENCIAL HID ATO FEM MAOS 40G"),
    ("140689", "MMBB HID PPBB CLAS 100ML"),
    ("189409", "TODODIA DES ROLLON MANGA ROSA 70ML"),
    ("102417", "NATURE SAB LIQUIDO 250ML"),
    ("174614", "TODODIA HID DES CEREJA NEGRA 400ML"),
    ("114464", "TODODIA SAB BARRA SORT 2 5X90G")
]

# Let's inspect each item
for code, name in prods:
    # First search for code
    found_by_code = False
    for p_num, text in pages_text.items():
        if f"({code})" in text or f" {code} " in text:
            print(f"[{code}] {name} -> FOUND on Page {p_num}")
            found_by_code = True
            # print surrounding lines
            for l in text.split('\n'):
                if any(x in l for x in [code, 'R$', 'pts']):
                    print(f"   {l}")
            break
    if not found_by_code:
        print(f"[{code}] {name} -> NOT FOUND BY CODE, searching keywords...")
