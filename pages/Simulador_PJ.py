import streamlit as st
from datetime import datetime
from docx import Document
from io import BytesIO
import requests
import base64

# Configuração da página
st.set_page_config(layout="wide", page_title="Simulador PJ")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Planos
planos = {
    "12 Meses": {"GPRS / Gsm": 80.88, "Satélite": 193.80, "Identificador de Motorista / RFID": 19.25,
                 "Leitor de Rede CAN / Telemetria": 75.25, "Videomonitoramento + DMS + ADAS": 409.11},
    "24 Meses": {"GPRS / Gsm": 53.92, "Satélite": 129.20, "Identificador de Motorista / RFID": 12.83,
                 "Leitor de Rede CAN / Telemetria": 50.17, "Videomonitoramento + DMS + ADAS": 272.74},
    "36 Meses": {"GPRS / Gsm": 44.93, "Satélite": 107.67, "Identificador de Motorista / RFID": 10.69,
                 "Leitor de Rede CAN / Telemetria": 41.81, "Videomonitoramento + DMS + ADAS": 227.28},
}

produtos_descricao = {
    "GPRS / Gsm": "Rastreadores GPRS",
    "Satélite": "Rastreadores Satelitais",
    "Identificador de Motorista / RFID": "Identificador de Motorista / RFID",
    "Leitor de Rede CAN / Telemetria": "Telemetria CAN",
    "Videomonitoramento + DMS + ADAS": "MDVR e Sensor de Fadiga"
}

# Sidebar
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# Seção de produtos
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
selecionados = {}
for i, (produto, preco) in enumerate(planos[temp].items()):
    col = col1 if i % 2 == 0 else col2
    if col.toggle(f"{produto} - R$ {preco:,.2f}"):
        selecionados[produto] = preco

# Cálculo dos valores
soma_total = sum(selecionados.values())
valor_unitario = soma_total * qtd_veiculos
contrato_total = valor_unitario * int(temp.split()[0])

# Resumo
st.markdown("---")
st.success(f"✅ Valor Unitário: R$ {valor_unitario:,.2f}")
st.info(f"📄 Valor Total do Contrato ({temp}): R$ {contrato_total:,.2f}")

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
        # Abrir documento
        doc = Document("Proposta Comercial e Intenção - Verdio.docx")

        # Substituir parágrafos
        for p in doc.paragraphs:
            if "Nome da empresa" in p.text:
                p.text = p.text.replace("Nome da empresa", nome_empresa)
            if "Nome do Responsável" in p.text:
                p.text = p.text.replace("Nome do Responsável", nome_responsavel)
            if "00/00/0000" in p.text:
                p.text = p.text.replace("00/00/0000", validade_proposta.strftime("%d/%m/%Y"))
            if "Nome do comercial" in p.text:
                p.text = p.text.replace("Nome do comercial", nome_consultor)

        # Preencher tabela
        for table in doc.tables:
            if any("Item" in cell.text for cell in table.rows[0].cells):
                while len(table.rows) > 1:
                    table._tbl.remove(table.rows[1]._tr)
                for produto, preco in selecionados.items():
                    row = table.add_row().cells
                    row[0].text = produtos_descricao[produto]
                    row[1].text = "R$ {:.2f}".format(preco)
                total_row = table.add_row().cells
                total_row[0].text = "Total"
                total_row[1].text = f"R$ {soma_total:,.2f}"

        # Adicionar info no texto (veículos e tempo)
        for p in doc.paragraphs:
            if "Número de veículos a serem monitorados:" in p.text:
                p.text = f"Número de veículos a serem monitorados: {qtd_veiculos}"
            if "Tempo médio de operação diária:" in p.text:
                p.text = f"Tempo médio de operação diária: {temp}"

        
        # Salvar DOCX modificado
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        # Enviar para PDFLayer via upload
        pdf_api = "https://api.pdflayer.com/api/convert"
        files = {
            'document_file': ('proposta.docx', buffer, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        params = {
            "access_key": "6c90a644ad3599e8ce44c40b57940a8f",
            "page_size": "A4"
        }

        try:
            response = requests.post(pdf_api, params=params, files=files)
            if response.status_code == 200:
                st.download_button(
                    label="📥 Baixar Proposta em PDF",
                    data=response.content,
                    file_name=f"Proposta_{nome_empresa}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ Erro ao gerar o PDF com a PDFLayer.")
                st.code(response.text)
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")
