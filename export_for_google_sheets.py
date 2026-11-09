import db
import pandas as pd

# Load current data
df_prod = pd.DataFrame(db.get_produtos())
df_vendas = pd.DataFrame(db.get_vendas())
df_clientes = pd.DataFrame(db.get_clientes())

# Reorder and format columns for clean Google Sheets view
cols_prod = [
    'codigo', 'descricao', 'categoria', 'unidade',
    'quantidade_comprada', 'quantidade_estoque', 'quantidade_vendida',
    'vl_unit_pago', 'desconto_compra_unit', 'preco_revista', 'preco_revista_promo', 'pagina_revista',
    'desconto_repassado_unit', 'vl_unit_venda_sugerida_final', 'origem', 'observacoes'
]
df_prod_clean = df_prod[cols_prod].rename(columns={
    'codigo': 'Código',
    'descricao': 'Produto',
    'categoria': 'Categoria',
    'unidade': 'Unidade',
    'quantidade_comprada': 'Qtd Comprada',
    'quantidade_estoque': 'Qtd em Estoque',
    'quantidade_vendida': 'Qtd Vendida',
    'vl_unit_pago': 'Quanto Paguei (Custo R$)',
    'desconto_compra_unit': 'Desconto Compra (R$)',
    'preco_revista': 'Valor Revista Catálogo (R$)',
    'preco_revista_promo': 'Promoção Ciclo Revista (R$)',
    'pagina_revista': 'Página Catálogo',
    'desconto_repassado_unit': 'Desconto a Repassar (R$)',
    'vl_unit_venda_sugerida_final': 'Preço Venda Praticado (R$)',
    'origem': 'Origem',
    'observacoes': 'Observações'
})

# Save Excel
excel_path = "Base_Dados_Natura.xlsx"
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_prod_clean.to_excel(writer, sheet_name='Estoque_Produtos', index=False)
    if not df_vendas.empty:
        df_vendas.to_excel(writer, sheet_name='Historico_Vendas', index=False)
    else:
        # Template for sales
        df_vendas_template = pd.DataFrame(columns=[
            'ID', 'Data Venda', 'Cliente', 'Telefone', 'Email', 'Data Nascimento',
            'Código Produto', 'Produto', 'Quantidade', 'Custo Unitário',
            'Preço Venda Unitário', 'Total Venda', 'Lucro Total', 'Forma Pagamento', 'Status'
        ])
        df_vendas_template.to_excel(writer, sheet_name='Historico_Vendas', index=False)
        
    if not df_clientes.empty:
        df_clientes.to_excel(writer, sheet_name='Clientes', index=False)
    else:
        # Template for clients
        df_cli_template = pd.DataFrame(columns=[
            'Nome Completo', 'Telefone / WhatsApp', 'E-mail', 'Data Nascimento', 'Observações'
        ])
        df_cli_template.to_excel(writer, sheet_name='Clientes', index=False)

# Also CSV for easy copy/paste
df_prod_clean.to_csv("Base_Produtos_Natura.csv", index=False, encoding="utf-8-sig")

print("Base files created successfully:")
print("- Base_Dados_Natura.xlsx")
print("- Base_Produtos_Natura.csv")
