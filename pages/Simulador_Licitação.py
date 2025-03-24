import streamlit as st

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Licitações e Editais",
    page_icon="📜",
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #004aad;'>📜 Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Tabela de preços
precoCusto = {
    "Rastreador GPRS/GSM 2G": 300,
    "Rastreador GPRS/GSM 4G": 400,
    "Rastreador Satelital": 900,
    "Telemetria/CAN": 600,
    "RFID - ID Motorista": 153,
}

# 🎯 Sidebar para entrada de dados
st.sidebar.header("📝 Configurações")
qtd = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1)
contrato = st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=1, value=12, step=1)

# 📌 Margem de lucro
margem = st.sidebar.slider("Margem de Lucro (%) 📈", min_value=0.0, max_value=1.0, value=0.3, step=0.01, format="%.2f")

# 🔽 Seleção de itens (distribuídos em 2 colunas)
st.markdown("### 📦 Selecione os Itens:")
col1, col2 = st.columns(2)
itens_selecionados = []

for idx, (item, preco) in enumerate(precoCusto.items()):
    col = col1 if idx % 2 == 0 else col2
    if col.checkbox(f"{item} - R$ {preco:,.2f}"):
        itens_selecionados.append(item)

# 📌 Cálculo do valor total
if itens_selecionados:
    valor_total_unitario = sum(precoCusto[item] for item in itens_selecionados)
    un_contrato = valor_total_unitario / 12
    un_margem = un_contrato + (un_contrato * margem)
    valor_total = un_margem * qtd * contrato

    # 🔹 Exibição dos resultados
    st.success("✅ Cálculo realizado com sucesso!")
    st.info(f"💰 **Valor Unitário:** R$ {un_margem:,.2f}")
    st.info(f"📄 **Valor Total do Contrato:** R$ {valor_total:,.2f}")
    st.write(f"##### (considerando {qtd} veículos e {contrato} meses)")
else:
    st.warning("⚠️ Selecione pelo menos um item para calcular o valor total.")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()
