import streamlit as st
import requests
import pdfkit
from jinja2 import Template
from datetime import datetime
from io import BytesIO

# Configuração
st.set_page_config(page_title="Simulador PJ", layout="wide")

# Título
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Tabela de preços
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

# Sidebar
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
tempo_contrato = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# Produtos selecionáveis
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
produtos_escolhidos = {}
for i, (produto, preco) in enumerate(planos[tempo_contrato].items()):
    col = col1 if i % 2 == 0 else col2
    if col.toggle(f"{produto} - R$ {preco:,.2f}"):
        produtos_escolhidos[produto] = preco

# Cálculo
valor_unitario = sum(produtos_escolhidos.values()) * qtd_veiculos
valor_total_contrato = valor_unitario * int(tempo_contrato.split()[0])

# Exibição
st.markdown("---")
st.success(f"✅ Valor Unitário: R$ {valor_unitario:,.2f}")
st.info(f"📄 Valor Total do Contrato ({tempo_contrato}): R$ {valor_total_contrato:,.2f}")

# Formulário
if produtos_escolhidos:
    with st.form("gerar_proposta"):
        st.subheader("📄 Dados para Geração do PDF")
        empresa = st.text_input("Nome da Empresa")
        responsavel = st.text_input("Nome do Responsável")
        consultor = st.text_input("Nome do Consultor Comercial")
        validade = st.date_input("Validade da Proposta", value=datetime.today())
        gerar = st.form_submit_button("Gerar Proposta em PDF")

    if gerar:
        # Obter HTML do GitHub
        html_url = "https://raw.githubusercontent.com/luizbicalho2024/Simulador-Telemetria/main/pages/Proposta-Comercial-e-Intenção-Verdio.html"
        response = requests.get(html_url)
        if response.status_code != 200:
            st.error("Erro ao carregar o modelo HTML.")
            st.stop()

        template_html = response.text

        # Construir tabela de produtos
        tabela_itens = ""
        for produto, preco in produtos_escolhidos.items():
            tabela_itens += f"""
            <tr>
                <td>{produto}</td>
                <td>{preco:,.2f}</td>
            </tr>
            """
        tabela_itens += f"""
        <tr>
            <td><strong>Total</strong></td>
            <td><strong>R$ {sum(produtos_escolhidos.values()):,.2f}</strong></td>
        </tr>
        """

        # Substituir placeholders
        template = Template(template_html)
        html_final = template.render(
            empresa=empresa,
            responsavel=responsavel,
            validade=validade.strftime("%d/%m/%Y"),
            consultor=consultor,
            qtd_veiculos=qtd_veiculos,
            tempo_contrato=tempo_contrato,
            itens_tabela=tabela_itens,
            valor_unitario=f"R$ {valor_unitario:,.2f}"
        )

        # Gerar PDF
        try:
            pdf = pdfkit.from_string(html_final, False)
            st.download_button(
                label="📥 Baixar Proposta em PDF",
                data=pdf,
                file_name=f"Proposta_{empresa}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")
else:
    st.warning("⚠️ Selecione ao menos um produto para gerar a proposta.")
