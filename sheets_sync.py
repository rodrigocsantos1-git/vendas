import urllib.request
import ssl
import json
import pandas as pd
import io
import os
import requests
import db

SHEET_ID = "1V84XN7tx2jicDcC4YDrMPwBrJFaa-a7z7dkFoCgDoNE"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
XLSX_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
CONFIG_FILE = "config_sheets.json"

def get_webhook_url():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("webhook_url", "")
        except:
            return ""
    return ""

def set_webhook_url(url):
    cfg = {"webhook_url": url.strip()}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def testar_conexao_webhook():
    """Testa se o Webhook está respondendo sem erro 401."""
    webhook_url = get_webhook_url()
    if not webhook_url:
        return False, "Nenhuma URL de Webhook configurada."
    try:
        resp = requests.post(webhook_url, json={"tipo": "teste"}, timeout=10)
        if resp.status_code == 401:
            return False, "Erro 401 (Não Autorizado): no Apps Script, a opção 'Quem pode acessar' precisa ser alterada para 'Qualquer pessoa'."
        elif resp.status_code == 200:
            return True, "Conexão com Google Sheets ativa e funcionando perfeitamente!"
        else:
            return False, f"Resposta inesperada do Google: Código {resp.status_code}"
    except Exception as e:
        return False, f"Falha de conexão: {str(e)}"

def enviar_venda_para_google_sheets(venda_dict):
    """Envia uma venda em tempo real para a planilha do Google Sheets via Webhook."""
    webhook_url = get_webhook_url()
    if not webhook_url:
        return False, "Nenhum Webhook configurado."
    
    payload = dict(venda_dict)
    payload["tipo"] = "venda"
    
    try:
        resp = requests.post(webhook_url, json=payload, timeout=12)
        if resp.status_code == 200:
            return True, "Venda gravada com sucesso direto no Google Sheets!"
        elif resp.status_code == 401:
            return False, "Erro 401: Altere 'Quem pode acessar' para 'Qualquer pessoa' na implantação do Apps Script."
        else:
            return False, f"Erro {resp.status_code} ao enviar para o Google Sheets."
    except Exception as e:
        return False, f"Falha ao enviar para o Google Sheets: {str(e)}"

def enviar_cliente_para_google_sheets(cliente_dict):
    """Envia um cliente em tempo real para a planilha do Google Sheets."""
    webhook_url = get_webhook_url()
    if not webhook_url:
        return False, "Nenhum Webhook configurado."
        
    payload = dict(cliente_dict)
    payload["tipo"] = "cliente"
    
    try:
        resp = requests.post(webhook_url, json=payload, timeout=12)
        if resp.status_code == 200:
            return True, "Cliente gravado com sucesso no Google Sheets!"
        else:
            return False, f"Erro {resp.status_code}"
    except Exception as e:
        return False, str(e)

def enviar_dados_pendentes():
    """Envia todas as vendas e clientes cadastrados localmente para o Google Sheets."""
    webhook_url = get_webhook_url()
    if not webhook_url:
        return False, "Configure a URL do Webhook primeiro."
        
    vendas = db.get_vendas()
    clientes = db.get_clientes()
    
    sucessos_v = 0
    sucessos_c = 0
    
    for v in vendas:
        ok, _ = enviar_venda_para_google_sheets(v)
        if ok:
            sucessos_v += 1
            
    for c in clientes:
        ok, _ = enviar_cliente_para_google_sheets(c)
        if ok:
            sucessos_c += 1
            
    return True, f"{sucessos_v} venda(s) e {sucessos_c} cliente(s) enviados para o Google Sheets!"

