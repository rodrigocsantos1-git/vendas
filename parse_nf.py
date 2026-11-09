import pdfplumber
import re
import json

def parse_items():
    with pdfplumber.open("Nota_fiscal_05_11_2026.pdf") as pdf:
        all_words = []
        for p_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            for w in words:
                w['page'] = p_idx + 1
            all_words.extend(words)

    # Filter out header and footer
    # Header has CNPJ, AVENIDA, Documento Auxiliar, Código Descrição Qtd...
    # Footer has "Qtde. total de itens", "Valor itens", etc.
    
    # Let's find all item starting words: x0 < 30 and text is digits
    items = []
    
    # We can group words into blocks
    # An item starts with a word whose text is digits and x0 < 25 (around 17.6)
    # Stop when we see "Qtde." or page 4
    
    # First find index of "Qtde." or "Qtde"
    footer_idx = len(all_words)
    for i, w in enumerate(all_words):
        if "Qtde" in w['text'] or "total de itens" in w['text']:
            footer_idx = i
            break

    item_starts = []
    for i in range(footer_idx):
        w = all_words[i]
        if w['page'] <= 3 and w['x0'] < 25 and w['text'].isdigit() and len(w['text']) >= 4:
            item_starts.append(i)

    print(f"Found {len(item_starts)} item start markers.")
    
    parsed_items = []
    for idx_pos, start_idx in enumerate(item_starts):
        end_idx = item_starts[idx_pos + 1] if idx_pos + 1 < len(item_starts) else len(all_words)
        item_words = all_words[start_idx:end_idx]
        
        # Stop item words if "Qtde." is encountered
        clean_words = []
        for w in item_words:
            if "Qtde" in w['text']:
                break
            clean_words.append(w)
        item_words = clean_words

        code = item_words[0]['text']
        
        # Find quantity: word with x0 between 145 and 160 on roughly the same top as code
        code_top = item_words[0]['top']
        code_page = item_words[0]['page']
        
        line1_words = [w for w in item_words if w['page'] == code_page and abs(w['top'] - code_top) < 3]
        
        # Quantity
        qtd = 1
        qtd_words = [w for w in line1_words if 146 <= w['x0'] <= 165 and w['text'].isdigit()]
        if qtd_words:
            qtd = int(qtd_words[0]['text'])
            
        # Vl Total (last word in line 1, x0 >= 195)
        vl_tot_words = [w for w in line1_words if w['x0'] >= 195]
        vl_total = 0.0
        if vl_tot_words:
            vl_total = float(vl_tot_words[-1]['text'].replace('.', '').replace(',', '.'))
            
        # Vl Unit: between 165 and 195 in line 1, might wrap
        # Let's find words around 165-195
        vl_unit_parts = [w['text'] for w in line1_words if 165 <= w['x0'] < 195]
        
        # Desconto: find word "Desconto" and the word next to it with '-'
        desc_val = 0.0
        for i, w in enumerate(item_words):
            if "Desconto" in w['text']:
                # search following words for '-'
                for next_w in item_words[i+1:i+4]:
                    if '-' in next_w['text']:
                        desc_str = next_w['text'].replace('-', '').replace('.', '').replace(',', '.')
                        desc_val = -float(desc_str)
                        break
                break

        # Description words: words with 40 <= x0 < 146 that don't belong to 'Desconto' line
        desc_words = []
        unit = "UN"
        for w in item_words:
            if "Desconto" in w['text']:
                continue
            # if line has 'Desconto', ignore
            # if x0 between 40 and 146
            if 40 <= w['x0'] < 146:
                desc_words.append(w['text'])
            elif 170 <= w['x0'] <= 190 and w['text'] in ['PC', 'UNI', 'UN']:
                unit = w['text']

        full_desc = " ".join(desc_words)
        
        # Vl Unit calculated accurately: vl_total / qtd
        vl_unit = round(vl_total / qtd, 2)
        
        # Valor Pago: vl_total + desc_val (since desc_val is negative)
        vl_pago = round(vl_total + desc_val, 2)
        vl_pago_unit = round(vl_pago / qtd, 2)
        
        parsed_items.append({
            "codigo": code,
            "descricao": full_desc,
            "unidade": unit,
            "quantidade": qtd,
            "vl_unit_sugerido": vl_unit,
            "vl_total_sugerido": vl_total,
            "desconto_total": desc_val,
            "desconto_unit": round(desc_val / qtd, 2),
            "vl_total_pago": vl_pago,
            "vl_unit_pago": vl_pago_unit,
        })
        
    return parsed_items

if __name__ == "__main__":
    items = parse_items()
    for i, it in enumerate(items):
        print(f"{i+1}: cod={it['codigo']} | qtd={it['quantidade']} | total={it['vl_total_sugerido']} | desc={it['desconto_total']} | descr={it['descricao']}")
    print(f"Total parsed: {len(items)}")
    tot_itens_val = sum(it['vl_total_sugerido'] for it in items)
    tot_desc_val = sum(it['desconto_total'] for it in items)
    tot_pago_val = sum(it['vl_total_pago'] for it in items)
    tot_qtd = sum(it['quantidade'] for it in items)

    print(f"Qtde total itens: {tot_qtd}")
    print(f"Valor itens: R$ {tot_itens_val:.2f}")
    print(f"Desconto: R$ {tot_desc_val:.2f}")
    print(f"Valor pago: R$ {tot_pago_val:.2f}")

