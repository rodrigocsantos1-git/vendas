import db

prods = db.get_produtos()
p = prods[0]
init_stock = p['quantidade_estoque']
print(f"Testando venda no Supabase para: {p['descricao']} (Estoque inicial: {init_stock})")

db.registrar_venda(
    produto_id=p['id'],
    qtd_venda=1,
    vl_unit_venda=34.90,
    desconto_repassado_unit=0.0,
    cliente="Cliente Teste Supabase",
    forma_pagamento="Pix",
    status_pagamento="Recebido",
    data_venda="2026-11-08",
    observacoes="Teste de gravacao em nuvem",
    cliente_telefone="11999998888",
    cliente_email="teste@supabase.com",
    cliente_nascimento="1990-05-20"
)

# Verify
vendas = db.get_vendas()
clientes = db.get_clientes()
prods_after = db.get_produtos()
p_after = [x for x in prods_after if x['id'] == p['id']][0]

print("Vendas no Supabase:", len(vendas))
print("Clientes no Supabase:", len(clientes))
print(f"Novo estoque no Supabase: {p_after['quantidade_estoque']} (Baixou 1? {p_after['quantidade_estoque'] == init_stock - 1})")

# Cancel test sale
db.cancelar_venda(vendas[0]['id'])
db.delete_cliente(clientes[0]['id'])

prods_restored = db.get_produtos()
p_restored = [x for x in prods_restored if x['id'] == p['id']][0]
print(f"Estoque restaurado no Supabase: {p_restored['quantidade_estoque']} (Igual inicial? {p_restored['quantidade_estoque'] == init_stock})")
print("Vendas restantes:", len(db.get_vendas()))
print("Clientes restantes:", len(db.get_clientes()))
