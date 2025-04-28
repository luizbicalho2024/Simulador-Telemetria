import streamlit as st
from io import BytesIO
from docx import Document
from datetime import datetime
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx2pdf.exceptions import ConversionError
import os
import tempfile

# Try to use docx2pdf, but have a fallback for cloud environments
try:
    from docx2pdf import convert as docx2pdf_convert
    HAS_WORD = True
except (ImportError, ConversionError):
    import subprocess
    HAS_WORD = False

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

selecionados = {}
valores = planos[temp]

for i, (produto, preco) in enumerate(valores.items()):
    col = col1 if i % 2 == 0 else col2
    toggle = col.toggle(f"{produto} - R$ {preco:,.2f}")
    if toggle:
        selecionados[produto] = preco

# 🔢 Cálculo dos valores
soma_total = sum(selecionados.values())
valor_total = soma_total * qtd_veiculos
contrato_total = valor_total * int(temp.split()[0])

# 🏆 Exibir o resumo da cotação
st.markdown("---")
st.markdown("### 💰 **Resumo da Cotação:**")
st.success(f"✅ **Valor Unitário:** R$ {soma_total:,.2f}")
st.info(f"📄 **Valor Total do Contrato ({temp}):** R$ {contrato_total:,.2f}")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()

# Método alternativo para criar PDF em ambientes cloud
def docx_to_pdf_cloud(docx_path, pdf_path):
    """
    Converte DOCX para PDF usando uma abordagem compatível com cloud
    """
    try:
        # Tenta usar libreoffice se disponível (funciona em muitos ambientes Linux)
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', 
                        '--outdir', os.path.dirname(pdf_path), docx_path], 
                        capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            # Tenta usar unoconv se disponível
            subprocess.run(['unoconv', '-f', 'pdf', '-o', pdf_path, docx_path], 
                           capture_output=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            # Não conseguiu converter
            return False

# Cria um DOCX básico se não puder converter para PDF
def create_simple_pdf(pdf_path, dados):
    """
    Cria um PDF básico com os dados da proposta
    """
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 730, "Proposta Comercial - Verdio")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 700, f"Empresa: {dados['nome_empresa']}")
    c.drawString(72, 680, f"Responsável: {dados['nome_responsavel']}")
    c.drawString(72, 660, f"Validade: {dados['validade']}")
    
    c.drawString(72, 620, "Produtos Selecionados:")
    y = 600
    total = 0
    for produto, preco in dados['produtos'].items():
        valor = preco * dados['qtd_veiculos']
        total += valor
        c.drawString(72, y, f"- {produto}: R$ {valor:,.2f}")
        y -= 20
    
    c.drawString(72, y-20, f"Total: R$ {total:,.2f}")
    c.drawString(72, y-60, f"Consultor: {dados['nome_comercial']}")
    c.save()

# 🚀 Se produtos foram selecionados, permitir gerar PDF
if selecionados:
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    with st.form("formulario_proposta"):
        nome_empresa = st.text_input("Nome da Empresa")
        nome_responsavel = st.text_input("Nome do Responsável")
        validade_proposta = st.date_input("Validade da Proposta", value=datetime.today())
        nome_comercial = st.text_input("Nome do Consultor Comercial")
        
        gerar = st.form_submit_button("Gerar Proposta")

    if gerar:
        # Criar diretório temporário
        with tempfile.TemporaryDirectory() as tmpdirname:
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
                if "Nome do comercial" in p.text:
                    p.text = p.text.replace("Nome do comercial", nome_comercial)

            # Atualizar tabelas de preço e remover produtos não selecionados
            for table in doc.tables:
                rows_to_remove = []
                
                # Primeiro passo: identificar linhas a remover
                for i, row in enumerate(table.rows):
                    product_found = False
                    for cell in row.cells:
                        # Verifica os nomes dos produtos na célula
                        for produto in planos[temp].keys():
                            if produto in cell.text and produto not in selecionados:
                                # O produto está na tabela mas não foi selecionado
                                rows_to_remove.append(i)
                                product_found = True
                                break
                        if product_found:
                            break
                
                # Remove as linhas de trás para frente para não afetar os índices
                for row_idx in sorted(rows_to_remove, reverse=True):
                    if row_idx > 0 and row_idx < len(table.rows) - 1:  # Não remove cabeçalho nem rodapé
                        tr = table._tbl.getchildren()[row_idx]
                        table._tbl.remove(tr)
                
                # Atualiza os valores dos produtos selecionados e o total
                for row in table.rows:
                    for cell in row.cells:
                        if "R$ 00,00" in cell.text and "Total" in row.cells[0].text:
                            cell.text = cell.text.replace("R$ 00,00", f"R$ {valor_total:,.2f}")
                        # Atualiza preços dos produtos selecionados
                        for produto, preco in selecionados.items():
                            if produto in row.cells[0].text:
                                for cell in row.cells:
                                    if "R$ 00,00" in cell.text:
                                        valor_produto = preco * qtd_veiculos
                                        cell.text = cell.text.replace("R$ 00,00", f"R$ {valor_produto:,.2f}")

            # Salvar o arquivo temporário em DOCX
            temp_docx = os.path.join(tmpdirname, f"Proposta_{nome_empresa}.docx")
            doc.save(temp_docx)
            
            # Tentar converter para PDF
            temp_pdf = os.path.join(tmpdirname, f"Proposta_{nome_empresa}.pdf")
            
            pdf_success = False
            if HAS_WORD:
                try:
                    docx2pdf_convert(temp_docx, temp_pdf)
                    pdf_success = True
                except Exception:
                    pdf_success = False
            
            if not pdf_success:
                # Tentar método alternativo
                pdf_success = docx_to_pdf_cloud(temp_docx, temp_pdf)
            
            if not pdf_success:
                # Se todas as conversões falharem, criar um PDF simples
                dados = {
                    'nome_empresa': nome_empresa,
                    'nome_responsavel': nome_responsavel,
                    'validade': validade_proposta.strftime("%d/%m/%Y"),
                    'produtos': selecionados,
                    'qtd_veiculos': qtd_veiculos,
                    'nome_comercial': nome_comercial
                }
                create_simple_pdf(temp_pdf, dados)
            
            # Ler o arquivo PDF para oferecer download
            with open(temp_pdf, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            
            # Oferecer download do PDF
            st.download_button(
                label="📥 Baixar Proposta em PDF",
                data=pdf_data,
                file_name=f"Proposta_{nome_empresa}.pdf",
                mime="application/pdf"
            )

            # Opção de backup: Também oferecer download do DOCX original
            with open(temp_docx, "rb") as docx_file:
                docx_data = docx_file.read()
            
            st.download_button(
                label="📥 Baixar Proposta em DOCX (Backup)",
                data=docx_data,
                file_name=f"Proposta_{nome_empresa}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )