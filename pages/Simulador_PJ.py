import streamlit as st
from io import BytesIO
from docx import Document
from docx.shared import Pt
import requests
import time
from datetime import datetime

# 🛡️ Token CloudConvert fornecido
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZmNhNjY2Y2E5NzEyMGYzNTgxM2IwNDVkMjA4OTYxODM1NGQxNjU0NjBkZjE1M2QwYzBiZjM4MjA5NGMxZDdjODUxMTg2Mzc1OTUxMDRhZDkiLCJpYXQiOjE3NDU4NzYwNTEuMjUwNjg1LCJuYmYiOjE3NDU4NzYwNTEuMjUwNjg2LCJleHAiOjQ5MDE1NDk2NTEuMjQ0MjU3LCJzdWIiOiI3MTc3MDMzMSIsInNjb3BlcyI6WyJ3ZWJob29rLndyaXRlIiwid2ViaG9vay5yZWFkIiwidGFzay53cml0ZSIsInRhc2sucmVhZCJdfQ.chEPyU6axXxsQTOqAvRg9qzKZP_gOgaKC4OyWuCPZDrwctEW63d-4hRt-4W9FL-aSqTcaXreBn2nax94T4zl_APuZj4bcRJefga8-uOhqWrUX6cAHjumev-BXILmtxi0XbgXkz4wZ-rsVP3-ETCfYq-GPYTnU-va6MgclBtVMOMM6I9-Yh-sCHiYBawPR_zzoHxk6j880I1CVHg42yGHfcIw83gq6Jfle7PrZaScPh3PzBl97STdRUeuaw6pwaTC8CPCTHV3YA3XU3JQd7i1o2t2PerMXuD79dk45NZxvJX8KJCcPtvnNCGFrI677X3nLfo86eUgnqtLbrRO1COhtU5spZUTNWqms2pGLfJFgotRUAc9T3NLHjVWF3841v0MjcIr1dLXFgf0KMbmI0pBmmotFw7t29Juid1pv5evRIRpYSbEvCNrpg9uIXlxPVPM863aZbBvqSalQAsYwkdv0Wvw16Z7cm2dgqHY-Xpv0I8Yubv61OJ4yirZPQNkXVoV-4DIFY-IHkRyX3C7fYwnAWXyK8wnskrDfHm5yegTVPduVmp8RzeH8WMSBmPlDLsU7KXc_4FhR212A5fzlfKhgVqIUlHKzoq-S-kyigNUUrSQt4ugYKX_2kEZKZMs6UMqt7MHTU7mLT1QWZOmMFBSDReHV0QwwLsKkaP4jkMNKoQ"

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
        doc = Document("Proposta Comercial e Intenção - Verdio.docx")
        for p in doc.paragraphs:
            if "Nome da empresa" in p.text:
                p.text = p.text.replace("Nome da empresa", nome_empresa)
            if "Nome do Responsável" in p.text:
                p.text = p.text.replace("Nome do Responsável", nome_responsavel)
            if "00/00/0000" in p.text:
                p.text = p.text.replace("00/00/0000", validade_proposta.strftime("%d/%m/%Y"))
            if "Nome do comercial" in p.text:
                p.text = p.text.replace("Nome do comercial", nome_consultor)

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

        buffer_docx = BytesIO()
        doc.save(buffer_docx)
        buffer_docx.seek(0)

        # Criar o job de conversão
        headers = {"Authorization": f"Bearer {API_KEY}"}
        job_payload = {
            "tasks": {
                "import-1": {"operation": "import/upload"},
                "convert-1": {"operation": "convert", "input": "import-1", "input_format": "docx", "output_format": "pdf"},
                "export-1": {"operation": "export/url", "input": "convert-1"}
            }
        }
        job = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_payload, headers=headers).json()
        upload_url = job['data']['tasks'][0]['result']['form']['url']
        parameters = job['data']['tasks'][0]['result']['form']['parameters']

        # Upload DOCX
        files = {'file': ('proposta.docx', buffer_docx, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        upload = requests.post(upload_url, data=parameters, files=files)

        # Esperar o processamento
        job_id = job['data']['id']
        while True:
            check = requests.get(f'https://api.cloudconvert.com/v2/jobs/{job_id}', headers=headers).json()
            if check['data']['status'] == 'finished':
                break
            time.sleep(2)

        # Pegar link do PDF
        pdf_url = None
        for task in check['data']['tasks']:
            if task['operation'] == 'export/url' and 'result' in task and 'files' in task['result']:
                pdf_url = task['result']['files'][0]['url']
                break

        if pdf_url:
            pdf_response = requests.get(pdf_url)
            st.download_button(
                label="📥 Baixar Proposta em PDF",
                data=pdf_response.content,
                file_name=f"Proposta_{nome_empresa}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Erro ao localizar o arquivo PDF exportado.")
else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")