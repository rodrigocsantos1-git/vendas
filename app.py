import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import io
import re
import db
import sheets_sync

# Configuração da Página
st.set_page_config(
    page_title="Controle de Vendas Natura",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar banco de dados
db.init_db()

# Dicionário de Meses em Português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Estilos CSS Personalizados
st.markdown("""
<style>
    .main {
        background-color: #fcfbfa;
    }
    
    .brand-header {
        background: linear-gradient(135deg, #FF6B4A 0%, #D84315 100%);
        padding: 24px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(216, 67, 21, 0.18);
    }
    .brand-title {
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-sub {
        font-size: 14px;
        opacity: 0.95;
        margin-top: 6px;
    }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #ede8e3;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #7d756d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #2b2623;
    }
    .metric-highlight-green {
        color: #2e7d32 !important;
    }
    .metric-highlight-orange {
        color: #d84315 !important;
    }
    .metric-highlight-blue {
        color: #1565c0 !important;
    }
    .metric-sub {
        font-size: 12px;
        color: #8c827a;
        margin-top: 4px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 18px;
        font-weight: 600;
    }
    
    .bday-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border: 1px solid #ffb74d;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    
    .success-sale-banner {
        background: #e8f5e9;
        border: 2px solid #4caf50;
        border-radius: 10px;
        padding: 16px;
        color: #1b5e20;
        font-weight: 600;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

# Funções Auxiliares
def format_currency(val):
    if val is None or pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_date_br(val):
    if not val or pd.isna(val):
        return "-"
    try:
        dt = datetime.strptime(str(val)[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return str(val)

def load_data():
    produtos = db.get_produtos()
    vendas = db.get_vendas()
    clientes = db.get_clientes()
    df_prod = pd.DataFrame(produtos)
    df_vend = pd.DataFrame(vendas)
    df_cli = pd.DataFrame(clientes)
    return df_prod, df_vend, df_cli

# Barra Lateral (Sidebar)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Natura_Cosmeticos_logo.svg/320px-Natura_Cosmeticos_logo.svg.png", width=160)
    st.markdown("### 🛍️ Vendas Natura")
    st.caption("Painel de Gestão Integrado")
    st.divider()
    
    df_p, df_v, df_c = load_data()
    total_itens = df_p['quantidade_comprada'].sum() if not df_p.empty else 0
    total_estoque = df_p['quantidade_estoque'].sum() if not df_p.empty else 0
    total_vendidos = df_p['quantidade_vendida'].sum() if not df_p.empty else 0
    total_clientes = len(df_c)
    
    st.markdown(f"**📦 Unidades Compradas:** {total_itens}")
    st.markdown(f"**🟢 Unidades em Estoque:** {total_estoque}")
    st.markdown(f"**🔴 Unidades Vendidas:** {total_vendidos}")
    st.markdown(f"**👥 Clientes Cadastrados:** {total_clientes}")
    
    if total_itens > 0:
        prog = float(total_vendidos / total_itens)
        st.progress(prog, text=f"Estoque Vendido: {prog*100:.1f}%")
        
    st.divider()
    
    # Conexão com Google Sheets
    st.markdown("🌐 **Planilha Google (Nuvem):**")
    st.caption(f"[Abrir Planilha no Google Sheets]({sheets_sync.GOOGLE_SHEET_URL})")
    if st.button("🔄 Sincronizar Google Sheets", use_container_width=True):
        ok, msg = sheets_sync.sync_from_google_sheet()
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.warning(msg)
            
    st.divider()
    
    # Aniversariantes do mês na barra lateral
    hoje = date.today()
    mes_atual = hoje.month
    nome_mes_atual = MESES_PT.get(mes_atual, "")
    aniversariantes_mes = []
    if not df_c.empty:
        for _, c in df_c.iterrows():
            if c['data_nascimento'] and str(c['data_nascimento']).strip():
                try:
                    d_nasc = datetime.strptime(str(c['data_nascimento'])[:10], "%Y-%m-%d")
                    if d_nasc.month == mes_atual:
                        aniversariantes_mes.append((c['nome'], d_nasc.day, c['telefone']))
                except:
                    pass
    
    if aniversariantes_mes:
        st.markdown(f"🎂 **Aniversariantes de {nome_mes_atual}:**")
        for nome, dia, fone in sorted(aniversariantes_mes, key=lambda x: x[1]):
            st.caption(f"🎉 **{dia:02d}/{mes_atual:02d}** - {nome} ({fone or 'Sem telefone'})")
    else:
        st.caption(f"🎂 Nenhum aniversariante cadastrado em {nome_mes_atual}.")

# Cabeçalho Principal
st.markdown("""
<div class="brand-header">
    <div class="brand-title">Controle de Vendas, Estoque & Clientes Natura</div>
    <div class="brand-sub">Sistema integrado para acompanhamento de custos da Nota Fiscal, valores sugeridos do Catálogo/Revista, precificação personalizada e clientes.</div>
</div>
""", unsafe_allow_html=True)

# Abas de Navegação (100% em Português)
tab_dash, tab_estoque, tab_venda, tab_clientes, tab_novo, tab_historico, tab_simulador, tab_export = st.tabs([
    "📊 Visão Geral",
    "📋 Estoque & Preços",
    "🛍️ Registrar Venda",
    "👥 Clientes",
    "➕ Novo Produto",
    "📜 Histórico de Vendas",
    "💡 Simulador de Repasse",
    "📥 Planilha & Backup"
])

df_prod, df_vendas, df_clientes = load_data()

# ==========================================
# ABA 1: VISÃO GERAL (DASHBOARD)
# ==========================================
with tab_dash:
    if df_prod.empty:
        st.warning("Nenhum produto cadastrado no momento.")
    else:
        total_pago_investido = (df_prod['quantidade_comprada'] * df_prod['vl_unit_pago']).sum()
        total_revista_tabela = (df_prod['quantidade_comprada'] * df_prod['preco_revista']).sum()
        total_desconto_compra = (df_prod['quantidade_comprada'] * df_prod['desconto_compra_unit']).sum()
        
        total_faturado_real = df_vendas['vl_total_venda'].sum() if not df_vendas.empty else 0.0
        custo_produtos_vendidos = (df_vendas['quantidade'] * df_vendas['vl_unit_pago']).sum() if not df_vendas.empty else 0.0
        lucro_liquido_real = df_vendas['lucro_total'].sum() if not df_vendas.empty else 0.0
        lucro_projetado_estoque = ((df_prod['quantidade_estoque'] * (df_prod['vl_unit_venda_sugerida_final'] - df_prod['vl_unit_pago'])).sum())
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Investimento (Quanto Paguei)</div>
                <div class="metric-value metric-highlight-orange">{format_currency(total_pago_investido)}</div>
                <div class="metric-sub">Economia obtida na NF: {format_currency(total_desconto_compra)}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            margem_teorica = ((total_revista_tabela - total_pago_investido)/total_pago_investido*100) if total_pago_investido else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Valor de Revista (Catálogo)</div>
                <div class="metric-value metric-highlight-blue">{format_currency(total_revista_tabela)}</div>
                <div class="metric-sub">Potencial bruto: {margem_teorica:.1f}% de margem</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Vendas Realizadas (Faturado)</div>
                <div class="metric-value metric-highlight-green">{format_currency(total_faturado_real)}</div>
                <div class="metric-sub">{len(df_vendas)} venda(s) registrada(s)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c4:
            margem_efetiva = (lucro_liquido_real / custo_produtos_vendidos * 100) if custo_produtos_vendidos > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Lucro Líquido Realizado</div>
                <div class="metric-value metric-highlight-green">{format_currency(lucro_liquido_real)}</div>
                <div class="metric-sub">Margem média real: {margem_efetiva:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.info(f"💡 **Lucro Potencial Restante em Estoque:** {format_currency(lucro_projetado_estoque)}")
        with sc2:
            st.success(f"📦 **Itens Restantes para Vender:** {df_prod['quantidade_estoque'].sum()} de {df_prod['quantidade_comprada'].sum()} unidades")
        with sc3:
            recuperado_pct = (total_faturado_real / total_pago_investido * 100) if total_pago_investido > 0 else 0
            st.warning(f"🔄 **Recuperação do Investimento Inicial:** {recuperado_pct:.1f}% já recuperado")

        st.markdown("<br>", unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📊 Comparativo Financeiro Global")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=["Quanto Paguei", "Valor Revista (Tabela)", "Total Venda Efetiva", "Lucro Real"],
                y=[total_pago_investido, total_revista_tabela, total_faturado_real, lucro_liquido_real],
                marker_color=["#D84315", "#1976D2", "#2E7D32", "#388E3C"],
                text=[format_currency(total_pago_investido), format_currency(total_revista_tabela), format_currency(total_faturado_real), format_currency(lucro_liquido_real)],
                textposition='auto',
            ))
            fig_bar.update_layout(
                yaxis_title="Valores em Reais (R$)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=30, b=20),
                height=350
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.subheader("🛍️ Mix de Produtos por Categoria")
            cat_summary = df_prod.groupby('categoria').agg({
                'quantidade_comprada': 'sum',
                'vl_unit_pago': lambda x: (x * df_prod.loc[x.index, 'quantidade_comprada']).sum()
            }).reset_index()
            cat_summary.rename(columns={'vl_unit_pago': 'total_investido'}, inplace=True)
            
            fig_pie = px.pie(
                cat_summary,
                values='total_investido',
                names='categoria',
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=350
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# ABA 2: ESTOQUE, CATÁLOGO & PREÇOS (EDIÇÃO)
# ==========================================
with tab_estoque:
    st.subheader("📋 Catálogo de Produtos, Estoque & Edição de Preços")
    st.write("Você tem **total liberdade para editar**: a quantidade em estoque, o custo que pagou, o valor da revista, o desconto a repassar e o preço final de venda. Pode editar diretamente na tabela ou pelo formulário detalhado abaixo.")
    
    if df_prod.empty:
        st.info("Nenhum produto cadastrado no momento.")
    else:
        st.markdown("##### ⚡ Ações Rápidas de Precificação:")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("📖 Definir Preços = Valor Cheio da Revista", use_container_width=True):
                for _, row in df_prod.iterrows():
                    db.update_produto(row['id'], {
                        'desconto_repassado_unit': 0.0,
                        'vl_unit_venda_sugerida_final': float(row['preco_revista'])
                    })
                st.success("✅ Preços atualizados para o valor de catálogo da Revista!")
                st.rerun()
                
        with col_btn2:
            if st.button("🔥 Definir Preços = Promoções da Revista (Ciclo)", use_container_width=True):
                for _, row in df_prod.iterrows():
                    preco_aplicar = row['preco_revista_promo'] if pd.notna(row['preco_revista_promo']) and row['preco_revista_promo'] > 0 else row['preco_revista']
                    desc_rep = max(0.0, row['preco_revista'] - preco_aplicar)
                    db.update_produto(row['id'], {
                        'desconto_repassado_unit': float(desc_rep),
                        'vl_unit_venda_sugerida_final': float(preco_aplicar)
                    })
                st.success("✅ Preços promocionais da Revista aplicados aos itens em promoção!")
                st.rerun()
                
        with col_btn3:
            if st.button("🎯 Repassar 30% do Desconto ao Cliente", use_container_width=True):
                for _, row in df_prod.iterrows():
                    desc_rep = round(row['desconto_compra_unit'] * 0.30, 2)
                    vl_venda = round(row['preco_revista'] - desc_rep, 2)
                    db.update_produto(row['id'], {
                        'desconto_repassado_unit': float(desc_rep),
                        'vl_unit_venda_sugerida_final': float(vl_venda)
                    })
                st.success("✅ Desconto de 30% repassado aos clientes em todos os produtos!")
                st.rerun()

        # Formulário para Edição Individual
        with st.expander("✏️ Editar Produto Específico (Formulário Completo)", expanded=False):
            prod_edit_options = {f"[{p['codigo']}] {p['descricao']} (Estoque: {p['quantidade_estoque']} un)": p for p in db.get_produtos()}
            sel_edit_label = st.selectbox("Selecione o Produto para Editar:", list(prod_edit_options.keys()))
            p_to_edit = prod_edit_options[sel_edit_label]
            
            with st.form("form_editar_produto_detalhe"):
                ed_c1, ed_c2 = st.columns(2)
                with ed_c1:
                    ed_codigo = st.text_input("Código do Produto:", value=p_to_edit['codigo'])
                    ed_descricao = st.text_input("Descrição / Nome do Produto:", value=p_to_edit['descricao'])
                    categorias_lista = [
                        "Perfumaria Masculina", "Perfumaria Feminina", "Sabonetes", 
                        "Hidratantes Corporais", "Óleos Corporais", "Cuidados para Mãos", 
                        "Cabelos", "Infantil", "Mamãe e Bebê", "Desodorantes", "Maquiagem", "Outros"
                    ]
                    cat_idx = categorias_lista.index(p_to_edit['categoria']) if p_to_edit['categoria'] in categorias_lista else 0
                    ed_cat = st.selectbox("Categoria:", categorias_lista, index=cat_idx)
                    ed_estoque = st.number_input("Quantidade em Estoque (unidades):", min_value=0, value=int(p_to_edit['quantidade_estoque']), step=1)
                with ed_c2:
                    ed_pago = st.number_input("Quanto Paguei (Custo Líquido Unitário R$):", min_value=0.0, value=float(p_to_edit['vl_unit_pago']), step=1.0)
                    ed_revista = st.number_input("Valor da Revista / Catálogo (R$):", min_value=0.0, value=float(p_to_edit['preco_revista']), step=1.0)
                    ed_desc_rep = st.number_input("Desconto a Repassar ao Cliente (R$):", min_value=0.0, value=float(p_to_edit['desconto_repassado_unit']), step=1.0)
                    ed_venda = st.number_input("Preço de Venda Praticado (R$):", min_value=0.0, value=float(p_to_edit['vl_unit_venda_sugerida_final']), step=1.0)
                    
                ed_obs = st.text_input("Observações:", value=p_to_edit['observacoes'] or "")
                
                col_btn_save_ed, col_btn_del = st.columns([2, 1])
                with col_btn_save_ed:
                    btn_salvar_ind = st.form_submit_button("💾 Salvar Alterações deste Produto", type="primary", use_container_width=True)
                with col_btn_del:
                    btn_excluir_ind = st.form_submit_button("🗑️ Excluir Produto", type="secondary", use_container_width=True)

                if btn_salvar_ind:
                    db.update_produto(p_to_edit['id'], {
                        'codigo': ed_codigo.strip(),
                        'descricao': ed_descricao.strip(),
                        'categoria': ed_cat,
                        'quantidade_estoque': int(ed_estoque),
                        'vl_unit_pago': float(ed_pago),
                        'preco_revista': float(ed_revista),
                        'desconto_repassado_unit': float(ed_desc_rep),
                        'vl_unit_venda_sugerida_final': float(ed_venda),
                        'observacoes': ed_obs.strip()
                    })
                    st.success(f"✅ Produto '{ed_descricao}' atualizado com sucesso!")
                    st.rerun()

                if btn_excluir_ind:
                    db.delete_produto(p_to_edit['id'])
                    st.warning(f"🗑️ Produto '{p_to_edit['descricao']}' excluído!")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📝 Edição Rápida em Massa na Tabela:")
        st.markdown("💡 *Altere **Descrição**, **Estoque**, **Quanto Paguei**, **Valor Revista**, **Desconto Repassado** e **Preço Praticado** diretamente nas células da tabela. Quando terminar, clique no botão verde para salvar tudo!*")

        fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
        with fcol1:
            filtro_busca = st.text_input("🔍 Buscar por Código ou Nome do Produto:", placeholder="Ex: Tododia, Kaiak, Essencial, 2832...")
        with fcol2:
            cats = ["Todas"] + sorted(df_prod['categoria'].unique().tolist())
            filtro_cat = st.selectbox("Filtrar por Categoria:", cats)
        with fcol3:
            filtro_status = st.selectbox("Status de Estoque:", ["Todos", "Apenas Disponíveis", "Esgotados"])
            
        df_filtered = df_prod.copy()
        if filtro_busca:
            df_filtered = df_filtered[
                df_filtered['descricao'].str.contains(filtro_busca, case=False, na=False) |
                df_filtered['codigo'].str.contains(filtro_busca, case=False, na=False) |
                df_filtered['nome_revista'].str.contains(filtro_busca, case=False, na=False)
            ]
        if filtro_cat != "Todas":
            df_filtered = df_filtered[df_filtered['categoria'] == filtro_cat]
        if filtro_status == "Apenas Disponíveis":
            df_filtered = df_filtered[df_filtered['quantidade_estoque'] > 0]
        elif filtro_status == "Esgotados":
            df_filtered = df_filtered[df_filtered['quantidade_estoque'] == 0]

        df_filtered['lucro_unit_estimado'] = df_filtered['vl_unit_venda_sugerida_final'] - df_filtered['vl_unit_pago']
        df_filtered['margem_estimada_perc'] = (df_filtered['lucro_unit_estimado'] / df_filtered['vl_unit_pago'] * 100).round(1)

        cols_display = [
            'id', 'codigo', 'descricao', 'pagina_revista',
            'quantidade_estoque',
            'vl_unit_pago', 'preco_revista', 'preco_revista_promo',
            'desconto_compra_unit',
            'desconto_repassado_unit', 'vl_unit_venda_sugerida_final',
            'lucro_unit_estimado', 'margem_estimada_perc'
        ]
        
        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "codigo": st.column_config.TextColumn("Código", disabled=True, width="small"),
            "descricao": st.column_config.TextColumn("Produto (Editável ✏️)", disabled=False, width="large"),
            "pagina_revista": st.column_config.NumberColumn("Pág. Revista", disabled=True, format="Pág. %d", help="Página correspondente no Catalogo.pdf"),
            "quantidade_estoque": st.column_config.NumberColumn("Em Estoque (Editável ✏️)", disabled=False, min_value=0, step=1, format="%d un"),
            "vl_unit_pago": st.column_config.NumberColumn("Quanto Paguei (Editável ✏️)", disabled=False, min_value=0.0, step=1.0, format="R$ %.2f", help="Custo líquido unitário na Nota Fiscal"),
            "preco_revista": st.column_config.NumberColumn("Valor Revista (Editável ✏️)", disabled=False, min_value=0.0, step=1.0, format="R$ %.2f", help="Preço regular de catálogo da Revista"),
            "preco_revista_promo": st.column_config.NumberColumn("Promoção Revista", disabled=True, format="R$ %.2f", help="Preço promocional divulgado no catálogo deste ciclo"),
            "desconto_compra_unit": st.column_config.NumberColumn("Desconto NF", disabled=True, format="R$ %.2f", help="Desconto unitário que você obteve na compra"),
            "desconto_repassado_unit": st.column_config.NumberColumn(
                "Desconto a Repassar (Editável ✏️)", 
                disabled=False,
                help="Desconto que você decide conceder ao seu cliente (R$)",
                min_value=0.0,
                step=1.0,
                format="R$ %.2f"
            ),
            "vl_unit_venda_sugerida_final": st.column_config.NumberColumn(
                "Preço Venda Praticado (Editável ✏️)", 
                disabled=False,
                help="Preço final praticado por você na venda",
                min_value=0.0,
                step=1.0,
                format="R$ %.2f"
            ),
            "lucro_unit_estimado": st.column_config.NumberColumn("Seu Lucro", disabled=True, format="R$ %.2f"),
            "margem_estimada_perc": st.column_config.NumberColumn("Margem %", disabled=True, format="%.1f%%")
        }

        edited_df = st.data_editor(
            df_filtered[cols_display],
            column_config=column_config,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            key="produtos_editor"
        )

        col_save, col_info = st.columns([1, 3])
        with col_save:
            if st.button("💾 Salvar Alterações na Tabela", type="primary", use_container_width=True):
                updated_count = 0
                for _, row in edited_df.iterrows():
                    p_id = int(row['id'])
                    db.update_produto(p_id, {
                        'descricao': str(row['descricao']).strip(),
                        'quantidade_estoque': int(row['quantidade_estoque']),
                        'vl_unit_pago': float(row['vl_unit_pago']),
                        'preco_revista': float(row['preco_revista']),
                        'desconto_repassado_unit': float(row['desconto_repassado_unit']),
                        'vl_unit_venda_sugerida_final': float(row['vl_unit_venda_sugerida_final'])
                    })
                    updated_count += 1
                st.success(f"✅ {updated_count} produto(s) atualizado(s) com sucesso!")
                st.rerun()

# ==========================================
# ABA 3: REGISTRAR VENDA (PDV)
# ==========================================
with tab_venda:
    st.subheader("🛍️ Registrar Venda Rápida")
    st.write("Selecione o produto e o cliente (com preenchimento automático de telefone, e-mail e data de nascimento), confirme o preço vendido e dê baixa no estoque.")
    
    # Exibir mensagem de sucesso caso uma venda tenha acabado de ser registrada
    if 'ultima_venda_msg' in st.session_state and st.session_state['ultima_venda_msg']:
        st.markdown(f"""
        <div class="success-sale-banner">
            {st.session_state['ultima_venda_msg']}
        </div>
        """, unsafe_allow_html=True)
        # Limpar para a próxima
        st.session_state['ultima_venda_msg'] = None

    prods_disponiveis = [p for p in db.get_produtos() if p['quantidade_estoque'] > 0]
    
    if not prods_disponiveis:
        st.warning("⚠️ Não há produtos disponíveis no estoque no momento.")
    else:
        prod_options = {
            f"[{p['codigo']}] {p['descricao']} (Estoque: {p['quantidade_estoque']} un) - Revista: {format_currency(p['preco_revista'])}": p
            for p in prods_disponiveis
        }
        
        col_v1, col_v2 = st.columns([2, 1])
        
        with col_v1:
            selected_label = st.selectbox("Selecione o Produto:", list(prod_options.keys()), key="venda_sel_prod")
            prod_sel = prod_options[selected_label]
            
            pag_info = f"Pág. {prod_sel['pagina_revista']}" if prod_sel['pagina_revista'] else "Catálogo Geral"
            promo_info = f"🔥 **Preço Promocional no Catálogo:** {format_currency(prod_sel['preco_revista_promo'])}" if prod_sel['preco_revista_promo'] else "🔹 Sem promoção especial neste ciclo"
            
            st.info(f"""
            📌 **Dados do Catálogo & Custos:**
            - **Localização na Revista:** {pag_info} | **Nome:** {prod_sel['nome_revista'] or prod_sel['descricao']}
            - **📖 Preço de Revista (Catálogo):** {format_currency(prod_sel['preco_revista'])}
            - {promo_info}
            - **💵 Custo (Quanto Você Pagou na NF):** {format_currency(prod_sel['vl_unit_pago'])}
            """)
            
            st.markdown("#### 👤 Dados do Cliente:")
            lista_clientes = db.get_clientes()
            cli_dict = {f"{c['nome']} ({c['telefone'] or 'Sem telefone'})": c for c in lista_clientes}
            opcoes_cli = ["-- Selecionar Cliente Existente --", "➕ Cadastrar Novo Cliente"] + list(cli_dict.keys())
            
            escolha_cli = st.selectbox("Cliente:", opcoes_cli, key="venda_escolha_cli")
            
            default_nome = ""
            default_fone = ""
            default_email = ""
            default_nasc = None
            sel_cliente_id = None
            
            if escolha_cli not in ["-- Selecionar Cliente Existente --", "➕ Cadastrar Novo Cliente"]:
                c_sel = cli_dict[escolha_cli]
                sel_cliente_id = c_sel['id']
                default_nome = c_sel['nome']
                default_fone = c_sel['telefone'] or ""
                default_email = c_sel['email'] or ""
                if c_sel['data_nascimento']:
                    try:
                        default_nasc = datetime.strptime(str(c_sel['data_nascimento'])[:10], "%Y-%m-%d").date()
                    except:
                        default_nasc = None

            c_cli1, c_cli2 = st.columns(2)
            with c_cli1:
                cliente_nome = st.text_input("Nome do Cliente *:", value=default_nome, placeholder="Ex: Ana Paula Ribeiro", key="venda_cli_nome")
                cliente_fone = st.text_input("Telefone / WhatsApp:", value=default_fone, placeholder="Ex: (11) 98765-4321", key="venda_cli_fone")
            with c_cli2:
                cliente_email = st.text_input("E-mail:", value=default_email, placeholder="Ex: anapaula@email.com", key="venda_cli_email")
                cliente_nasc = st.date_input(
                    "Data de Nascimento (opcional):",
                    value=default_nasc,
                    min_value=date(1930, 1, 1),
                    max_value=date.today(),
                    key="venda_cli_nasc"
                )

            st.markdown("#### 💰 Valores & Condições da Venda:")
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                qtd_venda = st.number_input(
                    "Quantidade Vendida:", 
                    min_value=1, 
                    max_value=prod_sel['quantidade_estoque'], 
                    value=1, 
                    step=1,
                    key="venda_qtd"
                )
            with v_col2:
                vl_venda_real = st.number_input(
                    "Valor Unitário Efetivo de Venda (R$):",
                    min_value=0.0,
                    value=float(prod_sel['vl_unit_venda_sugerida_final']),
                    step=1.0,
                    help="O valor que você de fato combinou ou cobrou do cliente",
                    key="venda_vl_unit"
                )
                
            v_col3, v_col4 = st.columns(2)
            with v_col3:
                forma_pagto = st.selectbox(
                    "Forma de Pagamento:",
                    ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "A Prazo / Fiado", "Outro"],
                    key="venda_forma_pagto"
                )
            with v_col4:
                status_pagto = st.selectbox("Status do Pagamento:", ["Recebido", "Pendente"], key="venda_status_pagto")
                
            v_col5, v_col6 = st.columns(2)
            with v_col5:
                data_venda = st.date_input("Data da Venda:", value=date.today(), key="venda_data")
            with v_col6:
                obs_venda = st.text_input("Observações (opcional):", placeholder="Ex: Pediu embrulho para presente", key="venda_obs")

        with col_v2:
            st.markdown("### 💰 Resumo da Venda")
            
            total_venda = qtd_venda * vl_venda_real
            custo_total = qtd_venda * prod_sel['vl_unit_pago']
            lucro_venda = total_venda - custo_total
            margem_pct = (lucro_venda / custo_total * 100) if custo_total > 0 else 0
            desconto_dado = max(0.0, (prod_sel['preco_revista'] - vl_venda_real))
            
            st.markdown(f"""
            <div style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid #ddd; margin-top: 10px;">
                <p><strong>Total da Venda:</strong> <span style="font-size: 18px; color: #2e7d32; font-weight: bold;">{format_currency(total_venda)}</span></p>
                <p><strong>Valor Revista (Catálogo):</strong> {format_currency(prod_sel['preco_revista'] * qtd_venda)}</p>
                <p><strong>Custo Total (Você pagou):</strong> {format_currency(custo_total)}</p>
                <p><strong>Desconto Concedido:</strong> {format_currency(desconto_dado * qtd_venda)} ({format_currency(desconto_dado)}/un)</p>
                <hr>
                <p><strong>Seu Lucro Líquido:</strong> <span style="font-size: 20px; color: #d84315; font-weight: bold;">{format_currency(lucro_venda)}</span></p>
                <p><strong>Margem de Lucro:</strong> <span style="font-size: 16px; font-weight: bold;">{margem_pct:.1f}%</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Confirmar e Finalizar Venda", type="primary", use_container_width=True, key="btn_confirmar_venda"):
                if not cliente_nome or not cliente_nome.strip():
                    cliente_nome = "Consumidor"
                    
                nasc_str = cliente_nasc.strftime("%Y-%m-%d") if cliente_nasc else ""
                
                try:
                    db.registrar_venda(
                        produto_id=prod_sel['id'],
                        qtd_venda=qtd_venda,
                        vl_unit_venda=vl_venda_real,
                        desconto_repassado_unit=desconto_dado,
                        cliente=cliente_nome.strip(),
                        forma_pagamento=forma_pagto,
                        status_pagamento=status_pagto,
                        data_venda=data_venda.strftime("%Y-%m-%d"),
                        observacoes=obs_venda,
                        cliente_id=sel_cliente_id,
                        cliente_telefone=cliente_fone.strip(),
                        cliente_email=cliente_email.strip(),
                        cliente_nascimento=nasc_str
                    )
                    st.session_state['ultima_venda_msg'] = f"🎉 Venda de <strong>{qtd_venda}x '{prod_sel['descricao']}'</strong> para <strong>'{cliente_nome}'</strong> no valor de <strong>{format_currency(total_venda)}</strong> (Lucro: {format_currency(lucro_venda)}) registrada com sucesso!"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar venda: {e}")

    # Exibir tabela com as últimas vendas logo abaixo na própria aba de vendas
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("#### 📋 Vendas Registradas:")
    df_ultimas_vendas = pd.DataFrame(db.get_vendas())
    if df_ultimas_vendas.empty:
        st.caption("Nenhuma venda registrada até o momento.")
    else:
        st.dataframe(
            df_ultimas_vendas[['id', 'data_venda', 'cliente', 'cliente_telefone', 'descricao', 'quantidade', 'vl_unit_venda', 'vl_total_venda', 'lucro_total', 'forma_pagamento', 'status_pagamento']],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "data_venda": st.column_config.TextColumn("Data"),
                "cliente": st.column_config.TextColumn("Cliente"),
                "cliente_telefone": st.column_config.TextColumn("Telefone"),
                "descricao": st.column_config.TextColumn("Produto"),
                "quantidade": st.column_config.NumberColumn("Qtd", format="%d un"),
                "vl_unit_venda": st.column_config.NumberColumn("Preço Unit.", format="R$ %.2f"),
                "vl_total_venda": st.column_config.NumberColumn("Total Recebido", format="R$ %.2f"),
                "lucro_total": st.column_config.NumberColumn("Lucro Líquido", format="R$ %.2f"),
                "forma_pagamento": st.column_config.TextColumn("Pagamento"),
                "status_pagamento": st.column_config.TextColumn("Status")
            },
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# ABA 4: GESTÃO DE CLIENTES
# ==========================================
with tab_clientes:
    st.subheader("👥 Cadastro & Gestão de Clientes")
    st.write("Gerencie os dados dos seus clientes para controle de vendas, fidelização, contato direto via WhatsApp e lembretes de aniversário!")
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total de Clientes", f"{len(df_clientes)} cadastrados")
    with m2:
        tot_gasto = df_clientes['valor_total_gasto'].sum() if not df_clientes.empty else 0.0
        st.metric("Total Faturado com Clientes", format_currency(tot_gasto))
    with m3:
        st.metric("Aniversariantes do Mês", f"{len(aniversariantes_mes)} clientes")

    st.markdown("<br>", unsafe_allow_html=True)

    if aniversariantes_mes:
        st.markdown(f"#### 🎂 Aniversariantes de {nome_mes_atual}:")
        col_b1, col_b2 = st.columns(2)
        for idx, (nome, dia, fone) in enumerate(sorted(aniversariantes_mes, key=lambda x: x[1])):
            target_col = col_b1 if idx % 2 == 0 else col_b2
            with target_col:
                wa_link = f"https://wa.me/55{re.sub(r'\\D', '', fone)}" if fone and len(re.sub(r'\D', '', fone)) >= 10 else None
                wa_btn = f"[📲 Enviar Mensagem no WhatsApp]({wa_link})" if wa_link else "*(Sem WhatsApp cadastrado)*"
                st.markdown(f"""
                <div class="bday-card">
                    <strong>🎉 {dia:02d}/{mes_atual:02d} - {nome}</strong><br>
                    <span>Telefone: {fone or 'Não informado'}</span><br>
                    {wa_btn}
                </div>
                """, unsafe_allow_html=True)

    with st.expander("➕ Cadastrar Novo Cliente", expanded=(len(df_clientes) == 0)):
        with st.form("form_novo_cliente", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                cad_nome = st.text_input("Nome Completo *:", placeholder="Ex: Mariana Ferreira")
                cad_fone = st.text_input("Telefone / Celular (WhatsApp) *:", placeholder="Ex: (11) 98765-4321")
            with fc2:
                cad_email = st.text_input("E-mail:", placeholder="Ex: mariana@email.com")
                cad_nasc = st.date_input(
                    "Data de Nascimento:", 
                    value=None, 
                    min_value=date(1930, 1, 1), 
                    max_value=date.today()
                )
            cad_obs = st.text_input("Preferências / Observações:", placeholder="Ex: Gosta de hidratantes florais e perfumes amadeirados")
            
            sub_cli = st.form_submit_button("💾 Salvar Cliente", type="primary")
            if sub_cli:
                if not cad_nome or not cad_nome.strip():
                    st.error("Por favor, preencha o Nome do cliente.")
                else:
                    nasc_str = cad_nasc.strftime("%Y-%m-%d") if cad_nasc else ""
                    db.add_cliente(
                        nome=cad_nome.strip(),
                        telefone=cad_fone.strip(),
                        email=cad_email.strip(),
                        data_nascimento=nasc_str,
                        observacoes=cad_obs.strip()
                    )
                    st.success(f"✅ Cliente '{cad_nome}' cadastrado com sucesso!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if not df_clientes.empty:
        st.markdown("#### 📋 Lista de Clientes:")
        
        filtro_cli = st.text_input("🔍 Buscar Cliente por Nome, Telefone ou E-mail:", placeholder="Ex: Maria, 98765...")
        df_c_filtro = df_clientes.copy()
        if filtro_cli:
            df_c_filtro = df_c_filtro[
                df_c_filtro['nome'].str.contains(filtro_cli, case=False, na=False) |
                df_c_filtro['telefone'].str.contains(filtro_cli, case=False, na=False) |
                df_c_filtro['email'].str.contains(filtro_cli, case=False, na=False)
            ]

        df_c_filtro['data_nasc_formatada'] = df_c_filtro['data_nascimento'].apply(format_date_br)
        df_c_filtro['ultima_compra_formatada'] = df_c_filtro['ultima_compra'].apply(format_date_br)
        
        cols_cli_view = ['id', 'nome', 'telefone', 'email', 'data_nasc_formatada', 'total_compras', 'valor_total_gasto', 'ultima_compra_formatada', 'observacoes']
        
        st.dataframe(
            df_c_filtro[cols_cli_view],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "nome": st.column_config.TextColumn("Nome do Cliente", width="medium"),
                "telefone": st.column_config.TextColumn("Telefone / WhatsApp"),
                "email": st.column_config.TextColumn("E-mail"),
                "data_nasc_formatada": st.column_config.TextColumn("Data de Nascimento 🎂"),
                "total_compras": st.column_config.NumberColumn("Compras Realizadas", format="%d"),
                "valor_total_gasto": st.column_config.NumberColumn("Total Gasto", format="R$ %.2f"),
                "ultima_compra_formatada": st.column_config.TextColumn("Última Compra"),
                "observacoes": st.column_config.TextColumn("Observações / Preferências")
            },
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# ABA 5: NOVO PRODUTO (INSERÇÃO MANUAL)
# ==========================================
with tab_novo:
    st.subheader("➕ Inserir Novo Produto")
    st.write("Adicione novos produtos com preço de custo, preço sugerido no catálogo e preço planejado de venda.")
    
    with st.form("form_novo_produto", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            novo_codigo = st.text_input("Código do Produto *:", placeholder="Ex: 123456")
            novo_desc = st.text_input("Descrição / Nome do Produto *:", placeholder="Ex: EKOS CASTANHA POLPA HIDRATANTE 400ML")
            novo_cat = st.selectbox("Categoria:", [
                "Perfumaria Masculina",
                "Perfumaria Feminina",
                "Sabonetes",
                "Hidratantes Corporais",
                "Óleos Corporais",
                "Cuidados para Mãos",
                "Cabelos",
                "Infantil",
                "Mamãe e Bebê",
                "Desodorantes",
                "Maquiagem",
                "Outros"
            ])
            novo_unidade = st.selectbox("Unidade:", ["UN", "PC", "CX", "KIT"])
            novo_qtd = st.number_input("Quantidade Comprada *:", min_value=1, value=1, step=1)
            novo_pag_rev = st.number_input("Página no Catálogo (opcional):", min_value=1, max_value=250, value=1, step=1)
            
        with col_n2:
            novo_sugerido = st.number_input("Valor de Revista / Sugerido (R$) *:", min_value=0.0, value=50.0, step=1.0)
            novo_pago = st.number_input("Quanto Paguei (Custo Líquido R$) *:", min_value=0.0, value=25.0, step=1.0)
            desc_compra_calc = max(0.0, novo_sugerido - novo_pago)
            novo_desc_compra = st.number_input("Desconto Obtido na Compra (R$):", min_value=0.0, value=float(desc_compra_calc), step=1.0)
            novo_desc_repassar = st.number_input("Desconto que Deseja Repassar (R$):", min_value=0.0, value=0.0, step=1.0)
            novo_venda_planejada = st.number_input("Preço de Venda Praticado (R$):", min_value=0.0, value=float(novo_sugerido - novo_desc_repassar), step=1.0)
            
        novo_obs = st.text_input("Observações (opcional):", placeholder="Ex: Adquirido no ciclo 19")
        
        submitted = st.form_submit_button("💾 Cadastrar Produto no Estoque", type="primary")
        if submitted:
            if not novo_codigo or not novo_desc:
                st.error("Por favor, preencha o Código e a Descrição do produto.")
            else:
                db.add_produto(
                    codigo=novo_codigo.strip(),
                    descricao=novo_desc.strip(),
                    categoria=novo_cat,
                    unidade=novo_unidade,
                    qtd=novo_qtd,
                    vl_sugerido=novo_sugerido,
                    vl_pago=novo_pago,
                    desconto_compra=novo_desc_compra,
                    desconto_repassado=novo_desc_repassar,
                    vl_venda=novo_venda_planejada,
                    observacoes=novo_obs
                )
                prods_updated = db.get_produtos()
                last_p = prods_updated[-1]
                db.update_produto(last_p['id'], {'pagina_revista': novo_pag_rev, 'preco_revista': novo_sugerido})
                st.success(f"✅ Produto '{novo_desc}' cadastrado com sucesso com estoque de {novo_qtd} unidades!")
                st.rerun()

# ==========================================
# ABA 6: HISTÓRICO DE VENDAS
# ==========================================
with tab_historico:
    st.subheader("📜 Histórico de Vendas Realizadas")
    
    if df_vendas.empty:
        st.info("Nenhuma venda realizada ainda. Use a aba '🛍️ Registrar Venda' para lançar sua primeira venda!")
    else:
        tot_vendas_count = len(df_vendas)
        tot_faturado = df_vendas['vl_total_venda'].sum()
        tot_lucro = df_vendas['lucro_total'].sum()
        
        h1, h2, h3 = st.columns(3)
        h1.metric("Total de Pedidos", f"{tot_vendas_count} vendas")
        h2.metric("Total Faturado", format_currency(tot_faturado))
        h3.metric("Lucro Líquido Real", format_currency(tot_lucro))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_v_display = df_vendas.copy()
        cols_v = [
            'id', 'data_venda', 'cliente', 'cliente_telefone', 'codigo', 'descricao', 
            'quantidade', 'vl_unit_pago', 'vl_unit_venda', 
            'vl_total_venda', 'lucro_total', 'forma_pagamento', 'status_pagamento'
        ]
        
        st.dataframe(
            df_v_display[cols_v],
            column_config={
                "id": st.column_config.NumberColumn("ID Venda", width="small"),
                "data_venda": st.column_config.TextColumn("Data"),
                "cliente": st.column_config.TextColumn("Cliente", width="medium"),
                "cliente_telefone": st.column_config.TextColumn("Telefone"),
                "codigo": st.column_config.TextColumn("Código"),
                "descricao": st.column_config.TextColumn("Produto", width="large"),
                "quantidade": st.column_config.NumberColumn("Qtd", format="%d"),
                "vl_unit_pago": st.column_config.NumberColumn("Custo Unitário", format="R$ %.2f"),
                "vl_unit_venda": st.column_config.NumberColumn("Preço Venda Unitário", format="R$ %.2f"),
                "vl_total_venda": st.column_config.NumberColumn("Total Recebido", format="R$ %.2f"),
                "lucro_total": st.column_config.NumberColumn("Lucro Líquido", format="R$ %.2f"),
                "forma_pagamento": st.column_config.TextColumn("Forma de Pagamento"),
                "status_pagamento": st.column_config.TextColumn("Status")
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        st.write("#### ↩️ Cancelar / Estornar Venda")
        c_cancel1, c_cancel2 = st.columns([2, 1])
        with c_cancel1:
            venda_ids = df_vendas['id'].tolist()
            venda_sel_id = st.selectbox(
                "Selecione a Venda para Cancelar:", 
                venda_ids, 
                format_func=lambda x: f"Venda #{x} - {df_vendas[df_vendas['id']==x]['descricao'].values[0]} ({df_vendas[df_vendas['id']==x]['quantidade'].values[0]} un) - {format_currency(df_vendas[df_vendas['id']==x]['vl_total_venda'].values[0])}"
            )
        with c_cancel2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❌ Confirmar Estorno da Venda", type="secondary"):
                db.cancelar_venda(venda_sel_id)
                st.success(f"Venda #{venda_sel_id} cancelada e produto devolvido ao estoque com sucesso!")
                st.rerun()

# ==========================================
# ABA 7: SIMULADOR DE REPASSE DE DESCONTO
# ==========================================
with tab_simulador:
    st.subheader("💡 Simulador de Estratégia de Preços & Repasse de Desconto")
    st.write("""
    Na sua compra da Nota Fiscal, você obteve **R$ 2.111,00 de desconto** sobre o preço de catálogo da Natura.
    Simule abaixo diferentes estratégias de precificação para seus clientes:
    """)
    
    col_sim1, col_sim2 = st.columns([1, 1])
    
    with col_sim1:
        st.markdown("#### 🎯 Cenário de Repasse de Desconto:")
        perc_repasse = st.slider(
            "Percentual do desconto da compra a repassar (%):",
            min_value=0,
            max_value=100,
            value=25,
            step=5,
            help="0% = Preço cheio da revista (lucro máximo). 50% = Divide o desconto com o cliente."
        )
        
        st.info(f"""
        **Neste cenário de {perc_repasse}% de repasse:**
        - O cliente recebe {perc_repasse}% de desconto em relação ao preço da Revista.
        - Você retém **{100 - perc_repasse}%** do desconto obtido como margem de lucro líquido!
        """)
        
    with col_sim2:
        st.markdown("#### 📈 Projeção do Estoque Atual:")
        df_sim = df_prod.copy()
        
        df_sim['sim_desconto_repassado'] = (df_sim['desconto_compra_unit'] * (perc_repasse / 100.0)).round(2)
        df_sim['sim_preco_venda'] = df_sim['preco_revista'] - df_sim['sim_desconto_repassado']
        df_sim['sim_lucro_unit'] = df_sim['sim_preco_venda'] - df_sim['vl_unit_pago']
        df_sim['sim_lucro_total'] = df_sim['sim_lucro_unit'] * df_sim['quantidade_estoque']
        df_sim['sim_faturamento_total'] = df_sim['sim_preco_venda'] * df_sim['quantidade_estoque']
        
        sim_faturado = df_sim['sim_faturamento_total'].sum()
        sim_lucro = df_sim['sim_lucro_total'].sum()
        custo_estoque = (df_sim['vl_unit_pago'] * df_sim['quantidade_estoque']).sum()
        sim_margem = (sim_lucro / custo_estoque * 100) if custo_estoque > 0 else 0
        
        s1, s2 = st.columns(2)
        s1.metric("Faturamento Projetado", format_currency(sim_faturado))
        s2.metric("Lucro Líquido Projetado", format_currency(sim_lucro), delta=f"{sim_margem:.1f}% de margem")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("#### 🔍 Prévia dos Preços Praticados neste Cenário:")
    
    col_sim_t = ['codigo', 'descricao', 'pagina_revista', 'vl_unit_pago', 'preco_revista', 'sim_desconto_repassado', 'sim_preco_venda', 'sim_lucro_unit']
    st.dataframe(
        df_sim[col_sim_t].head(10),
        column_config={
            "codigo": "Código",
            "descricao": "Produto",
            "pagina_revista": st.column_config.NumberColumn("Pág. Revista", format="Pág. %d"),
            "vl_unit_pago": st.column_config.NumberColumn("Quanto Paguei", format="R$ %.2f"),
            "preco_revista": st.column_config.NumberColumn("Valor Revista", format="R$ %.2f"),
            "sim_desconto_repassado": st.column_config.NumberColumn("Desconto Repassado", format="R$ %.2f"),
            "sim_preco_venda": st.column_config.NumberColumn("Preço Final Venda", format="R$ %.2f"),
            "sim_lucro_unit": st.column_config.NumberColumn("Seu Lucro", format="R$ %.2f"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(f"⚡ Aplicar esse Repasse de {perc_repasse}% em Todos os Produtos do Estoque", type="primary"):
        for _, row in df_sim.iterrows():
            db.update_produto(row['id'], {
                'desconto_repassado_unit': float(row['sim_desconto_repassado']),
                'vl_unit_venda_sugerida_final': float(row['sim_preco_venda'])
            })
        st.success(f"🚀 Todos os produtos foram atualizados com {perc_repasse}% de desconto repassado aos clientes!")
        st.rerun()

# ==========================================
# ABA 8: PLANILHA & BACKUP
# ==========================================
with tab_export:
    st.subheader("📥 Integração com Planilha Google & Exportação de Dados")
    
    # Seção Google Sheets
    st.markdown("### 🌐 Base de Dados no Google Sheets")
    st.write("A sua aplicação está configurada para conectar diretamente com a sua planilha do Google Drive:")
    st.markdown(f"🔗 **Link da sua Planilha:** [{sheets_sync.GOOGLE_SHEET_URL}]({sheets_sync.GOOGLE_SHEET_URL})")
    
    is_ok, msg_status, row_count = sheets_sync.check_google_sheet_status()
    if is_ok and row_count and row_count > 0:
        st.success(f"🟢 {msg_status}")
    else:
        st.info(f"ℹ️ **Status da Planilha:** A planilha está acessível, mas ainda não possui linhas preenchidas.")
        st.markdown("""
        **Como alimentar sua planilha no Google Sheets em 3 passos:**
        1. Clique no botão abaixo **'📥 Baixar Planilha Base para Google Sheets (.xlsx)'**.
        2. Abra a sua planilha no Google: [Abrir Google Sheets](https://docs.google.com/spreadsheets/d/1V84XN7tx2jicDcC4YDrMPwBrJFaa-a7z7dkFoCgDoNE/edit#gid=0).
        3. Vá no menu **Arquivo > Importar > Fazer upload**, selecione o arquivo baixado e escolha **'Substituir planilha'**.
        4. Pronto! Sempre que você atualizar valores na sua planilha Google, basta clicar no botão **'🔄 Sincronizar Agora com Google Sheets'**!
        """)

    col_gs1, col_gs2 = st.columns(2)
    with col_gs1:
        if st.button("🔄 Sincronizar Agora com Google Sheets", type="primary", use_container_width=True):
            sucesso, msg_sync = sheets_sync.sync_from_google_sheet()
            if sucesso:
                st.success(f"🎉 {msg_sync}")
                st.rerun()
            else:
                st.warning(f"Aviso: {msg_sync}")
                
    with col_gs2:
        try:
            with open("Base_Dados_Natura.xlsx", "rb") as f_base:
                base_bytes = f_base.read()
            st.download_button(
                label="📥 Baixar Planilha Base para Google Sheets (.xlsx)",
                data=base_bytes,
                file_name="Base_Dados_Natura.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except:
            pass

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚡ Gravação Automática e Direta no Google Sheets (Tempo Real)")
    st.info("💡 **Onde colar a URL:** Este campo abaixo fica **aqui no seu site**, na aba **'Planilha & Backup'**.")
    
    current_wh = sheets_sync.get_webhook_url()
    wh_input = st.text_input(
        "Cole aqui a URL do Webhook do Google Apps Script (terminada em /exec):",
        value=current_wh,
        placeholder="https://script.google.com/macros/s/.../exec",
        help="Cole a URL gerada no Google Apps Script após clicar em 'Implantar'"
    )
    
    col_wh1, col_wh2, col_wh3 = st.columns(3)
    with col_wh1:
        if st.button("💾 Salvar Webhook", type="primary", use_container_width=True):
            if wh_input and wh_input.strip():
                sheets_sync.set_webhook_url(wh_input)
                st.success("Salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Cole a URL antes de salvar.")
                
    with col_wh2:
        if st.button("🔍 Testar Conexão do Webhook", use_container_width=True):
            ok_teste, msg_teste = sheets_sync.testar_conexao_webhook()
            if ok_teste:
                st.success(f"✅ {msg_teste}")
            else:
                st.error(f"❌ {msg_teste}")
                
    with col_wh3:
        if st.button("📤 Enviar Dados Pendentes", use_container_width=True):
            ok_env, msg_env = sheets_sync.enviar_dados_pendentes()
            if ok_env:
                st.success(f"🎉 {msg_env}")
            else:
                st.error(f"Erro: {msg_env}")

    with st.expander("❓ Como gerar essa URL no Google Sheets (Passo a Passo)", expanded=(not bool(current_wh))):
        st.write("""
        1. Na sua planilha do Google, clique no menu superior em **Extensões > Apps Script**.
        2. Apague o código que estiver lá e cole o código que enviamos.
        3. Clique no botão azul **Implantar > Nova implantação**:
           - Tipo: **App da Web** (ícone de engrenagem)
           - Executar como: **Eu**
           - Quem pode acessar: **Qualquer pessoa**
           - Clique em **Implantar** e copie a URL gerada.
        4. Cole a URL copiada no campo branco logo acima e clique em **'Salvar Conexão com Google Sheets'**.
        """)

    st.divider()

    st.markdown("### 📤 Importar Planilha Local (.xlsx ou .csv)")
    st.write("Se preferir, você também pode subir um arquivo Excel ou CSV diretamente aqui para atualizar o estoque:")
    uploaded_file = st.file_uploader("Selecione um arquivo de planilha (.xlsx ou .csv):", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".xlsx"):
                df_up = pd.read_excel(uploaded_file)
            else:
                df_up = pd.read_csv(uploaded_file)
            st.write(f"Arquivo carregado com **{len(df_up)} linhas** e colunas: {list(df_up.columns[:6])}...")
            if st.button("💾 Importar Dados desta Planilha para a Aplicação"):
                with open("Base_Dados_Natura.xlsx", "wb") as f_up:
                    f_up.write(uploaded_file.getbuffer())
                st.success("✅ Planilha importada com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

    st.divider()

    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        st.markdown("#### 📊 Exportar Backup Completo")
        st.write("Baixe a planilha com as 3 abas completas: **Estoque_e_Precos**, **Historico_Vendas** e **Cadastro_Clientes**.")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_prod.to_excel(writer, sheet_name='Estoque_e_Precos', index=False)
            if not df_vendas.empty:
                df_vendas.to_excel(writer, sheet_name='Historico_Vendas', index=False)
            if not df_clientes.empty:
                df_clientes.to_excel(writer, sheet_name='Cadastro_Clientes', index=False)
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Baixar Backup em Excel (.xlsx)",
            data=excel_data,
            file_name=f"controle_vendas_natura_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
    with col_ex2:
        st.markdown("#### 🔄 Restaurar Dados Originais")
        st.write("Caso queira reiniciar o banco de dados com a lista original extraída da Nota Fiscal e Catálogo:")
        
        if st.button("⚠️ Reiniciar Banco com Dados Originais", type="secondary"):
            db.init_db(force_reseed=True)
            st.success("✅ Banco de dados redefinido com sucesso!")
            st.rerun()
