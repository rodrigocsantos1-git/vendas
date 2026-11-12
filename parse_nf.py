import pdfplumber
import re
import io
import json
from datetime import date

def _open_pdf(pdf_source):
    if isinstance(pdf_source, (bytes, bytearray)):
        return pdfplumber.open(io.BytesIO(pdf_source))
    return pdfplumber.open(pdf_source)

def extract_nf_metadata(pdf_source="Nota_fiscal_05_11_2026.pdf"):
    """Extrai data de emissão e número da NFC-e / Nota Fiscal a partir do PDF."""
    data_nf_iso = date.today().isoformat()
    data_nf_br = date.today().strftime("%d/%m/%Y")
    numero_nf = ""

    try:
        with _open_pdf(pdf_source) as pdf:
            full_text = "\n".join((p.extract_text() or "") for p in pdf.pages)

        # Procurar padrão NFC-e nº 000044852 Série 3 05/11/2026
        m_nfce = re.search(r'NFC-e\s*n[º°o]?\s*(\d+).*?(\d{2}/\d{2}/\d{4})', full_text, re.IGNORECASE | re.DOTALL)
        if m_nfce:
            numero_nf = str(int(m_nfce.group(1)))
            data_nf_br = m_nfce.group(2)
        else:
            m_data = re.search(r'(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}:\d{2}', full_text)
            if not m_data:
                m_data = re.search(r'Data\s+de\s+autoriza[çc][ãa]o:\s*(\d{2}/\d{2}/\d{4})', full_text, re.IGNORECASE)
            if m_data:
                data_nf_br = m_data.group(1)

        parts = data_nf_br.split("/")
        if len(parts) == 3:
            data_nf_iso = f"{parts[2]}-{parts[1]}-{parts[0]}"
    except Exception as e:
        print("Aviso ao extrair metadados da NF:", e)

    origem_label = f"Nota Fiscal {data_nf_br}" + (f" (Nº {numero_nf})" if numero_nf else "")
    return {
        "data_nf_iso": data_nf_iso,
        "data_nf_br": data_nf_br,
        "numero_nf": numero_nf,
        "origem": origem_label
    }

