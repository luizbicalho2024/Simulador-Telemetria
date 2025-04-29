import streamlit as st
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(layout="wide", page_title="Simulador PJ")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Produtos e planos
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

# Entradas na sidebar
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# Seção principal
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
selecionados = {}
for i, (produto, preco) in enumerate(planos[temp].items()):
    col = col1 if i % 2 == 0 else col2
    if col.toggle(f"{produto} - R$ {preco:,.2f}"):
        selecionados[produto] = preco

# Cálculos
soma_total = sum(selecionados.values())
valor_total = soma_total * qtd_veiculos
contrato_total = valor_total * int(temp.split()[0])

st.markdown("---")
st.success(f"✅ Valor Unitário: R$ {valor_total:,.2f}")
st.info(f"📄 Valor Total do Contrato ({temp}): R$ {contrato_total:,.2f}")

if st.button("🔄 Limpar Seleção"):
    st.rerun()

# Formulário
if selecionados:
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    with st.form("formulario_proposta"):
        nome_empresa = st.text_input("Nome da Empresa")
        nome_responsavel = st.text_input("Nome do Responsável")
        nome_consultor = st.text_input("Nome do Consultor Comercial")
        validade_proposta = st.date_input("Validade da Proposta", value=datetime.today())
        gerar = st.form_submit_button("Gerar Proposta")

    if gerar:
        # 🔗 URL do HTML no GitHub
        html_url = "https://raw.githubusercontent.com/luizbicalho2024/Simulador-Telemetria/main/pages/Proposta-Comercial-e-Inten%C3%A7%C3%A3o-Verdio.html"

        # Montar chamada para PDFLayer
        pdf_url = "http://api.pdflayer.com/api/convert"
        params = {
            "access_key": "6c90a644ad3599e8ce44c40b57940a8f",
            "document_url": html_url,
            "page_size": "A4",
            "margin_top": "10",
            "margin_bottom": "10",
            "margin_left": "15",
            "margin_right": "15"
        }

        response = requests.get(pdf_url, params=params)

        if response.status_code == 200 and response.headers["Content-Type"] == "application/pdf":
            st.download_button(
                label="📥 Baixar Proposta em PDF",
                data=response.content,
                file_name=f"Proposta_{nome_empresa}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("❌ Erro ao gerar o PDF com a PDFLayer.")
else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")
