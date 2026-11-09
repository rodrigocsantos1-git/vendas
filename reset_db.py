import db

db.init_db(force_reseed=True)
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("DELETE FROM vendas")
cursor.execute("DELETE FROM clientes")
conn.commit()

prods = db.get_produtos()
vendas = db.get_vendas()
clientes = db.get_clientes()

print("=== RESET TOTAL CONCLUÍDO ===")
print(f"Total de produtos: {len(prods)} itens cadastrados")
print(f"Estoque total disponível: {sum(p['quantidade_estoque'] for p in prods)} unidades")
print(f"Total de vendas: {len(vendas)}")
print(f"Total de clientes: {len(clientes)}")
conn.close()
