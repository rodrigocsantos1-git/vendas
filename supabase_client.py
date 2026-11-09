import os
import json
from supabase import create_client, Client

CONFIG_SUPABASE_FILE = "config_supabase.json"

def get_supabase_config():
    # 1. Verifica Streamlit Secrets (Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
            key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase_key")
            if url and key:
                return {"supabase_url": str(url).strip(), "supabase_key": str(key).strip()}
    except:
        pass

    # 2. Verifica Variaveis de Ambiente (Vercel / Render / Docker)
    env_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    env_key = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if env_url and env_key:
        return {"supabase_url": env_url.strip(), "supabase_key": env_key.strip()}

    # 3. Verifica arquivo local de configuracao
    if os.path.exists(CONFIG_SUPABASE_FILE):
        try:
            with open(CONFIG_SUPABASE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def set_supabase_config(url, key):
    cfg = {"supabase_url": url.strip(), "supabase_key": key.strip()}
    with open(CONFIG_SUPABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def is_supabase_configured():
    cfg = get_supabase_config()
    return bool(cfg.get("supabase_url") and cfg.get("supabase_key"))

def get_client() -> Client:
    cfg = get_supabase_config()
    url = cfg.get("supabase_url")
    key = cfg.get("supabase_key")
    if not url or not key:
        raise ValueError("Supabase não configurado. Forneça URL e Key.")
    return create_client(url, key)

def test_supabase_connection():
    if not is_supabase_configured():
        return False, "URL e Chave do Supabase não configuradas."
    try:
        supabase = get_client()
        # Test query
        res = supabase.table("produtos").select("id", count="exact").limit(1).execute()
        count = res.count if res.count is not None else len(res.data)
        return True, f"Conexão com Supabase realizada com sucesso! ({count} produtos no banco em nuvem)"
    except Exception as e:
        return False, f"Erro de conexão com Supabase: {str(e)}"

def sync_local_to_supabase():
    """Envia todos os produtos, vendas e clientes locais para o Supabase."""
    import db
    if not is_supabase_configured():
        return False, "Configure o Supabase primeiro."
    try:
        supabase = get_client()
        
        # 1. Produtos
        prods = db.get_produtos()
        for p in prods:
            p_data = {
                "codigo": p['codigo'],
                "descricao": p['descricao'],
                "categoria": p['categoria'],
                "unidade": p['unidade'],
                "quantidade_comprada": p['quantidade_comprada'],
                "quantidade_estoque": p['quantidade_estoque'],
                "quantidade_vendida": p['quantidade_vendida'],
                "vl_unit_sugerido": p['vl_unit_sugerido'],
                "desconto_compra_unit": p['desconto_compra_unit'],
                "vl_unit_pago": p['vl_unit_pago'],
                "desconto_repassado_unit": p['desconto_repassado_unit'],
                "vl_unit_venda_sugerida_final": p['vl_unit_venda_sugerida_final'],
                "preco_revista": p['preco_revista'],
                "preco_revista_promo": p['preco_revista_promo'],
                "pagina_revista": p['pagina_revista'],
                "nome_revista": p['nome_revista'],
                "origem": p['origem'],
                "observacoes": p['observacoes'] or ""
            }
            # Upsert by codigo
            supabase.table("produtos").upsert(p_data, on_conflict="codigo").execute()
            
        # 2. Clientes
        clientes = db.get_clientes()
        for c in clientes:
            c_data = {
                "nome": c['nome'],
                "telefone": c['telefone'] or "",
                "email": c['email'] or "",
                "data_nascimento": c['data_nascimento'] or None,
                "observacoes": c['observacoes'] or ""
            }
            supabase.table("clientes").insert(c_data).execute()
            
        # 3. Vendas
        vendas = db.get_vendas()
        for v in vendas:
            v_data = {
                "codigo": v['codigo'],
                "descricao": v['descricao'],
                "quantidade": v['quantidade'],
                "vl_unit_pago": v['vl_unit_pago'],
                "vl_unit_venda": v['vl_unit_venda'],
                "desconto_repassado_unit": v['desconto_repassado_unit'],
                "vl_total_venda": v['vl_total_venda'],
                "lucro_total": v['lucro_total'],
                "cliente": v['cliente'],
                "cliente_telefone": v['cliente_telefone'] or "",
                "cliente_email": v['cliente_email'] or "",
                "cliente_nascimento": v['cliente_nascimento'] or None,
                "forma_pagamento": v['forma_pagamento'],
                "status_pagamento": v['status_pagamento'],
                "data_venda": v['data_venda'],
                "observacoes": v['observacoes'] or ""
            }
            supabase.table("vendas").insert(v_data).execute()
            
        return True, "Migração completa para o Supabase concluída com sucesso!"
    except Exception as e:
        return False, f"Falha na migração: {str(e)}"