def check_google_sheet_status():
    """Verifica se a planilha do Google está acessível e se possui dados."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(XLSX_URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False, "Planilha vazia ou inacessível", None
            
            excel_file = pd.ExcelFile(io.BytesIO(data))
            sheet_names = excel_file.sheet_names
            
            target_sheet = 'Estoque_Produtos' if 'Estoque_Produtos' in sheet_names else sheet_names[0]
            df = excel_file.parse(target_sheet)
            
            if df.empty or len(df.columns) <= 1:
                return True, "Planilha conectada, porém está vazia.", 0
            
            return True, f"Conectada com sucesso! ({len(df)} produtos encontrados)", len(df)
    except Exception as e:
        return False, f"Erro ao conectar com Google Sheets: {str(e)}", None

def sync_from_google_sheet():
    """Baixa os dados do Google Sheets e atualiza o banco de dados da aplicação."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(XLSX_URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = resp.read()
            excel_file = pd.ExcelFile(io.BytesIO(data))
            sheet_names = excel_file.sheet_names
            
            target_sheet = 'Estoque_Produtos' if 'Estoque_Produtos' in sheet_names else sheet_names[0]
            df_prods = excel_file.parse(target_sheet)
            
            if df_prods.empty or len(df_prods) == 0:
                return False, "A planilha do Google não possui linhas de produtos para importar."
            
            col_map = {}
            for col in df_prods.columns:
                c_clean = str(col).strip().lower()
                if 'código' in c_clean or 'codigo' in c_clean:
                    col_map['codigo'] = col
                elif 'produto' in c_clean or 'descri' in c_clean:
                    col_map['descricao'] = col
                elif 'categoria' in c_clean:
                    col_map['categoria'] = col
                elif 'unidade' in c_clean:
                    col_map['unidade'] = col
                elif 'estoque' in c_clean:
                    col_map['quantidade_estoque'] = col
                elif 'comprada' in c_clean:
                    col_map['quantidade_comprada'] = col
                elif 'paguei' in c_clean or 'custo' in c_clean:
                    col_map['vl_unit_pago'] = col
                elif 'revista' in c_clean or 'catálogo' in c_clean or 'catalogo' in c_clean:
                    col_map['preco_revista'] = col
                elif 'repassar' in c_clean:
                    col_map['desconto_repassado_unit'] = col
                elif 'praticado' in c_clean or 'venda' in c_clean:
                    col_map['vl_unit_venda_sugerida_final'] = col
            
            if 'codigo' not in col_map or 'descricao' not in col_map:
                return False, "Colunas mínimas necessárias ('Código' e 'Produto') não foram identificadas na planilha."
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            imported_count = 0
            for _, row in df_prods.iterrows():
                cod = str(row[col_map['codigo']]).strip()
                desc = str(row[col_map['descricao']]).strip()
                cat = str(row.get(col_map.get('categoria', ''), 'Outros')).strip()
                qtd_est = int(row.get(col_map.get('quantidade_estoque', 1), 1))
                vl_pago = float(row.get(col_map.get('vl_unit_pago', 0.0), 0.0))
                p_revista = float(row.get(col_map.get('preco_revista', 0.0), 0.0))
                desc_rep = float(row.get(col_map.get('desconto_repassado_unit', 0.0), 0.0))
                vl_venda = float(row.get(col_map.get('vl_unit_venda_sugerida_final', p_revista - desc_rep), p_revista - desc_rep))
                
                cursor.execute("SELECT id FROM produtos WHERE codigo = ?", (cod,))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                    UPDATE produtos SET
                        descricao = ?, categoria = ?, quantidade_estoque = ?,
                        vl_unit_pago = ?, preco_revista = ?, desconto_repassado_unit = ?,
                        vl_unit_venda_sugerida_final = ?
                    WHERE id = ?
                    """, (desc, cat, qtd_est, vl_pago, p_revista, desc_rep, vl_venda, existing['id']))
                else:
                    cursor.execute("""
                    INSERT INTO produtos (
                        codigo, descricao, categoria, quantidade_comprada, quantidade_estoque,
                        quantidade_vendida, vl_unit_sugerido, desconto_compra_unit,
                        vl_unit_pago, preco_revista, desconto_repassado_unit,
                        vl_unit_venda_sugerida_final, origem
                    ) VALUES (?, ?, ?, ?, ?, 0, ?, 0.0, ?, ?, ?, ?, 'Google Sheets')
                    """, (cod, desc, cat, qtd_est, qtd_est, p_revista, vl_pago, p_revista, desc_rep, vl_venda))
                imported_count += 1
                
            conn.commit()
            conn.close()
            return True, f"{imported_count} produtos sincronizados com sucesso a partir do Google Sheets!"
    except Exception as e:
        return False, f"Falha na sincronização: {str(e)}"
