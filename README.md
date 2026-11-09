# 🛍️ Sistema de Controle de Vendas & Precificação Natura

Sistema web desenvolvido especialmente para gestão e precificação de produtos Natura, integrado com extração automática da **Nota Fiscal 05/11/2026** e suporte a novos cadastros.

---

## 📌 Funcionalidades Principais

1. **📊 Visão Geral & Métricas Financeiras:**
   - **Quanto Paguei:** Total investido na compra (R$ 992,00 na NF inicial).
   - **Venda Sugerida:** Potencial de faturamento com preços cheios de catálogo (R$ 3.103,00).
   - **O que de Fato Vendi:** Faturamento real acumulado das vendas realizadas.
   - **Lucro Líquido Realizado:** Lucro real que já entrou no bolso.
   - **Retorno do Investimento (ROI):** Acompanhamento do percentual do investimento inicial já recuperado.
   - Gráficos interativos por categoria e mix financeiro.

2. **📋 Estoque & Preços (Edição Direta e Flexível):**
   - Lista completa com todos os 38 produtos importados da nota fiscal.
   - Mostra: Código, Descrição, Categoria, Qtd em Estoque, Qtd Vendida, Preço Pago (Custo), Desconto Obtido na Compra, Preço Sugerido (Catálogo).
   - **Campos Editáveis:**
     - **Desconto a Repassar (R$):** você define quanto do seu desconto quer conceder para o cliente.
     - **Preço de Venda Praticado (R$):** você pode editar o preço final diretamente na tabela!
   - Botão para salvar alterações em lote com 1 clique.

3. **👥 Gestão Completa de Clientes:**
   - **Campos de Controle:** Nome Completo, Telefone / WhatsApp, E-mail e Data de Nascimento.
   - **🎂 Painel de Aniversariantes do Mês:** Destaque automático dos aniversariantes do mês atual com atalho direto para mandar mensagem de parabéns / promoção no WhatsApp (`wa.me`).
   - **Histórico por Cliente:** Total de pedidos, valor total gasto e data da última compra.
   - **Cadastro Integrado:** Você pode cadastrar clientes pela aba exclusiva ou diretamente durante o registro de uma nova venda sem sair da tela!

4. **🛍️ Registro Rápido de Venda (PDV):**
   - Seleção inteligente de clientes cadastrados (auto-preenche telefone, email e nascimento) ou criação de novo cliente na hora da venda.
   - Escolha o produto com auto-preenchimento de estoque, custo e preço de catálogo.
   - Cálculo instantâneo do lucro líquido e margem antes de confirmar a venda.
   - Baixa automática no estoque.

4. **➕ Cadastro de Novos Produtos:**
   - Formulário para inserir novos produtos comprados no futuro com:
     - Código
     - Nome / Descrição
     - Categoria
     - Quantidade
     - Valor que pagou (Custo)
     - Valor de venda sugerido (Catálogo)
     - Desconto da compra e desconto a repassar
     - Preço final planejado

5. **📜 Histórico de Vendas & Estorno:**
   - Lista detalhada de todas as vendas já realizadas.
   - Opção de estorno/cancelamento de venda com devolução automática das unidades ao estoque.

6. **💡 Simulador de Repasse de Desconto:**
   - Permite simular cenários de repasse (ex: repassar 10%, 20%, 30% ou 50% do desconto obtido).
   - Mostra na hora o faturamento projetado, lucro projetado e margem.
   - Botão para aplicar o percentual escolhido em todos os produtos do estoque de uma só vez!

7. **📥 Exportação & Backup:**
   - Download de planilha completa em **Excel (.xlsx)** com abas de Estoque e Vendas.
   - Opção para reiniciar o banco com os dados originais da Nota Fiscal caso necessário.

---

## 🚀 Como Iniciar o Sistema

### Opção 1: Atalho Rápido no Windows
Dê dois cliques no arquivo:
```
iniciar_sistema.bat
```

### Opção 2: Pelo Terminal
Abra o PowerShell ou Prompt de Comando na pasta do projeto e execute:
```powershell
python -m streamlit run app.py
```
O sistema abrirá automaticamente no seu navegador em `http://localhost:8501`.

---

## 🧾 Resumo dos Dados Importados da Nota Fiscal (05/11/2026)

- **Total de Itens Importados:** 38 itens (43 unidades no total)
- **Valor dos Itens (Preço Catálogo):** R$ 3.103,00
- **Desconto Obtido na Compra:** -R$ 2.111,00 (~68% de desconto)
- **Valor Total Pago (Investimento Líquido):** R$ 992,00
- **Forma de Pagamento Original:** Cartão de Crédito
