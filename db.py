import sqlite3
import os
import json
import hashlib
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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        senha_hash TEXT NOT NULL,
        perfil TEXT DEFAULT 'admin',
        ativo INTEGER DEFAULT 1,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
        ultimo_login TEXT
    )
    """)
    
    # Inserir usuários padrão caso não existam
    cursor.execute("SELECT COUNT(*) as c FROM usuarios")
    if cursor.fetchone()['c'] == 0:
        cursor.execute("""
        INSERT INTO usuarios (email, nome, senha_hash, perfil, ativo) VALUES
        ('rodrigo.correa01@outlook.com', 'Rodrigo Corrêa', 'alterar123', 'admin', 1),
        ('daniele_barreto@hotmail.com', 'Daniele Barreto', 'alterar123', 'admin', 1)
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

def hash_senha(senha):
    """Gera hash SHA-256 para senhas."""
    return hashlib.sha256(senha.strip().encode('utf-8')).hexdigest()

def autenticar_usuario(email, senha):
    """
    Autentica usuário comparando com Supabase (ou banco local se offline).
    Aceita senha tanto em texto puro quanto hash SHA-256 no banco.
    """
    email_limpo = email.strip().lower()
    senha_limpa = senha.strip()
    senha_sha256 = hash_senha(senha_limpa)

    # 1. Tentar Supabase
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            res = sb.table("usuarios").select("*").eq("email", email_limpo).eq("ativo", True).execute()
            if res.data and len(res.data) > 0:
                user = res.data[0]
                db_hash = str(user.get("senha_hash", ""))
                # Compara tanto com texto direto quanto com sha256
                if db_hash == senha_limpa or db_hash == senha_sha256:
                    # Atualiza último login
                    try:
                        from datetime import datetime
                        sb.table("usuarios").update({"ultimo_login": datetime.now().isoformat()}).eq("id", user["id"]).execute()
                    except:
                        pass
                    return {"sucesso": True, "usuario": user}
                else:
                    return {"sucesso": False, "mensagem": "Senha incorreta."}
        except Exception as e:
            print("Aviso ao autenticar no Supabase, tentando local:", e)

    # 2. Fallback SQLite local
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE LOWER(email) = ? AND ativo = 1", (email_limpo,))
    row = cursor.fetchone()
    conn.close()

    if row:
        user = dict(row)
        db_hash = str(user.get("senha_hash", ""))
        if db_hash == senha_limpa or db_hash == senha_sha256:
            return {"sucesso": True, "usuario": user}
        return {"sucesso": False, "mensagem": "Senha incorreta."}

    return {"sucesso": False, "mensagem": "Usuário não encontrado ou inativo."}

def alterar_senha_usuario(email, nova_senha):
    """Atualiza a senha do usuário no Supabase e no banco local."""
    email_limpo = email.strip().lower()
    senha_limpa = nova_senha.strip()

    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            sb.table("usuarios").update({"senha_hash": senha_limpa}).eq("email", email_limpo).execute()
        except Exception as e:
            print("Erro ao atualizar senha no Supabase:", e)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE LOWER(email) = ?", (senha_limpa, email_limpo))
    conn.commit()
    conn.close()
    return True

