#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Keep-Alive do Supabase - Vendas Barreto Corrêa
Executado diariamente para manter o banco Supabase ativo (evitando pausa por inatividade).
Insere um registro com data/horário e reinicia o ciclo ao atingir 1 semana (7 registros).
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("[ERRO] Pacote 'supabase' não instalado. Instale com: pip install supabase")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent

def get_credentials():
    # 1. Variáveis de ambiente
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return url.strip(), key.strip()

    # 2. Arquivo config_supabase.json
    cfg_file = BASE_DIR / "config_supabase.json"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                u = data.get("supabase_url")
                k = data.get("supabase_key")
                if u and k:
                    return u.strip(), k.strip()
        except Exception:
            pass

    # 3. Fallback
    return (
        "https://evqjlgfhdpisxxbvxelh.supabase.co",
        "sb_publishable_YLDCZL8qtWXqIFEeH7QzfQ_zf7v5gcQ"
    )

def main():
    print("=" * 60)
    print("  KEEP-ALIVE DIÁRIO - SUPABASE VENDAS BARRETO CORRÊA")
    print(f"  Horário de execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)

    url, key = get_credentials()
    client: Client = create_client(url, key)

    table_name = "keep_alive"

    try:
        # 1. Busca registros atuais na tabela keep_alive
        res = client.table(table_name).select("id, data_hora, mensagem").order("id", desc=False).execute()
        registros = res.data or []
        total_atual = len(registros)
        print(f"[STATUS] Registros existentes na semana: {total_atual}/7")

        # 2. Se já completou 1 semana (7 registros ou mais), limpa a tabela para reiniciar
        if total_atual >= 7:
            print("[CICLO] 1 semana completa atingida! Limpando histórico para reiniciar o ciclo...")
            for r in registros:
                client.table(table_name).delete().eq("id", r["id"]).execute()
            print("[OK] Tabela reiniciada com sucesso para um novo ciclo de 7 dias.")

        # 3. Insere o registro de hoje
        novo_registro = {
            "data_hora": datetime.now(timezone.utc).isoformat(),
            "origem": "github-actions-cron",
            "mensagem": f"Supabase ativo - Ping diário {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        }

        res_ins = client.table(table_name).insert(novo_registro).execute()
        print(f"[SUCESSO] Novo registro de atividade inserido com sucesso!")
        if res_ins.data:
            print(f"  -> ID gerado: {res_ins.data[0].get('id')}")
            print(f"  -> Data/Hora: {res_ins.data[0].get('data_hora')}")

    except Exception as e:
        err_msg = str(e)
        if "PGRST205" in err_msg or "keep_alive" in err_msg:
            print(f"[AVISO] A tabela '{table_name}' ainda precisa ser criada no Supabase SQL Editor.")
            print("\nExecute o SQL abaixo no painel do Supabase:")
            print("-" * 60)
            print("""CREATE TABLE IF NOT EXISTS public.keep_alive (
    id BIGSERIAL PRIMARY KEY,
    data_hora TIMESTAMPTZ DEFAULT NOW(),
    origem TEXT DEFAULT 'github-actions',
    mensagem TEXT DEFAULT 'Supabase ativo'
);

ALTER TABLE public.keep_alive ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso publico keep_alive" 
ON public.keep_alive 
FOR ALL 
TO anon, authenticated 
USING (true) 
WITH CHECK (true);""")
            print("-" * 60)
            # Ping de fallback para manter ativo mesmo se a tabela não foi criada ainda
            try:
                client.table("produtos").select("id").limit(1).execute()
                print("[FALLBACK] Ping realizado com sucesso na tabela 'produtos' para manter o banco ativo!")
            except Exception as e2:
                print(f"[ERRO FALLBACK]: {e2}")
        else:
            print(f"[ERRO]: {err_msg}")
            raise e

    print("=" * 60)
    print("Processo Keep-Alive finalizado.")

if __name__ == "__main__":
    main()
