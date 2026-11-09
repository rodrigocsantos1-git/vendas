import pdfplumber
import re
import json

keywords_map = {
    "146888": ("ESSENCIAL DES SPRAY EXCLU FEM 100ML", ["spray", "essencial exclusivo", "exclusivo feminino"]),
    "92796": ("MMBB SABONETE EM BARRA 2X100G", ["mame e beb", "mamae e bebe", "sabonete em barra", "2 unidades", "100 g"]),
    "21307": ("TODODIA OLEO DES HID COR CERE 120ML", ["leo", "bifsico", "cereja e avel", "120 ml", "tododia"]),
    "18978": ("TODODIA RF SAB LIQ CEREJA E AVELA 300ML", ["refil", "sabonete lquido", "cereja e avel", "300 ml"]),
    "174169": ("ESSENCIAL HID MAOS EXCL RAM 40G", ["mos", "essencial", "40 g", "exclusivo"]),
    "102412": ("NATURE COLONIA PULACORDA 100ML", ["pulacorda", "pula-corda", "pula corda", "natur", "subindo na arvore"]),
    "135049": ("MMBB CLASSICO HIDRA CORP 100ML", ["mame e beb", "hidratante", "100 ml", "relaxante"]),
    "194826": ("LUNA HID FASCINANTE FEM MAOS 40G", ["luna", "fascinante", "mos", "40 g"]),
    "194822": ("ESSENCIAL HID ATO FEM MAOS 40G", ["essencial ato", "ato", "mos", "40 g"]),
    "140689": ("MMBB HID PPBB CLAS 100ML", ["pele sensvel", "papo a papo", "mame", "beb", "100 ml"]),
    "174614": ("TODODIA HID DES CEREJA NEGRA 400ML", ["cereja negra", "400 ml", "jabuticaba"]),
    "114464": ("TODODIA SAB BARRA SORT 2 5X90G", ["sortidos", "sortidas", "coleo", "tododia sabonetes"]),
    "7733": ("TODODIA SAB BARRA TAMAR CANEL 5X90G", ["tamarindo", "canela", "tamar"])
}

with pdfplumber.open("Catalogo.pdf") as pdf:
    pages = [p.extract_text() or "" for p in pdf.pages]

print("Searching keywords...")
for code, (desc, kws) in keywords_map.items():
    print(f"\n=============================")
    print(f"Product {code}: {desc}")
    found = []
    for idx, page_t in enumerate(pages):
        page_lower = page_t.lower()
        score = sum(1 for kw in kws if kw in page_lower)
        if score >= 2:
            found.append((idx + 1, score, page_t))
    found.sort(key=lambda x: x[1], reverse=True)
    for p_num, sc, pt in found[:3]:
        print(f"  -> Page {p_num} (score {sc}):")
        lines = [l for l in pt.split('\n') if any(kw in l.lower() for kw in kws) or 'r$' in l.lower()]
        for l in lines[:8]:
            print(f"     {l}")
