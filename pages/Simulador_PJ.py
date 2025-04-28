import streamlit as st
from io import BytesIO
from docx import Document
from datetime import datetime
import decimal

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide", 
    page_title="Simulador PJ", 
    page_icon="imgs/v-c.png", 
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho
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

# 🔽 Seção de seleção de produtos
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

# 🏆 Exibir o resumo da cotação
st.markdown("---")
st.markdown("### 💰 **Resumo da Cotação:**")
st.success(f"✅ **Valor Unitário:** R$ {valor_total:,.2f}")
st.info(f"📄 **Valor Total do Contrato ({temp}):** R$ {contrato_total:,.2f}")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()

# 🚀 Se produtos foram selecionados, permitir gerar PDF
if selecionados:
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    with st.form("formulario_proposta"):
        nome_empresa = st.text_input("Nome da Empresa")
        nome_responsavel = st.text_input("Nome do Responsável")
        validade_proposta = st.date_input("Validade da Proposta", value=datetime.today())

        gerar = st.form_submit_button("Gerar Proposta")

    if gerar:
        # Carregar o template
        doc = Document("Proposta Comercial e Intenção - Verdio.docx")

        # Atualizar campos no documento
        for p in doc.paragraphs:
            if "Nome da empresa" in p.text:
                p.text = p.text.replace("Nome da empresa", nome_empresa)
            if "Nome do Responsável" in p.text:
                p.text = p.text.replace("Nome do Responsável", nome_responsavel)
            if "00/00/0000" in p.text:
                p.text = p.text.replace("00/00/0000", validade_proposta.strftime("%d/%m/%Y"))

        # Atualizar tabelas de preço
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if "R$ 00,00" in cell.text:
                        cell.text = cell.text.replace("R$ 00,00", f"R$ {valor_total:,.2f}")

        # Salvar o arquivo em memória
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        # Oferecer download
        st.download_button(
            label="📥 Baixar Proposta",
            data=buffer,
            file_name=f"Proposta_{nome_empresa}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
