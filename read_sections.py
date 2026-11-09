import pdfplumber
import re
import json

with pdfplumber.open("Catalogo.pdf") as pdf:
    pages_text = {}
    for i in range(len(pdf.pages)):
        pages_text[i+1] = pdf.pages[i].extract_text() or ""

# Let's inspect specific sections:
# 1. Mamãe e Bebê: pages 166-172
print("=== MAMÃE E BEBÊ (Pages 166-172) ===")
for p in range(166, 173):
    print(f"\n--- PAGE {p} ---")
    print(pages_text[p])

# 2. Naturé: pages 173-176
print("\n=== NATURÉ (Pages 173-176) ===")
for p in range(173, 177):
    print(f"\n--- PAGE {p} ---")
    print(pages_text[p])

# 3. Tododia Corpo & Sabonetes & Desodorantes: pages 134-146, 160-165
print("\n=== TODODIA CORPO & DESODORANTES (Pages 134-138, 161-164) ===")
for p in [134, 135, 136, 137, 138, 141, 142, 143, 144, 161, 162, 163]:
    lines = pages_text[p].split('\n')
    print(f"\n--- PAGE {p} (Sample lines) ---")
    for l in lines[:15]:
        print(f"  {l}")

# 4. Lumina: pages 184-188
print("\n=== LUMINA (Pages 184-188) ===")
for p in range(184, 189):
    print(f"\n--- PAGE {p} ---")
    print(pages_text[p])

# 5. Perfumaria Feminina & Spray / Mãos: pages 60-70
print("\n=== ESSENCIAL / LUNA (Pages 62-68) ===")
for p in range(62, 69):
    print(f"\n--- PAGE {p} ---")
    print(pages_text[p])
