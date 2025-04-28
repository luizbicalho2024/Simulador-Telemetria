import streamlit as st
from decimal import Decimal, ROUND_DOWN

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Licitações e Editais",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Preços dos produtos
precoCusto = {
    "Rastreador GPRS/GSM 2G": Decimal("300"),
    "Rastreador GPRS/GSM 4G": Decimal("400"),
    "Rastreador Satelital": Decimal("900"),
    "Telemetria/CAN": Decimal("600"),
    "RFID - ID Motorista": Decimal("153"),
}

# 🎯 Sidebar para entrada de dados
st.sidebar.header("📝 Configurações")
qtd = Decimal(st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=1, value=12, step=1))

# 📈 Margem de lucro
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", min_value=0.0, max_value=1.0, value=0.3, step=0.01, format="%.2f")))

# 🔽 Seleção de itens
st.markdown("### 📦 Selecione os Itens:")
col1, col2 = st.columns(2)
itens_selecionados = []

for idx, (item, preco) in enumerate(precoCusto.items()):
    col = col1 if idx % 2 == 0 else col2
    with col:
        toggle = st.toggle(f"{item} - R$ {preco:,.2f}")
        if toggle:
            itens_selecionados.append(item)

# 📊 Cálculo do valor
if itens_selecionados:
    # Soma dos valores selecionados
    valor_total_sem_margem = sum(precoCusto[item] for item in itens_selecionados).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # Cálculo da margem em reais
    valor_margem = (valor_total_sem_margem * margem).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # Valor com margem aplicada
    valor_unitario_margem = (valor_total_sem_margem + valor_margem).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # Valor total considerando veículos e tempo de contrato
    valor_total = (valor_unitario_margem * qtd * contrato).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # 🔹 Exibição dos resultados detalhados
    st.success("✅ Cálculo realizado com sucesso!")
    st.markdown("### 📋 **Detalhamento dos Valores:**")
    st.info(f"🔹 **Valor Unitário (Sem Margem):** R$ {valor_total_sem_margem}")
    st.info(f"🔹 **Valor da Margem Aplicada:** R$ {valor_margem}")
    st.info(f"💰 **Valor Unitário com Margem:** R$ {valor_unitario_margem}")
    st.info(f"📄 **Valor Total do Contrato:** R$ {valor_total}")
    st.write(f"##### (considerando {qtd} veículos e {contrato} meses)")

else:
    st.warning("⚠️ Selecione pelo menos um item para calcular o valor total.")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()
