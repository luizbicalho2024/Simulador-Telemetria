import streamlit as st
from io import BytesIO
from docx import Document
from docx.shared import Pt
import requests
from datetime import datetime

# Configuração Streamlit
st.set_page_config(layout="wide", page_title="Simulador PJ")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Produtos
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
    "Satélite": "Equipamento de rastreamento via satélite",
    "Identificador de Motorista / RFID": "Identificação automática de motoristas via RFID",
    "Leitor de Rede CAN / Telemetria": "Leitura de dados de telemetria via rede CAN",
    "Videomonitoramento + DMS + ADAS": "Sistema de videomonitoramento com assistência ao motorista"
}

# Sidebar
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# Produtos
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
        doc = Document("Proposta Comercial e Intenção - Verdio.docx")

        # Substituições simples
        for p in doc.paragraphs:
            if "Nome da empresa" in p.text:
                p.text = p.text.replace("Nome da empresa", nome_empresa)
            if "Nome do Responsável" in p.text:
                p.text = p.text.replace("Nome do Responsável", nome_responsavel)
            if "00/00/0000" in p.text:
                p.text = p.text.replace("00/00/0000", validade_proposta.strftime("%d/%m/%Y"))
            if "Nome do comercial" in p.text:
                p.text = p.text.replace("Nome do comercial", nome_consultor)

        # Inserir quantidade e tempo de contrato antes do "Parcelamento"
        for i, p in enumerate(doc.paragraphs):
            if "Parcelamento" in p.text:
                insert_info = f"Quantidade de veículos: {qtd_veiculos} • Tempo de contrato: {temp}"
                doc.paragraphs[i].insert_paragraph_before(insert_info)
                break

        # Atualizar tabela
        for table in doc.tables:
            if any("Item" in cell.text for cell in table.rows[0].cells):
                while len(table.rows) > 1:
                    table._tbl.remove(table.rows[1]._tr)
                for produto, preco in selecionados.items():
                    row = table.add_row().cells
                    row[0].text = produto
                    row[1].text = produtos_descricao[produto]
                    row[2].text = f"R$ {preco:,.2f}"
                total_row = table.add_row().cells
                total_row[0].text = "TOTAL"
                total_row[1].text = ""
                total_row[2].text = f"R$ {soma_total:,.2f}"

        # Salvar como .docx temporário
        buffer_docx = BytesIO()
        doc.save(buffer_docx)
        buffer_docx.seek(0)

        # Enviar para a PDFLayer
        files = {'document': ('proposta.docx', buffer_docx)}
        params = {
            "access_key": "6c90a644ad3599e8ce44c40b57940a8f",
            "page_size": "A4",
        }

        response = requests.post("http://api.pdflayer.com/api/convert", files=files, data=params)

        if response.status_code == 200:
            st.download_button(
                label="📥 Baixar Proposta em PDF",
                data=response.content,
                file_name=f"Proposta_{nome_empresa}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Erro ao converter o arquivo para PDF.")
else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")
