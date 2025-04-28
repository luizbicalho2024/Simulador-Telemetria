import streamlit as st
from io import BytesIO
from docx import Document
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import tempfile

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

# Função para criar um PDF formatado
def create_proposal_pdf(pdf_path, dados):
    """
    Cria um PDF formatado com os dados da proposta
    """
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 750, "Proposta Comercial - Verdio")
    
    # Informações de cabeçalho
    c.setFont("Helvetica", 12)
    c.drawString(72, 710, f"Empresa: {dados['nome_empresa']}")
    c.drawString(72, 690, f"Aos cuidados de: {dados['nome_responsavel']}")
    c.drawString(72, 670, f"Validade da proposta: {dados['validade']}")
    
    # Apresentação
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 630, "Prezados,")
    c.setFont("Helvetica", 11)
    texto_apresentacao = "Apresentamos a vocês uma proposta de parceria para oferecer maior segurança, eficiência"
    texto_apresentacao2 = "e inteligência na gestão de frotas e maquinários com o Verdio."
    c.drawString(72, 610, texto_apresentacao)
    c.drawString(72, 595, texto_apresentacao2)
    
    # Desafios e vantagens
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 560, "Produtos Selecionados:")
    
    # Tabela de produtos
    y = 530
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, "Item")
    c.drawString(300, y, "Preço | Mês")
    c.line(72, y-5, 520, y-5)  # Linha horizontal
    
    y -= 25
    total = 0
    c.setFont("Helvetica", 11)
    
    # Adiciona produtos selecionados
    for produto, preco in dados['produtos'].items():
        valor = preco * dados['qtd_veiculos']
        total += valor
        c.drawString(72, y, produto)
        c.drawString(300, y, f"R$ {valor:,.2f}")
        y -= 20
    
    # Total
    y -= 10
    c.line(72, y+5, 520, y+5)  # Linha horizontal
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y-15, "Total")
    c.drawString(300, y-15, f"R$ {total:,.2f}")
    
    # Informações adicionais
    y -= 60
    c.setFont("Helvetica", 11)
    c.drawString(72, y, f"Proposta válida até {dados['validade']}")
    
    # Assinatura do consultor
    y -= 40
    c.line(72, y, 250, y)  # Linha para assinatura
    c.setFont("Helvetica", 10)
    c.drawString(72, y-15, f"{dados['nome_comercial']}")
    c.drawString(72, y-30, "Consultor de Negócios Verdio")
    
    c.save()

# 🚀 Se produtos foram selecionados, permitir gerar proposta
if selecionados:
    st.markdown("---")
    st.subheader("📄 Gerar Proposta")

    with st.form("formulario_proposta"):
        nome_empresa = st.text_input("Nome da Empresa")
        nome_responsavel = st.text_input("Nome do Responsável")
        validade_proposta = st.date_input("Validade da Proposta", value=datetime.today())
        nome_comercial = st.text_input("Nome do Consultor Comercial")
        
        col1, col2 = st.columns(2)
        gerar_pdf = col1.checkbox("Gerar PDF", value=True)
        gerar_docx = col2.checkbox("Gerar DOCX", value=True)
        
        gerar = st.form_submit_button("Gerar Proposta")

    if gerar:
        # Criar diretório temporário
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Dados da proposta
            dados = {
                'nome_empresa': nome_empresa,
                'nome_responsavel': nome_responsavel,
                'validade': validade_proposta.strftime("%d/%m/%Y"),
                'produtos': selecionados,
                'qtd_veiculos': qtd_veiculos,
                'nome_comercial': nome_comercial
            }
            
            # Gerar DOCX se solicitado
            if gerar_docx:
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
                
                # Oferecer download do DOCX
                with open(temp_docx, "rb") as docx_file:
                    docx_data = docx_file.read()
                
                st.download_button(
                    label="📥 Baixar Proposta em DOCX",
                    data=docx_data,
                    file_name=f"Proposta_{nome_empresa}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_docx"
                )
            
            # Gerar PDF se solicitado
            if gerar_pdf:
                # Criar PDF com ReportLab
                temp_pdf = os.path.join(tmpdirname, f"Proposta_{nome_empresa}.pdf")
                create_proposal_pdf(temp_pdf, dados)
                
                # Oferecer download do PDF
                with open(temp_pdf, "rb") as pdf_file:
                    pdf_data = pdf_file.read()
                
                st.download_button(
                    label="📥 Baixar Proposta em PDF",
                    data=pdf_data,
                    file_name=f"Proposta_{nome_empresa}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )