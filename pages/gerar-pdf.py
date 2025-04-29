import streamlit as st
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from datetime import datetime

# ... (Seu código Streamlit para seleção de produtos, cálculo de valores, etc.)

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

        # Parte fixa do documento (você pode ajustar o estilo conforme necessário)
        story.append(Paragraph("<b>Proposta Comercial</b>", styles['h1']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"A<br/>{nome_empresa}<br/><br/>Aos cuidados de<br/>{nome_responsavel}<br/><br/>Prezados,", styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Apresentamos a vocês uma proposta de parceria para oferecer maior segurança, eficiência e inteligência na gestão de frotas e maquinários com o Verdio. Nosso sistema permite controle total sobre veículos e motoristas, aumentando a produtividade, reduzindo custos e garantindo a segurança operacional.", styles['BodyText']))
        # ... (Continue com as outras partes fixas do texto)

        # Tabela dinâmica (gerada a partir dos dados selecionados)
        story.append(Paragraph("<b>5. Valor dos Serviços</b>", styles['h2']))
        story.append(Paragraph("Já falamos sobre o valor que o Verdio pode agregar à sua empresa. Agora, falaremos sobre os custos da solução.", styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))

        data = [["<b>Item</b>", "<b>Descrição</b>", "<b>Preço | Mês</b>"]]  # Título da tabela
        data.append(["Número de veículos a serem monitorados:", str(qtd_veiculos), ""])
        # ... (Adicione outras informações-base, se necessário)
        for produto, preco in selecionados.items():
            data.append([produto, produtos_descricao[produto], f"R$ {preco:,.2f}"])
        data.append(["<b>Total</b>", "", f"<b>R$ {soma_total:,.2f}</b>"])

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

        # ... (Continue com o restante do documento, termo de confidencialidade, etc.)
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph(f"Proposta válida até {validade_proposta.strftime('%d/%m/%Y')}", styles['BodyText']))
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph(f"Nome do comercial<br/>Consultor de Negócios Verdio", styles['BodyText']))

        doc.build(story)

        buffer.seek(0)
        st.download_button(
            label="📥 Baixar Proposta em PDF",
            data=buffer,
            file_name=f"Proposta_{nome_empresa}.pdf",
            mime="application/pdf"
        )