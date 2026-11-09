import db

prods = db.get_produtos()

with open("schema_supabase.sql", "a", encoding="utf-8") as f:
    f.write("\n-- ==============================================================\n")
    f.write("-- DADOS INICIAIS DA NOTA FISCAL 05/11/2026 E CATÁLOGO NATURA\n")
    f.write("-- ==============================================================\n\n")
    
    for p in prods:
        promo_val = f"{p['preco_revista_promo']}" if p['preco_revista_promo'] else "NULL"
        pag_val = f"{p['pagina_revista']}" if p['pagina_revista'] else "NULL"
        desc_clean = p['descricao'].replace("'", "''")
        nome_rev_clean = (p['nome_revista'] or '').replace("'", "''")
        obs_clean = (p['observacoes'] or '').replace("'", "''")
        
        insert_sql = f"""INSERT INTO public.produtos (
    codigo, descricao, categoria, unidade, quantidade_comprada, quantidade_estoque,
    quantidade_vendida, vl_unit_sugerido, desconto_compra_unit, vl_unit_pago,
    desconto_repassado_unit, vl_unit_venda_sugerida_final, preco_revista, preco_revista_promo,
    pagina_revista, nome_revista, origem, observacoes
) VALUES (
    '{p['codigo']}', '{desc_clean}', '{p['categoria']}', '{p['unidade']}', {p['quantidade_comprada']}, {p['quantidade_estoque']},
    {p['quantidade_vendida']}, {p['vl_unit_sugerido']}, {p['desconto_compra_unit']}, {p['vl_unit_pago']},
    {p['desconto_repassado_unit']}, {p['vl_unit_venda_sugerida_final']}, {p['preco_revista']}, {promo_val},
    {pag_val}, '{nome_rev_clean}', 'Nota Fiscal 05/11/2026', '{obs_clean}'
);\n"""
        f.write(insert_sql)

print(f"Added {len(prods)} inserts to schema_supabase.sql")
