import streamlit as st
from io import BytesIO
from docx import Document
from docx.shared import Pt
import time
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch

# Configuração Streamlit
st.set_page_config(layout="wide", page_title="Gerador PDF")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Produtos (mantido igual)
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

# Sidebar (mantido igual)
st.sidebar.header("📝 Configurações")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# Seção principal (mantido igual)
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
selecionados = {}
for i, (produto, preco) in enumerate(planos[temp].items()):
    col = col1 if i % 2 == 0 else col2
    if col.toggle(f"{produto} - R$ {preco:,.2f}"):
        selecionados[produto] = preco

# Cálculos (mantido igual)
soma_total = sum(selecionados.values())
valor_total = soma_total * qtd_veiculos
contrato_total = valor_total * int(temp.split()[0])

st.markdown("---")
st.success(f"✅ Valor Unitário: R$ {valor_total:,.2f}")
st.info(f"📄 Valor Total do Contrato ({temp}): R$ {contrato_total:,.2f}")

if st.button("🔄 Limpar Seleção"):
    st.rerun()

# Formulário e Geração de PDF com Reportlab
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
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<b>Proposta Comercial</b>", styles['h1']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Empresa:</b> {nome_empresa}", styles['normal']))
        story.append(Paragraph(f"<b>Responsável:</b> {nome_responsavel}", styles['normal']))
        story.append(Paragraph(f"<b>Consultor Comercial:</b> {nome_consultor}", styles['normal']))
        story.append(Paragraph(f"<b>Validade da Proposta:</b> {validade_proposta.strftime('%d/%m/%Y')}", styles['normal']))
        story.append(Spacer(1, 0.4*inch))

        story.append(Paragraph("<b>Itens Selecionados:</b>", styles['h2']))
        data = [["<b>Item</b>", "<b>Descrição</b>", "<b>Preço Unitário</b>"]]
        for produto, preco in selecionados.items():
            data.append([produto, produtos_descricao[produto], f"R$ {preco:,.2f}"])
        data.append(["<b>TOTAL</b>", "", f"<b>R$ {soma_total:,.2f}</b>"])

        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph(f"<b>Quantidade de Veículos:</b> {qtd_veiculos}", styles['normal']))
        story.append(Paragraph(f"<b>Tempo de Contrato:</b> {temp}", styles['normal']))
        story.append(Paragraph(f"<b>Valor Total Unitário:</b> R$ {valor_total:,.2f}", styles['h3']))
        story.append(Paragraph(f"<b>Valor Total do Contrato ({temp}):</b> R$ {contrato_total:,.2f}", styles['h3']))

        doc.build(story)
        buffer.seek(0)

        st.download_button(
            label="📥 Baixar Proposta em PDF",
            data=buffer,
            file_name=f"Proposta_{nome_empresa}.pdf",
            mime="application/pdf"
        )
else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")