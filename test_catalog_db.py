import db
prods = db.get_produtos()
print(f"Total de itens no banco: {len(prods)}")
print("-" * 95)
print(f"{'CÓDIGO':<7} | {'PRODUTO':<32} | {'PAGO (NF)':<10} | {'REVISTA':<10} | {'PROMO':<8} | {'PÁG'}")
print("-" * 95)
for p in prods:
    promo_str = f"R$ {p['preco_revista_promo']:.2f}" if p['preco_revista_promo'] else "-"
    print(f"{p['codigo']:<7} | {p['descricao'][:32]:<32} | R$ {p['vl_unit_pago']:<7.2f} | R$ {p['preco_revista']:<7.2f} | {promo_str:<8} | Pág. {p['pagina_revista']}")
