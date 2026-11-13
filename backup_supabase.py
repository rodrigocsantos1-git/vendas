#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Backup Automatizado do Supabase - Vendas Barreto Corrêa
Exporta dados completos (produtos, clientes, vendas, logs_importacao_nfe) em JSON e CSV.
Mantém histórico dos últimos 30 backups na pasta 'backups/'.
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path

# Tentativa de carregar supabase client
try:
    from supabase import create_client, Client
except ImportError:
    print("[ERRO] Pacote 'supabase' não instalado. Instale com: pip install supabase")
    sys.exit(1)

# Diretório base
BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Obtenção de credenciais
def get_credentials():
    # 1. Variáveis de ambiente (ex: GitHub Actions secrets)
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

    # 3. Fallback para as credenciais padrão do projeto
    return (
        "https://evqjlgfhdpisxxbvxelh.supabase.co",
        "sb_publishable_YLDCZL8qtWXqIFEeH7QzfQ_zf7v5gcQ"
    )

def fetch_table(client: Client, table_name: str):
    """Busca todos os registros de uma tabela (com paginação para bases com mais de 1000 registros)"""
    all_rows = []
    page_size = 1000
    offset = 0

    while True:
        try:
            res = client.table(table_name).select("*").range(offset, offset + page_size - 1).execute()
            data = res.data or []
            all_rows.extend(data)
            if len(data) < page_size:
                break
            offset += page_size
        except Exception as e:
            # Caso a tabela não exista ou ocorra restrição de RLS
            print(f"  [AVISO] Não foi possível ler tabela '{table_name}': {e}")
            break

    return all_rows

def export_csv(rows, filepath: Path):
    """Exporta lista de dicionários para CSV com UTF-8 BOM para abrir perfeitamente no Excel"""
    if not rows:
        return
    headers = list(rows[0].keys())
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def cleanup_old_backups(keep_count: int = 30):
    """Remove backups antigos mantendo apenas os últimos N backups JSON"""
    json_backups = sorted(BACKUP_DIR.glob("backup_supabase_*.json"))
    if len(json_backups) > keep_count:
        to_delete = json_backups[:-keep_count]
        for f in to_delete:
            try:
                f.unlink()
                print(f"  [LIMPEZA] Backup antigo removido: {f.name}")
            except Exception:
                pass

def main():
    print("=" * 60)
    print("  INICIANDO BACKUP DO BANCO SUPABASE - VENDAS BARRETO CORRÊA")
    print("=" * 60)

    url, key = get_credentials()
    print(f"Conectando ao Supabase: {url}")
    client = create_client(url, key)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    now_iso = datetime.now().isoformat()

    tabelas = ["produtos", "clientes", "vendas", "logs_importacao_nfe"]
    dados_backup = {}
    contagens = {}

    for tab in tabelas:
        print(f"Lendo tabela '{tab}'...")
        rows = fetch_table(client, tab)
        dados_backup[tab] = rows
        contagens[tab] = len(rows)
        print(f"  -> {len(rows)} registro(s) obtido(s).")

    # Monta estrutura completa do backup JSON
    payload = {
        "metadata": {
            "projeto": "Vendas Barreto Corrêa",
            "gerado_em": now_iso,
            "formato_versao": "2.0",
            "estatisticas": contagens
        },
        "tabelas": dados_backup
    }

    # Salva arquivo JSON versionado
    json_filename = f"backup_supabase_{timestamp}.json"
    json_path = BACKUP_DIR / json_filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Arquivo JSON gerado: {json_path}")

    # Salva também como 'backup_latest.json' para referência rápida
    latest_path = BACKUP_DIR / "backup_latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Gera CSVs mais recentes de cada tabela
    for tab in ["produtos", "clientes", "vendas"]:
        if dados_backup[tab]:
            csv_path = BACKUP_DIR / f"{tab}_latest.csv"
            export_csv(dados_backup[tab], csv_path)
            print(f"[OK] Export CSV atualizado: {csv_path.name}")

    # Rotatividade de backups
    cleanup_old_backups(keep_count=30)

    print("\n" + "=" * 60)
    print("  RESUMO DO BACKUP:")
    for tab, count in contagens.items():
        print(f"   - {tab.ljust(22)}: {count:4d} registro(s)")
    print(f"  Total de tabelas salvas: {len(tabelas)}")
    print(f"  Local dos arquivos     : {BACKUP_DIR}")
    print("=" * 60)
    print("Backup concluído com sucesso!")

if __name__ == "__main__":
    main()
