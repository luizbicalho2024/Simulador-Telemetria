import streamlit as st
from io import BytesIO
from docx import Document
from docx.shared import Pt
from datetime import datetime

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide", 
    page_title="Simulador PJ", 
    page_icon="imgs/v-c.png", 
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Produtos e preços
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
    "GPRS / Gsm": "Equipamento de rastreamento para monitoramento em tempo real via GSM/GPRS 2G ou 4G",
    "Satélite": "Equipamento de rastreamento com cobertura via satélite",
    "Identificador de Motorista / RFID": "Identificação do motorista com cartão magnético",
    "Leitor de Rede CAN / Telemetria": "Monitoramento de combustível, temperatura e RPM",
    "Videomonitoramento + DMS + ADAS": "Videomonitoramento, análise de fadiga e assistência avançada de direção"
}

# 📊 Entrada
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# 🔽 Seção produtos
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
selecionados = {}

valores = planos[temp]
for i, (produto, preco) in enumerate(valores.items()):
    col = col1 if i % 2 == 0 else col2
    toggle = col.toggle(f"{produto} - R$ {preco:,.2f}")
    if toggle:
        selecionados[produto] = preco

# 🔢 Cálculo
soma_total = sum(selecionados.values())
valor_total = soma_total * qtd_veiculos
contrato_total = valor_total * int(temp.split()[0])

st.markdown("---")
st.markdown("### 💰 **Resumo da Cotação:**")
st.success(f"✅ **Valor Unitário:** R$ {valor_total:,.2f}")
st.info(f"📄 **Valor Total do Contrato ({temp}):** R$ {contrato_total:,.2f}")

if st.button("🔄 Limpar Seleção"):
    st.rerun()

# 🚀 Formulário para gerar proposta
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

        # Atualizar campos
        for p in doc.paragraphs:
            if "Nome da empresa" in p.text:
                p.text = p.text.replace("Nome da empresa", nome_empresa)
            if "Nome do Responsável" in p.text:
                p.text = p.text.replace("Nome do Responsável", nome_responsavel)
            if "00/00/0000" in p.text:
                p.text = p.text.replace("00/00/0000", validade_proposta.strftime("%d/%m/%Y"))
            if "Nome do comercial" in p.text:
                p.text = p.text.replace("Nome do comercial", nome_consultor)

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
                
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.font.name = 'Arial'
                                run.font.size = Pt(10)

       # Salvar .docx em memória
        buffer_docx = BytesIO()
        doc.save(buffer_docx)
        buffer_docx.seek(0)

        # Baixar o DOCX (mantendo layout, fonte, tabela)
        st.download_button(
            label="📥 Baixar Proposta (.docx)",
            data=buffer_docx,
            file_name=f"Proposta_{nome_empresa}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )


else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")
