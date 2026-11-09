import sqlite3
import os
from parse_nf import parse_items

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
    
    # Check if new columns exist if table was already created
    cursor.execute("PRAGMA table_info(produtos)")
    cols = [r['name'] for r in cursor.fetchall()]
    if 'preco_revista' not in cols:
        cursor.execute("ALTER TABLE produtos ADD COLUMN preco_revista REAL DEFAULT 0.0")
    if 'preco_revista_promo' not in cols:
        cursor.execute("ALTER TABLE produtos ADD COLUMN preco_revista_promo REAL")
    if 'pagina_revista' not in cols:
        cursor.execute("ALTER TABLE produtos ADD COLUMN pagina_revista INTEGER")
    if 'nome_revista' not in cols:
        cursor.execute("ALTER TABLE produtos ADD COLUMN nome_revista TEXT")

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
        produto_id INTEGER NOT NULL,
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
    
    # Check if migration columns exist in vendas
    cursor.execute("PRAGMA table_info(vendas)")
    v_cols = [r['name'] for r in cursor.fetchall()]
    if 'cliente_id' not in v_cols:
        cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_id INTEGER")
    if 'cliente_telefone' not in v_cols:
        cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_telefone TEXT")
    if 'cliente_email' not in v_cols:
        cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_email TEXT")
    if 'cliente_nascimento' not in v_cols:
        cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_nascimento TEXT")
    
    conn.commit()
    
    # Import catalog mapping
    from build_catalog_mapping import catalog_data

    # Check if empty or forced reseed
    cursor.execute("SELECT COUNT(*) as cnt FROM produtos")
    count = cursor.fetchone()['cnt']
    
    if count == 0 or force_reseed:
        if force_reseed:
            cursor.execute("DELETE FROM vendas")
            cursor.execute("DELETE FROM produtos")
            conn.commit()
            
        items = parse_items()
        for it in items:
            cat = categorize_product(it['descricao'])
            qtd = it['quantidade']
            vl_sug = it['vl_unit_sugerido']
            desc_compra = abs(it['desconto_unit'])
            vl_pago = it['vl_unit_pago']
            
            # Catalog info lookup
            c_info = catalog_data.get(it['codigo'], {})
            preco_rev = c_info.get('preco_revista_tabela', vl_sug)
            preco_promo = c_info.get('preco_revista_promo', None)
            pag_rev = c_info.get('pagina_revista', None)
            nome_rev = c_info.get('nome_revista', it['descricao'])

            # Default final selling price suggestion is the catalog price, 
            # with 0 discount passed to customer initially (editable)
            vl_venda_padrao = preco_rev
            
            cursor.execute("""
            INSERT INTO produtos (
                codigo, descricao, categoria, unidade,
                quantidade_comprada, quantidade_estoque, quantidade_vendida,
                vl_unit_sugerido, desconto_compra_unit, vl_unit_pago,
                desconto_repassado_unit, vl_unit_venda_sugerida_final,
                preco_revista, preco_revista_promo, pagina_revista, nome_revista,
                origem, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, 'Nota Fiscal 05/11/2026', '')
            """, (
                it['codigo'],
                it['descricao'],
                cat,
                it['unidade'],
                qtd,
                qtd,
                vl_sug,
                desc_compra,
                vl_pago,
                vl_venda_padrao,
                preco_rev,
                preco_promo,
                pag_rev,
                nome_rev
            ))
        conn.commit()
        print(f"Banco inicializado com {len(items)} produtos da Nota Fiscal e dados do Catálogo.")
    else:
        # Update existing records with catalog info if they don't have it
        for cod, c_info in catalog_data.items():
            cursor.execute("""
            UPDATE produtos SET
                preco_revista = ?,
                preco_revista_promo = ?,
                pagina_revista = ?,
                nome_revista = ?
            WHERE codigo = ?
            """, (
                c_info.get('preco_revista_tabela'),
                c_info.get('preco_revista_promo'),
                c_info.get('pagina_revista'),
                c_info.get('nome_revista'),
                cod
            ))
        conn.commit()
    
    conn.close()

def get_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_vendas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendas ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_produto(codigo, descricao, categoria, unidade, qtd, vl_sugerido, vl_pago, desconto_compra=0.0, desconto_repassado=0.0, vl_venda=None, observacoes=""):
    if vl_venda is None:
        vl_venda = vl_sugerido - desconto_repassado
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO produtos (
        codigo, descricao, categoria, unidade,
        quantidade_comprada, quantidade_estoque, quantidade_vendida,
        vl_unit_sugerido, desconto_compra_unit, vl_unit_pago,
        desconto_repassado_unit, vl_unit_venda_sugerida_final,
        origem, observacoes
    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 'Cadastro Manual', ?)
    """, (
        codigo, descricao, categoria, unidade,
        qtd, qtd, vl_sugerido, desconto_compra, vl_pago,
        desconto_repassado, vl_venda, observacoes
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_produto(prod_id, updates):
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in updates.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(prod_id)
    query = f"UPDATE produtos SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def delete_produto(prod_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas WHERE produto_id = ?", (prod_id,))
    cursor.execute("DELETE FROM produtos WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()

def get_clientes():
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO clientes (nome, telefone, email, data_nascimento, observacoes)
    VALUES (?, ?, ?, ?, ?)
    """, (nome, telefone, email, data_nascimento, observacoes))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    try:
        import sheets_sync
        sheets_sync.enviar_cliente_para_google_sheets({
            'id': new_id,
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'data_nascimento': data_nascimento,
            'observacoes': observacoes
        })
    except:
        pass

    return new_id

