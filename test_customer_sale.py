import db

db.init_db()
prods = db.get_produtos()
p = prods[0]
initial_stock = p['quantidade_estoque']

print(f"Testing with product: {p['descricao']} (initial stock: {initial_stock})")

# Register a sale with customer info
db.registrar_venda(
    produto_id=p['id'],
    qtd_venda=1,
    vl_unit_venda=34.90,
    desconto_repassado_unit=0.0,
    cliente="Camila Rocha",
    forma_pagamento="Pix",
    status_pagamento="Recebido",
    data_venda="2026-11-08",
    observacoes="Cliente comprou para presente",
    cliente_telefone="(11) 99887-6655",
    cliente_email="camila@exemplo.com",
    cliente_nascimento="1995-11-15"
)

# Check customer
cls = db.get_clientes()
print("Clientes registered:", len(cls))
camila = [c for c in cls if c['nome'] == "Camila Rocha"][0]
print("Camila record:", camila)

# Check sale
vendas = db.get_vendas()
print("Vendas registered:", len(vendas))
v = vendas[0]
print(f"Venda details: Cliente={v['cliente']}, Tel={v['cliente_telefone']}, Email={v['cliente_email']}, Nasc={v['cliente_nascimento']}, Total={v['vl_total_venda']}, Lucro={v['lucro_total']}")

# Cancel sale to restore test state
db.cancelar_venda(v['id'])
prods_after = db.get_produtos()
print("Stock restored:", prods_after[0]['quantidade_estoque'] == initial_stock)

# Remove test customer
db.delete_cliente(camila['id'])
print("Cleaned up test customer. Clientes now:", len(db.get_clientes()))
