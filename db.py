import sqlite3
import os
import json
from parse_nf import parse_items
import supabase_client

DB_PATH = "vendas_natura.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def categorize_product(desc):
    desc_upper = desc.upper()
    if "SAB" in desc_upper or "SABONETE" in desc_upper:
        if "MMBB" in desc_upper:
            return "Mamãe e Bebê"
        if "LIQ" in desc_upper:
            return "Sabonete Líquido"
        return "Sabonetes"
    elif "DEO PARFUM" in desc_upper or "PARFU" in desc_upper or "DES COL" in desc_upper or "COLONIA" in desc_upper:
        if "NATURE" in desc_upper:
            return "Infantil"
        elif "MASC" in desc_upper or "KAIAK" in desc_upper or "KMAX" in desc_upper:
            return "Perfumaria Masculina"
        elif "FEM" in desc_upper or "LUNA" in desc_upper:
            return "Perfumaria Feminina"
        return "Perfumaria"
    elif "MAOS" in desc_upper:
        return "Cuidados para Mãos"
    elif "OLEO" in desc_upper:
        return "Óleos Corporais"
    elif "COND" in desc_upper or "SHAMP" in desc_upper or "LUMINA" in desc_upper:
        return "Cabelos"
    elif "ROLLON" in desc_upper or "SPRAY" in desc_upper:
        return "Desodorantes"
    elif "HID" in desc_upper or "HIDRA" in desc_upper:
        if "MMBB" in desc_upper:
            return "Mamãe e Bebê"
        return "Hidratantes Corporais"
    elif "MMBB" in desc_upper:
        return "Mamãe e Bebê"
    return "Outros"

def init_db(force_reseed=False):
    """Inicializa banco local como fallback e verifica tabelas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        categoria TEXT NOT NULL,
        unidade TEXT DEFAULT 'UN',
        quantidade_comprada INTEGER NOT NULL,
        quantidade_estoque INTEGER NOT NULL,
        quantidade_vendida INTEGER DEFAULT 0,
        vl_unit_sugerido REAL NOT NULL,
        desconto_compra_unit REAL NOT NULL,
        vl_unit_pago REAL NOT NULL,
        desconto_repassado_unit REAL DEFAULT 0.0,
        vl_unit_venda_sugerida_final REAL NOT NULL,
        preco_revista REAL DEFAULT 0.0,
        preco_revista_promo REAL,
        pagina_revista INTEGER,
        nome_revista TEXT,
        data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
        origem TEXT DEFAULT 'Nota Fiscal 05/11/2026',
        observacoes TEXT DEFAULT ''
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        email TEXT,
        data_nascimento TEXT,
        observacoes TEXT DEFAULT '',
        data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER,
        codigo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        vl_unit_pago REAL NOT NULL,
        vl_unit_venda REAL NOT NULL,
        desconto_repassado_unit REAL DEFAULT 0.0,
        vl_total_venda REAL NOT NULL,
        lucro_total REAL NOT NULL,
        cliente_id INTEGER,
        cliente TEXT DEFAULT 'Consumidor',
        cliente_telefone TEXT,
        cliente_email TEXT,
        cliente_nascimento TEXT,
        forma_pagamento TEXT DEFAULT 'Pix',
        status_pagamento TEXT DEFAULT 'Recebido',
        data_venda TEXT NOT NULL,
        observacoes TEXT DEFAULT '',
        FOREIGN KEY(produto_id) REFERENCES produtos(id),
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    """)
    conn.commit()
    conn.close()