def update_cliente(cliente_id, updates):
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in updates.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(cliente_id)
    query = f"UPDATE clientes SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def delete_cliente(cliente_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE vendas SET cliente_id = NULL WHERE cliente_id = ?", (cliente_id,))
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()

def registrar_venda(produto_id, qtd_venda, vl_unit_venda, desconto_repassado_unit, cliente, forma_pagamento, status_pagamento, data_venda, observacoes="", cliente_id=None, cliente_telefone="", cliente_email="", cliente_nascimento=""):
    conn = get_connection()
    cursor = conn.cursor()
    
    # If customer name is provided but no cliente_id, check if customer already exists or create
    if not cliente_id and cliente and cliente.strip() and cliente.strip().lower() != "consumidor":
        cursor.execute("SELECT id FROM clientes WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))", (cliente.strip(),))
        row = cursor.fetchone()
        if row:
            cliente_id = row['id']
            # Optionally update phone/email if missing
            if cliente_telefone or cliente_email or cliente_nascimento:
                cursor.execute("""
                UPDATE clientes SET
                    telefone = CASE WHEN telefone IS NULL OR telefone = '' THEN ? ELSE telefone END,
                    email = CASE WHEN email IS NULL OR email = '' THEN ? ELSE email END,
                    data_nascimento = CASE WHEN data_nascimento IS NULL OR data_nascimento = '' THEN ? ELSE data_nascimento END
                WHERE id = ?
                """, (cliente_telefone, cliente_email, cliente_nascimento, cliente_id))
        else:
            # Create new client
            cursor.execute("""
            INSERT INTO clientes (nome, telefone, email, data_nascimento, observacoes)
            VALUES (?, ?, ?, ?, 'Cadastrado automaticamente na venda')
            """, (cliente.strip(), cliente_telefone, cliente_email, cliente_nascimento))
            cliente_id = cursor.lastrowid
    
    # Obter dados do produto
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        raise ValueError("Produto não encontrado.")
    
    prod = dict(prod)
    if qtd_venda > prod['quantidade_estoque']:
        conn.close()
        raise ValueError(f"Quantidade insuficiente em estoque. Disponível: {prod['quantidade_estoque']}")
    
    vl_unit_pago = prod['vl_unit_pago']
    vl_total_venda = round(qtd_venda * vl_unit_venda, 2)
    custo_total = round(qtd_venda * vl_unit_pago, 2)
    lucro_total = round(vl_total_venda - custo_total, 2)
    
    # Inserir venda
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
    
    # Atualizar estoque
    novo_estoque = prod['quantidade_estoque'] - qtd_venda
    nova_qtd_vendida = prod['quantidade_vendida'] + qtd_venda
    cursor.execute("""
    UPDATE produtos SET
        quantidade_estoque = ?,
        quantidade_vendida = ?
    WHERE id = ?
    """, (novo_estoque, nova_qtd_vendida, produto_id))
    
    conn.commit()
    new_venda_id = cursor.lastrowid
    conn.close()

    # Tentar enviar diretamente ao Google Sheets via Webhook (se configurado)
    try:
        import sheets_sync
        sheets_sync.enviar_venda_para_google_sheets({
            'id': new_venda_id,
            'codigo': prod['codigo'],
            'descricao': prod['descricao'],
            'quantidade': qtd_venda,
            'vl_unit_pago': vl_unit_pago,
            'vl_unit_venda': vl_unit_venda,
            'desconto_repassado_unit': desconto_repassado_unit,
            'vl_total_venda': vl_total_venda,
            'lucro_total': lucro_total,
            'cliente': cliente,
            'cliente_telefone': cliente_telefone,
            'cliente_email': cliente_email,
            'cliente_nascimento': cliente_nascimento,
            'forma_pagamento': forma_pagamento,
            'status_pagamento': status_pagamento,
            'data_venda': data_venda,
            'observacoes': observacoes
        })
    except Exception as e:
        print("Aviso: webhook Google Sheets não disparado:", e)

    return True

def cancelar_venda(venda_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,))
    venda = cursor.fetchone()
    if not venda:
        conn.close()
        raise ValueError("Venda não encontrada.")
    venda = dict(venda)
    
    # Devolver ao estoque
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

if __name__ == "__main__":
    init_db(force_reseed=True)
    prods = get_produtos()
    print(f"Total produtos no banco: {len(prods)}")
