import streamlit as st

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide", 
    page_title="Simulador PJ", 
    page_icon="imgs/v-c.png", 
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Definição dos preços para cada plano
planos = {
    "12 Meses": {
        "GPRS / Gsm": 80.88,
        "Satélite": 193.80,
        "Identificador de Motorista / RFID": 19.25,
        "Leitor de Rede CAN / Telemetria": 75.25,
        "Videomonitoramento + DMS + ADAS": 409.11
    },
    "24 Meses": {
        "GPRS / Gsm": 53.92,
        "Satélite": 129.20,
        "Identificador de Motorista / RFID": 12.83,
        "Leitor de Rede CAN / Telemetria": 50.17,
        "Videomonitoramento + DMS + ADAS": 272.74
    },
    "36 Meses": {
        "GPRS / Gsm": 44.93,
        "Satélite": 107.67,
        "Identificador de Motorista / RFID": 10.69,
        "Leitor de Rede CAN / Telemetria": 41.81,
        "Videomonitoramento + DMS + ADAS": 227.28
    }
}

# 📊 Seção de entrada de dados
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))
razao= st.sidebar.text_input("Razão Social: ")
resp= st.sidebar.text_input("Solicitante: ")
comercial= st.sidebar.text_input("Comercial Responsável: ")
prazo= st.sidebar.date_input("Prazo da Proposta: ")

# 🔽 Exibir botões de produtos
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)

selecionados = []
valores = planos[temp]

for i, (produto, preco) in enumerate(valores.items()):
    col = col1 if i % 2 == 0 else col2
    toggle = col.toggle(f"{produto} - R$ {preco:,.2f}")
    if toggle:
        selecionados.append(preco)

# 🔢 Cálculo dos valores
soma_total = sum(selecionados)
valor_total = soma_total * qtd_veiculos
contrato_total = valor_total * int(temp.split()[0])

# 🏆 Exibir os resultados
st.markdown("---")
st.markdown("### 💰 **Resumo da Cotação:**")
st.success(f"✅ **Valor Unitário:** R$ {valor_total:,.2f}")
st.info(f"📄 **Valor Total do Contrato ({temp}):** R$ {contrato_total:,.2f}")

if st.button("🔄 Gerar Proposta"):
    