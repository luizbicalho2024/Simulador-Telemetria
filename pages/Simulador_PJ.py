import streamlit as st
from datetime import datetime
from io import BytesIO
from weasyprint import HTML

# Dados dos planos e produtos
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

produtos_descricao = {
    "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G",
    "Satélite": "Rastreamento via satélite",
    "Identificador de Motorista / RFID": "Identificação de motoristas via RFID",
    "Leitor de Rede CAN / Telemetria": "Telemetria via rede CAN",
    "Videomonitoramento + DMS + ADAS": "Videomonitoramento e assistência ao motorista"
}

# Configuração da página
st.set_page_config(layout="wide", page_title="Simulador PJ")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Entradas
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()), index=0)

# Seleção de produtos
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
selecionados = {}
for i, (produto, preco) in enumerate(planos[temp].items()):
    col = col1 if i % 2 == 0 else col2
    if col.toggle(f"{produto} - R$ {preco:,.2f}"):
        selecionados[produto] = preco

# Cálculo
valor_unitario = sum(selecionados.values()) * qtd_veiculos
valor_total_contrato = valor_unitario * int(temp.split()[0])

st.markdown("---")
st.success(f"✅ Valor Unitário: R$ {valor_unitario:,.2f}")
st.info(f"📄 Valor Total do Contrato ({temp}): R$ {valor_total_contrato:,.2f}")

if st.button("🔄 Limpar Seleção"):
    st.rerun()

# Geração de proposta
if selecionados:
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    with st.form("dados_proposta"):
        empresa = st.text_input("Nome da Empresa")
        responsavel = st.text_input("Nome do Responsável")
        consultor = st.text_input("Consultor Comercial")
        validade = st.date_input("Validade da Proposta", value=datetime.today())
        gerar = st.form_submit_button("Gerar PDF")

    if gerar:
        # Lê o HTML base
        with open("/mnt/data/modelo_proposta.html", "r", encoding="utf-8") as f:
            html_template = f.read()

        # Gera tabela com os itens
        tabela_html = ""
        for produto, preco in selecionados.items():
            tabela_html += f"""
                <tr>
                    <td>{produto}</td>
                    <td>{produtos_descricao.get(produto, '')}</td>
                    <td>R$ {preco:,.2f}</td>
                </tr>
            """

        # Substitui os placeholders
        html_final = html_template \
            .replace("{{empresa}}", empresa) \
            .replace("{{responsavel}}", responsavel) \
            .replace("{{consultor}}", consultor) \
            .replace("{{validade}}", validade.strftime("%d/%m/%Y")) \
            .replace("{{qtd}}", str(qtd_veiculos)) \
            .replace("{{contrato}}", temp) \
            .replace("{{total_contrato}}", f"{valor_total_contrato:,.2f}") \
            .replace("{{tabela_itens}}", tabela_html)

        # Gera PDF
        pdf_bytes = BytesIO()
        HTML(string=html_final).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)

        st.download_button(
            label="📥 Baixar Proposta em PDF",
            data=pdf_bytes,
            file_name=f"Proposta_{empresa}.pdf",
            mime="application/pdf"
        )
else:
    st.warning("⚠️ Selecione ao menos um item para gerar a proposta.")