def parse_items(pdf_source="Nota_fiscal_05_11_2026.pdf"):
    with _open_pdf(pdf_source) as pdf:
        all_words = []
        for p_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            for w in words:
                w['page'] = p_idx + 1
            all_words.extend(words)

    # Localizar onde começa o rodapé ("Qtde. total de itens" / "Valor itens")
    footer_idx = len(all_words)
    for i, w in enumerate(all_words):
        if "Qtde" in w['text'] or "total de itens" in w['text']:
            footer_idx = i
            break

    # Localizar início dos itens (após cabeçalho "Código", x0 < 25 e numérico >= 3 dígitos)
    header_end_idx = 0
    for i in range(min(60, footer_idx)):
        if all_words[i]['text'] in ('Código', 'Codigo', 'Total', 'Unit'):
            header_end_idx = i + 1

    item_starts = []
    for i in range(header_end_idx, footer_idx):
        w = all_words[i]
        if w['x0'] < 25 and w['text'].isdigit() and len(w['text']) >= 3:
            item_starts.append(i)

    parsed_items = []
    for idx_pos, start_idx in enumerate(item_starts):
        end_idx = item_starts[idx_pos + 1] if idx_pos + 1 < len(item_starts) else footer_idx
        item_words = all_words[start_idx:end_idx]

        clean_words = []
        for w in item_words:
            if "Qtde" in w['text']:
                break
            clean_words.append(w)
        item_words = clean_words
        if not item_words:
            continue

        code = item_words[0]['text'].strip()
        code_top = item_words[0]['top']
        code_page = item_words[0]['page']

        line1_words = [w for w in item_words if w['page'] == code_page and abs(w['top'] - code_top) < 3.5]

        # Quantidade (x0 entre 145 e 165)
        qtd = 1
        qtd_words = [w for w in line1_words if 145 <= w['x0'] <= 165 and w['text'].isdigit()]
        if qtd_words:
            qtd = int(qtd_words[0]['text'])

        # Vl Total (última palavra da linha 1, x0 >= 195)
        vl_tot_words = [w for w in line1_words if w['x0'] >= 195]
        vl_total = 0.0
        if vl_tot_words:
            try:
                vl_total = float(vl_tot_words[-1]['text'].replace('.', '').replace(',', '.'))
            except:
                vl_total = 0.0

        # Desconto: procurar palavra "Desconto" e o valor negativo logo a seguir
        desc_val = 0.0
        for i, w in enumerate(item_words):
            if "Desconto" in w['text']:
                for next_w in item_words[i+1:i+5]:
                    if '-' in next_w['text'] or re.match(r'^\d+[,\.]\d{2}$', next_w['text']):
                        desc_str = next_w['text'].replace('-', '').replace('.', '').replace(',', '.').strip()
                        try:
                            desc_val = -abs(float(desc_str))
                            break
                        except:
                            pass
                break

        # Palavras da descrição: 40 <= x0 < 146 (ignorando linha de Desconto)
        desc_words = []
        unit = "UN"
        for w in item_words:
            if "Desconto" in w['text']:
                continue
            if 40 <= w['x0'] < 146:
                desc_words.append(w['text'])
            elif 145 <= w['x0'] <= 192 and w['text'].upper() in ['PC', 'UNI', 'UN', 'CX', 'KIT']:
                unit = w['text'].upper()

        full_desc = " ".join(desc_words).strip()

        vl_unit = round(vl_total / qtd, 2) if qtd > 0 else 0.0
        vl_pago = round(vl_total + desc_val, 2)
        vl_pago_unit = round(vl_pago / qtd, 2) if qtd > 0 else 0.0
        desconto_unit = round(abs(desc_val) / qtd, 2) if qtd > 0 else 0.0

        parsed_items.append({
            "codigo": code,
            "descricao": full_desc,
            "unidade": unit,
            "quantidade": qtd,
            "vl_unit_sugerido": vl_unit,
            "vl_total_sugerido": vl_total,
            "desconto_total": desc_val,
            "desconto_unit": -desconto_unit,
            "desconto_compra_unit": desconto_unit,
            "vl_total_pago": vl_pago,
            "vl_unit_pago": vl_pago_unit,
        })

    return parsed_items

def group_items_by_sku(parsed_items):
    """Agrupa itens do mesmo SKU dentro do PDF somando suas quantidades."""
    grouped = {}
    for it in parsed_items:
        cod = str(it["codigo"]).strip()
        if cod not in grouped:
            grouped[cod] = dict(it)
        else:
            grouped[cod]["quantidade"] += int(it["quantidade"])
            grouped[cod]["vl_total_sugerido"] = round(grouped[cod]["vl_total_sugerido"] + it["vl_total_sugerido"], 2)
            grouped[cod]["desconto_total"] = round(grouped[cod]["desconto_total"] + it["desconto_total"], 2)
            grouped[cod]["vl_total_pago"] = round(grouped[cod]["vl_total_pago"] + it["vl_total_pago"], 2)
    return list(grouped.values())

if __name__ == "__main__":
    meta = extract_nf_metadata()
    print("Metadata:", meta)
    items = parse_items()
    for i, it in enumerate(items):
        print(f"{i+1}: cod={it['codigo']} | qtd={it['quantidade']} | total={it['vl_total_sugerido']} | desc={it['desconto_total']} | descr={it['descricao']}")
    print(f"Total parsed: {len(items)} lines ({len(group_items_by_sku(items))} unique SKUs)")
    tot_itens_val = sum(it['vl_total_sugerido'] for it in items)
    tot_desc_val = sum(it['desconto_total'] for it in items)
    tot_pago_val = sum(it['vl_total_pago'] for it in items)
    tot_qtd = sum(it['quantidade'] for it in items)

    print(f"Qtde total unidades: {tot_qtd}")
    print(f"Valor itens: R$ {tot_itens_val:.2f}")
    print(f"Desconto: R$ {tot_desc_val:.2f}")
    print(f"Valor pago: R$ {tot_pago_val:.2f}")