def verificar_nf_ja_importada(metadata):
    """
    Verifica se uma Nota Fiscal já foi importada anteriormente:
    Checa pela chave de acesso (44 dígitos), protocolo ou número de NFC-e + data.
    """
    chave = metadata.get('chave_acesso')
    identificador = metadata.get('identificador_unico')
    numero_nf = metadata.get('numero_nf')
    data_br = metadata.get('data_nf_br')

    # 1. Checa tabela local de notas fiscais
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas_fiscais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificador_unico TEXT UNIQUE NOT NULL,
        chave_acesso TEXT,
        numero_nf TEXT,
        serie TEXT,
        protocolo TEXT,
        data_emissao TEXT,
        valor_total REAL,
        total_itens INTEGER,
        total_unidades INTEGER,
        data_importacao TEXT DEFAULT CURRENT_TIMESTAMP,
        origem TEXT
    )
    """)
    conn.commit()

    if chave:
        cursor.execute("SELECT * FROM notas_fiscais WHERE chave_acesso = ?", (chave,))
        if cursor.fetchone():
            conn.close()
            return True, f"A Nota Fiscal com chave de acesso '{chave}' já foi importada anteriormente."

    if identificador:
        cursor.execute("SELECT * FROM notas_fiscais WHERE identificador_unico = ?", (identificador,))
        if cursor.fetchone():
            conn.close()
            return True, f"A Nota Fiscal '{identificador}' já foi importada anteriormente."

    # 2. Checa se já existe registro nos produtos com essa chave de acesso ou número
    if chave:
        cursor.execute("SELECT COUNT(*) as c FROM produtos WHERE observacoes LIKE ? OR origem LIKE ?", (f"%{chave}%", f"%{chave}%"))
        if cursor.fetchone()['c'] > 0:
            conn.close()
            return True, f"A Nota Fiscal com chave '{chave}' já consta registrada no estoque."

    if numero_nf and data_br:
        cursor.execute("SELECT COUNT(*) as c FROM produtos WHERE origem LIKE ? AND origem LIKE ?", (f"%{data_br}%", f"%{numero_nf}%"))
        if cursor.fetchone()['c'] > 0:
            conn.close()
            return True, f"A Nota Fiscal nº {numero_nf} de {data_br} já consta registrada no estoque."

    conn.close()

    # 3. Checa também no Supabase (se online)
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
            if chave:
                res_sb = sb.table("produtos").select("id").or_(f"observacoes.ilike.%{chave}%,origem.ilike.%{chave}%").limit(1).execute()
                if res_sb.data and len(res_sb.data) > 0:
                    return True, f"A Nota Fiscal com chave '{chave}' já foi importada anteriormente no Supabase."
            if numero_nf and data_br:
                res_sb2 = sb.table("produtos").select("id").ilike("origem", f"%{data_br}%").ilike("origem", f"%{numero_nf}%").limit(1).execute()
                if res_sb2.data and len(res_sb2.data) > 0:
                    return True, f"A Nota Fiscal nº {numero_nf} de {data_br} já consta registrada no Supabase."
        except Exception as e:
            pass

    return False, ""

def processar_carga_nf_pdf(pdf_source):
    """
    Processa um PDF de Nota Fiscal de Compra para controle de estoque:
    - Valida se a Nota Fiscal já foi importada (impede duplicação acidental).
    - O que for inserido NÃO remove o anterior.
    - Se o SKU (código) já existir no estoque:
      * Adiciona APENAS a nova quantidade ao estoque (quantidade_estoque += qtd_nova)
      * Adiciona à quantidade comprada histórica (quantidade_comprada += qtd_nova)
      * NÃO altera em nada os valores ou preços anteriores do item já existente.
    - Se for um NOVO SKU (não existente no estoque):
      * Inclui o novo SKU com seus valores de custo, revista e quantidade da Nota Fiscal.
    """
    import parse_nf
    from datetime import datetime

    metadata = parse_nf.extract_nf_metadata(pdf_source)

    # VALIDAÇÃO: Impede que a mesma Nota Fiscal seja subida mais de uma vez
    ja_importada, msg_bloqueio = verificar_nf_ja_importada(metadata)
    if ja_importada:
        raise ValueError(f"⚠️ Operação cancelada: {msg_bloqueio}")

    raw_items = parse_nf.parse_items(pdf_source)
    if not raw_items:
        raise ValueError("Nenhum item foi encontrado ou o PDF não possui o formato de Nota Fiscal esperado.")

    grouped_items = parse_nf.group_items_by_sku(raw_items)

    produtos_atuais = get_produtos()
    prods_por_codigo = {}
    for p in produtos_atuais:
        cod = str(p['codigo']).strip()
        if cod not in prods_por_codigo:
            prods_por_codigo[cod] = []
        prods_por_codigo[cod].append(p)

    skus_atualizados = []
    skus_novos = []
    total_unidades_processadas = 0

    sb = None
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
        except Exception as e:
            print("Aviso ao conectar com Supabase:", e)

    conn = get_connection()
    cursor = conn.cursor()

    tag_nf = f"[NF: {metadata.get('identificador_unico', '')}]" if metadata.get('identificador_unico') else ""

    for item in grouped_items:
        cod = str(item['codigo']).strip()
        qtd_nova = int(item['quantidade'])
        total_unidades_processadas += qtd_nova

        if cod in prods_por_codigo:
            # SKU JÁ EXISTE NO ESTOQUE:
            # Regra: NÃO altera em nada o anterior (preços, custos, margens permanecem intocados).
            # Apenas incrementa a quantidade do estoque e o histórico de compras.
            alvo = prods_por_codigo[cod][0]
            novo_estoque = int(alvo['quantidade_estoque']) + qtd_nova
            nova_comprada = int(alvo['quantidade_comprada']) + qtd_nova

            obs_anterior = alvo.get('observacoes') or ""
            nova_obs = f"{obs_anterior} {tag_nf}".strip() if tag_nf and tag_nf not in obs_anterior else obs_anterior

            if sb:
                try:
                    sb.table("produtos").update({
                        "quantidade_estoque": novo_estoque,
                        "quantidade_comprada": nova_comprada,
                        "observacoes": nova_obs
                    }).eq("id", alvo['id']).execute()
                except Exception as e:
                    print(f"Erro ao atualizar estoque do SKU {cod} no Supabase:", e)

            cursor.execute("""
                UPDATE produtos SET
                    quantidade_estoque = ?,
                    quantidade_comprada = ?,
                    observacoes = ?
                WHERE id = ?
            """, (novo_estoque, nova_comprada, nova_obs, alvo['id']))

            skus_atualizados.append({
                "codigo": cod,
                "descricao": alvo['descricao'],
                "qtd_adicionada": qtd_nova,
                "estoque_anterior": alvo['quantidade_estoque'],
                "novo_estoque": novo_estoque,
                "tipo": "atualizado"
            })
        else:
            # NOVO SKU:
            # Cadastra o novo produto mantendo os valores da nota fiscal
            cat = categorize_product(item['descricao'])
            vl_unit_sugerido = float(item['vl_unit_sugerido'])
            vl_unit_pago = float(item['vl_unit_pago'])
            desconto_compra = float(item.get('desconto_compra_unit', 0.0))
            preco_venda = vl_unit_sugerido

            novo_prod_data = {
                "codigo": cod,
                "descricao": item['descricao'],
                "categoria": cat,
                "unidade": item.get('unidade', 'UN'),
                "quantidade_comprada": qtd_nova,
                "quantidade_estoque": qtd_nova,
                "quantidade_vendida": 0,
                "vl_unit_sugerido": vl_unit_sugerido,
                "desconto_compra_unit": desconto_compra,
                "vl_unit_pago": vl_unit_pago,
                "desconto_repassado_unit": 0.0,
                "vl_unit_venda_sugerida_final": preco_venda,
                "preco_revista": vl_unit_sugerido,
                "preco_revista_promo": None,
                "pagina_revista": None,
                "nome_revista": item['descricao'],
                "origem": metadata.get('origem', f"Nota Fiscal {datetime.now().strftime('%d/%m/%Y')}"),
                "observacoes": f"Carga via PDF {tag_nf}".strip()
            }

            if sb:
                try:
                    sb.table("produtos").insert(novo_prod_data).execute()
                except Exception as e:
                    print(f"Erro ao inserir novo SKU {cod} no Supabase:", e)

            cursor.execute("""
                INSERT INTO produtos (
                    codigo, descricao, categoria, unidade,
                    quantidade_comprada, quantidade_estoque, quantidade_vendida,
                    vl_unit_sugerido, desconto_compra_unit, vl_unit_pago,
                    desconto_repassado_unit, vl_unit_venda_sugerida_final,
                    preco_revista, preco_revista_promo, pagina_revista,
                    nome_revista, origem, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0.0, ?, ?, NULL, NULL, ?, ?, ?)
            """, (
                cod, item['descricao'], cat, item.get('unidade', 'UN'),
                qtd_nova, qtd_nova, vl_unit_sugerido, desconto_compra,
                vl_unit_pago, preco_venda, vl_unit_sugerido, item['descricao'],
                novo_prod_data['origem'], novo_prod_data['observacoes']
            ))

            skus_novos.append({
                "codigo": cod,
                "descricao": item['descricao'],
                "qtd_adicionada": qtd_nova,
                "vl_unit_pago": vl_unit_pago,
                "vl_unit_sugerido": vl_unit_sugerido,
                "tipo": "novo"
            })

    # Registra a Nota Fiscal na tabela de controle de notas fiscais importadas
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO notas_fiscais (
            identificador_unico, chave_acesso, numero_nf, serie, protocolo,
            data_emissao, valor_total, total_itens, total_unidades, origem
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.get('identificador_unico') or f"NF_{metadata.get('numero_nf')}",
            metadata.get('chave_acesso') or "",
            metadata.get('numero_nf') or "",
            metadata.get('serie_nf') or "",
            metadata.get('protocolo_nf') or "",
            metadata.get('data_nf_br') or "",
            sum(it['vl_total_pago'] for it in grouped_items),
            len(grouped_items),
            total_unidades_processadas,
            metadata.get('origem') or ""
        ))
    except Exception as e:
        print("Aviso ao registrar NF em notas_fiscais:", e)

    conn.commit()
    conn.close()

    return {
        "sucesso": True,
        "metadata": metadata,
        "total_linhas_pdf": len(raw_items),
        "total_skus_pdf": len(grouped_items),
        "total_unidades": total_unidades_processadas,
        "skus_atualizados": skus_atualizados,
        "skus_novos": skus_novos
    }

def estornar_importacao_nf(identificador_unico_ou_chave, skus_info=None):
    """
    Remove ou estorna os dados inseridos por uma Nota Fiscal específica:
    - Para SKUs que foram criados exclusivamente por esta NF:
      * Se não houve vendas deles, são removidos do banco.
      * Se já houve vendas, reduz a quantidade_comprada e quantidade_estoque pela quantidade desta NF.
    - Para SKUs que já existiam e apenas tiveram estoque incrementado por esta NF:
      * Subtrai a quantidade adicionada da quantidade_estoque e da quantidade_comprada.
      * Preços e custos antigos continuam 100% preservados.
    - Remove o registro da NF na tabela de notas fiscais e das observações dos produtos.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sb = None
    if supabase_client.is_supabase_configured():
        try:
            sb = supabase_client.get_client()
        except Exception as e:
            print("Aviso ao conectar com Supabase:", e)

    chave = identificador_unico_ou_chave.strip()
    tag_nf = f"[NF: {chave}]"

    # 1. Se skus_info não for passado, tenta descobrir pelos produtos que têm a tag ou origem
    produtos_atuais = get_produtos()
    produtos_afetados = [p for p in produtos_atuais if chave in (p.get('observacoes') or '') or chave in (p.get('origem') or '')]

    removidos = []
    ajustados = []

    if skus_info:
        for s in skus_info.get('skus_novos', []):
            cod = str(s['codigo']).strip()
            qtd_add = int(s['qtd_adicionada'])
            p = next((x for x in produtos_atuais if str(x['codigo']).strip() == cod), None)
            if p:
                if p.get('quantidade_vendida', 0) == 0 and p.get('quantidade_comprada', 0) <= qtd_add:
                    # Pode excluir com segurança
                    cursor.execute("DELETE FROM produtos WHERE id = ?", (p['id'],))
                    if sb:
                        try:
                            sb.table("produtos").delete().eq("id", p['id']).execute()
                        except Exception as e:
                            print(f"Erro ao remover produto {cod} no Supabase:", e)
                    removidos.append(f"{cod} - {p['descricao']}")
                else:
                    # Reduz a quantidade inserida
                    n_est = max(0, int(p['quantidade_estoque']) - qtd_add)
                    n_comp = max(0, int(p['quantidade_comprada']) - qtd_add)
                    cursor.execute("UPDATE produtos SET quantidade_estoque = ?, quantidade_comprada = ? WHERE id = ?", (n_est, n_comp, p['id']))
                    if sb:
                        try:
                            sb.table("produtos").update({"quantidade_estoque": n_est, "quantidade_comprada": n_comp}).eq("id", p['id']).execute()
                        except Exception as e:
                            pass
                    ajustados.append(f"{cod} - {p['descricao']} (-{qtd_add} un)")

        for s in skus_info.get('skus_atualizados', []):
            cod = str(s['codigo']).strip()
            qtd_add = int(s['qtd_adicionada'])
            p = next((x for x in produtos_atuais if str(x['codigo']).strip() == cod), None)
            if p:
                n_est = max(0, int(p['quantidade_estoque']) - qtd_add)
                n_comp = max(0, int(p['quantidade_comprada']) - qtd_add)
                obs_limpa = (p.get('observacoes') or '').replace(tag_nf, '').strip()

                cursor.execute("UPDATE produtos SET quantidade_estoque = ?, quantidade_comprada = ?, observacoes = ? WHERE id = ?", (n_est, n_comp, obs_limpa, p['id']))
                if sb:
                    try:
                        sb.table("produtos").update({"quantidade_estoque": n_est, "quantidade_comprada": n_comp, "observacoes": obs_limpa}).eq("id", p['id']).execute()
                    except Exception as e:
                        pass
                ajustados.append(f"{cod} - {p['descricao']} (-{qtd_add} un)")
    else:
        # Fallback genérico pelos produtos marcados
        for p in produtos_afetados:
            obs_limpa = (p.get('observacoes') or '').replace(tag_nf, '').strip()
            cursor.execute("UPDATE produtos SET observacoes = ? WHERE id = ?", (obs_limpa, p['id']))
            if sb:
                try:
                    sb.table("produtos").update({"observacoes": obs_limpa}).eq("id", p['id']).execute()
                except Exception as e:
                    pass

    # Remove do banco local de notas fiscais
    try:
        cursor.execute("DELETE FROM notas_fiscais WHERE identificador_unico = ? OR chave_acesso = ?", (chave, chave))
    except:
        pass

    conn.commit()
    conn.close()

    return {
        "sucesso": True,
        "skus_removidos": removidos,
        "skus_ajustados": ajustados
    }