def get_produtos():
    """Busca produtos diretamente do Supabase (com fallback local se offline)."""
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            res = sb.table("produtos").select("*").order("id").execute()
            if res.data:
                # Converter tipos numéricos para float
                for r in res.data:
                    for k in ['vl_unit_sugerido', 'desconto_compra_unit', 'vl_unit_pago', 'desconto_repassado_unit', 'vl_unit_venda_sugerida_final', 'preco_revista', 'preco_revista_promo']:
                        if r.get(k) is not None:
                            r[k] = float(r[k])
                return res.data
        except Exception as e:
            print("Aviso: Falha ao consultar Supabase, usando local:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_vendas():
    """Busca vendas diretamente do Supabase."""
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            res = sb.table("vendas").select("*").order("id", desc=True).execute()
            if res.data is not None:
                for r in res.data:
                    for k in ['vl_unit_pago', 'vl_unit_venda', 'desconto_repassado_unit', 'vl_total_venda', 'lucro_total']:
                        if r.get(k) is not None:
                            r[k] = float(r[k])
                return res.data
        except Exception as e:
            print("Aviso: Falha ao consultar vendas no Supabase:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendas ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_clientes():
    """Busca clientes do Supabase com cálculos de compras e total gasto."""
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            res_c = sb.table("clientes").select("*").order("nome").execute()
            res_v = sb.table("vendas").select("id, cliente_id, cliente, vl_total_venda, data_venda").execute()
            
            clientes = res_c.data or []
            vendas = res_v.data or []
            
            for c in clientes:
                c_vendas = [v for v in vendas if v.get('cliente_id') == c['id'] or (v.get('cliente') and v['cliente'].strip().lower() == c['nome'].strip().lower())]
                c['total_compras'] = len(c_vendas)
                c['valor_total_gasto'] = float(sum(float(v.get('vl_total_venda') or 0.0) for v in c_vendas))
                datas = [v['data_venda'] for v in c_vendas if v.get('data_venda')]
                c['ultima_compra'] = max(datas) if datas else None
            return clientes
        except Exception as e:
            print("Aviso: Falha ao consultar clientes no Supabase:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, 
           COUNT(v.id) as total_compras, 
           COALESCE(SUM(v.vl_total_venda), 0.0) as valor_total_gasto,
           MAX(v.data_venda) as ultima_compra
    FROM clientes c
    LEFT JOIN vendas v ON c.id = v.cliente_id OR (c.nome = v.cliente AND v.cliente_id IS NULL)
    GROUP BY c.id
    ORDER BY c.nome ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_cliente(nome, telefone="", email="", data_nascimento="", observacoes=""):
    """Adiciona cliente no Supabase e no banco local."""
    c_id = None
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            nasc_val = data_nascimento if data_nascimento and str(data_nascimento).strip() else None
            c_data = {
                "nome": nome.strip(),
                "telefone": telefone.strip(),
                "email": email.strip(),
                "data_nascimento": nasc_val,
                "observacoes": observacoes.strip()
            }
            res = sb.table("clientes").insert(c_data).execute()
            if res.data:
                c_id = res.data[0]['id']
        except Exception as e:
            print("Erro ao adicionar cliente no Supabase:", e)
            
    # Salvar também no local
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO clientes (nome, telefone, email, data_nascimento, observacoes)
    VALUES (?, ?, ?, ?, ?)
    """, (nome, telefone, email, data_nascimento, observacoes))
    conn.commit()
    local_id = cursor.lastrowid
    conn.close()
    return c_id or local_id

def update_cliente(cliente_id, updates):
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            sb.table("clientes").update(updates).eq("id", cliente_id).execute()
        except Exception as e:
            print("Erro ao atualizar cliente no Supabase:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    fields = [f"{k} = ?" for k in updates.keys()]
    values = list(updates.values()) + [cliente_id]
    cursor.execute(f"UPDATE clientes SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_cliente(cliente_id):
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            sb.table("clientes").delete().eq("id", cliente_id).execute()
        except Exception as e:
            print("Erro ao excluir cliente no Supabase:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()

def add_produto(codigo, descricao, categoria, unidade, qtd, vl_sugerido, vl_pago, desconto_compra=0.0, desconto_repassado=0.0, vl_venda=None, observacoes=""):
    if vl_venda is None:
        vl_venda = vl_sugerido - desconto_repassado
        
    p_id = None
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            p_data = {
                "codigo": codigo,
                "descricao": descricao,
                "categoria": categoria,
                "unidade": unidade,
                "quantidade_comprada": qtd,
                "quantidade_estoque": qtd,
                "quantidade_vendida": 0,
                "vl_unit_sugerido": vl_sugerido,
                "desconto_compra_unit": desconto_compra,
                "vl_unit_pago": vl_pago,
                "desconto_repassado_unit": desconto_repassado,
                "vl_unit_venda_sugerida_final": vl_venda,
                "preco_revista": vl_sugerido,
                "origem": "Cadastro Manual",
                "observacoes": observacoes
            }
            res = sb.table("produtos").insert(p_data).execute()
            if res.data:
                p_id = res.data[0]['id']
        except Exception as e:
            print("Erro ao adicionar produto no Supabase:", e)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO produtos (
        codigo, descricao, categoria, unidade,
        quantidade_comprada, quantidade_estoque, quantidade_vendida,
        vl_unit_sugerido, desconto_compra_unit, vl_unit_pago,
        desconto_repassado_unit, vl_unit_venda_sugerida_final,
        preco_revista, origem, observacoes
    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 'Cadastro Manual', ?)
    """, (
        codigo, descricao, categoria, unidade,
        qtd, qtd, vl_sugerido, desconto_compra, vl_pago,
        desconto_repassado, vl_venda, vl_sugerido, observacoes
    ))
    conn.commit()
    local_id = cursor.lastrowid
    conn.close()
    return p_id or local_id

def update_produto(prod_id, updates):
    """Atualiza dados do produto no Supabase e no local."""
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            sb.table("produtos").update(updates).eq("id", prod_id).execute()
        except Exception as e:
            print("Erro ao atualizar produto no Supabase:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    fields = [f"{k} = ?" for k in updates.keys()]
    values = list(updates.values()) + [prod_id]
    cursor.execute(f"UPDATE produtos SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_produto(prod_id):
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            sb.table("produtos").delete().eq("id", prod_id).execute()
        except Exception as e:
            print("Erro ao excluir produto no Supabase:", e)
            
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()

def registrar_venda(produto_id, qtd_venda, vl_unit_venda, desconto_repassado_unit, cliente, forma_pagamento, status_pagamento, data_venda, observacoes="", cliente_id=None, cliente_telefone="", cliente_email="", cliente_nascimento=""):
    """Registra venda diretamente no Supabase em tempo real com baixa de estoque e dados do cliente."""
    
    # 1. Obter produto
    prods = get_produtos()
    prod = next((p for p in prods if str(p['id']) == str(produto_id)), None)
    if not prod:
        raise ValueError("Produto não encontrado.")
    
    if qtd_venda > prod['quantidade_estoque']:
        raise ValueError(f"Quantidade insuficiente em estoque. Disponível: {prod['quantidade_estoque']}")
    
    vl_unit_pago = float(prod['vl_unit_pago'])
    vl_total_venda = round(qtd_venda * vl_unit_venda, 2)
    custo_total = round(qtd_venda * vl_unit_pago, 2)
    lucro_total = round(vl_total_venda - custo_total, 2)
    
    # 2. Se cliente não tem ID e nome foi informado, verificar ou cadastrar
    if not cliente_id and cliente and cliente.strip() and cliente.strip().lower() != "consumidor":
        clientes = get_clientes()
        existente = next((c for c in clientes if c['nome'].strip().lower() == cliente.strip().lower()), None)
        if existente:
            cliente_id = existente['id']
        else:
            cliente_id = add_cliente(
                nome=cliente.strip(),
                telefone=cliente_telefone,
                email=cliente_email,
                data_nascimento=cliente_nascimento,
                observacoes="Cadastrado na venda"
            )

    # 3. Inserir no Supabase
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            nasc_val = cliente_nascimento if cliente_nascimento and str(cliente_nascimento).strip() else None
            venda_data = {
                "produto_id": produto_id,
                "codigo": prod['codigo'],
                "descricao": prod['descricao'],
                "quantidade": qtd_venda,
                "vl_unit_pago": vl_unit_pago,
                "vl_unit_venda": vl_unit_venda,
                "desconto_repassado_unit": desconto_repassado_unit,
                "vl_total_venda": vl_total_venda,
                "lucro_total": lucro_total,
                "cliente_id": cliente_id,
                "cliente": cliente,
                "cliente_telefone": cliente_telefone or "",
                "cliente_email": cliente_email or "",
                "cliente_nascimento": nasc_val,
                "forma_pagamento": forma_pagamento,
                "status_pagamento": status_pagamento,
                "data_venda": data_venda,
                "observacoes": observacoes or ""
            }
            sb.table("vendas").insert(venda_data).execute()
            
            # Baixar estoque no Supabase
            novo_est = prod['quantidade_estoque'] - qtd_venda
            novo_vend = prod['quantidade_vendida'] + qtd_venda
            sb.table("produtos").update({
                "quantidade_estoque": novo_est,
                "quantidade_vendida": novo_vend
            }).eq("id", produto_id).execute()
            
        except Exception as e:
            print("Erro ao registrar venda no Supabase:", e)
            raise e

    # 4. Salvar também no local
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO vendas (
        produto_id, codigo, descricao, quantidade,
        vl_unit_pago, vl_unit_venda, desconto_repassado_unit,
        vl_total_venda, lucro_total, cliente_id, cliente,
        cliente_telefone, cliente_email, cliente_nascimento,
        forma_pagamento, status_pagamento, data_venda, observacoes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        produto_id, prod['codigo'], prod['descricao'], qtd_venda,
        vl_unit_pago, vl_unit_venda, desconto_repassado_unit,
        vl_total_venda, lucro_total, cliente_id, cliente,
        cliente_telefone, cliente_email, cliente_nascimento,
        forma_pagamento, status_pagamento, data_venda, observacoes
    ))
    cursor.execute("""
    UPDATE produtos SET
        quantidade_estoque = quantidade_estoque - ?,
        quantidade_vendida = quantidade_vendida + ?
    WHERE id = ?
    """, (qtd_venda, qtd_venda, produto_id))
    conn.commit()
    conn.close()
    
    return True

def cancelar_venda(venda_id):
    """Estorna venda no Supabase e no banco local."""
    vendas = get_vendas()
    venda = next((v for v in vendas if str(v['id']) == str(venda_id)), None)
    if not venda:
        raise ValueError("Venda não encontrada.")
        
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            if venda.get('produto_id'):
                # Devolver estoque
                prods = get_produtos()
                prod = next((p for p in prods if p['id'] == venda['produto_id']), None)
                if prod:
                    sb.table("produtos").update({
                        "quantidade_estoque": prod['quantidade_estoque'] + venda['quantidade'],
                        "quantidade_vendida": max(0, prod['quantidade_vendida'] - venda['quantidade'])
                    }).eq("id", venda['produto_id']).execute()
            sb.table("vendas").delete().eq("id", venda_id).execute()
        except Exception as e:
            print("Erro ao cancelar venda no Supabase:", e)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE produtos SET
        quantidade_estoque = quantidade_estoque + ?,
        quantidade_vendida = quantidade_vendida - ?
    WHERE id = ?
    """, (venda['quantidade'], venda['quantidade'], venda['produto_id']))
    cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
    conn.commit()
    conn.close()
    return True
