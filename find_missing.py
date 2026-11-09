import pdfplumber
import re

with pdfplumber.open("Catalogo.pdf") as pdf:
    pages_text = {}
    for i in range(len(pdf.pages)):
        pages_text[i+1] = pdf.pages[i].extract_text() or ""

targets = [
    ("146888", "ESSENCIAL DES SPRAY EXCLU FEM 100ML", ["spray", "exclusivo"]),
    ("92796", "MMBB SABONETE EM BARRA 2X100G", ["sabonete", "100 g", "barra"]),
    ("21307", "TODODIA OLEO DES HID COR CERE 120ML", ["bifsico", "bifasico", "120 ml"]),
    ("18978", "TODODIA RF SAB LIQ CEREJA E AVELA 300ML", ["refil", "cereja", "300 ml"]),
    ("174169", "ESSENCIAL HID MAOS EXCL RAM 40G", ["mos", "maos", "40 g"]),
    ("102412", "NATURE COLONIA PULACORDA 100ML", ["pula", "natur", "colnia", "colonia"]),
    ("135049", "MMBB CLASSICO HIDRA CORP 100ML", ["hidratante", "100 ml", "beb", "bebe"]),
    ("194826", "LUNA HID FASCINANTE FEM MAOS 40G", ["luna", "mos", "fascinante"]),
    ("194822", "ESSENCIAL HID ATO FEM MAOS 40G", ["ato", "mos", "essencial"]),
    ("140689", "MMBB HID PPBB CLAS 100ML", ["papo", "100 ml", "beb"]),
    ("174614", "TODODIA HID DES CEREJA NEGRA 400ML", ["cereja negra", "jabuticaba", "400 ml"]),
    ("114464", "TODODIA SAB BARRA SORT 2 5X90G", ["sortido", "sortida", "5x90"]),
    ("189409", "TODODIA DES ROLLON MANGA ROSA 70ML", ["roll-on", "rollon", "manga rosa", "70 ml"])
]

for code, name, kws in targets:
    print(f"\n==========================================")
    print(f"SEARCHING FOR: [{code}] {name}")
    found = []
    for p_num, text in pages_text.items():
        t_lower = text.lower()
        if all(kw.lower() in t_lower for kw in kws[:2]):
            found.append(p_num)
    print(f"Pages with match: {found[:5]}")
    for p in found[:3]:
        print(f"--- PAGE {p} ---")
        lines = pages_text[p].split('\n')
        for l in lines:
            if any(kw.lower() in l.lower() for kw in kws) or 'r$' in l.lower():
                print(f"  {l}")
