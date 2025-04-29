import streamlit as st
from datetime import datetime
from io import BytesIO
import pdfkit

# Função para montar a tabela HTML com os itens
def gerar_tabela_html(itens, descricoes):
    html = ""
    for produto, preco in itens.items():
        html += f"""
        <tr>
            <td>{produto}</td>
            <td>{descricoes.get(produto, "")}</td>
            <td>R$ {preco:,.2f}</td>
        </tr>
        """
    return html

# Produtos
planos = {
    "12 Meses": {...},  # mesmo dicionário que você já usa
    "24 Meses": {...},
    "36 Meses": {...}
}
descricoes = {
    "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G",
    "Satélite": "Rastreamento via satélite",
    "Identificador de Motorista / RFID": "Identificação de motoristas via RFID",
    "Leitor de Rede CAN / Telemetria": "Telemetria via rede CAN",
    "Videomonitoramento + DMS + ADAS": "Videomonitoramento e assistência ao motorista"
}

# Layout Streamlit
st.set_page_config(layout="wide", page_title="Simulador PJ")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.header("📝 Configurações")
qtd = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# Produtos
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)
selecionados = {}
for i, (produto, preco) in enumerate(planos[temp].items()):
    col = col1 if i % 2 == 0 else col2
    if col.toggle(f"{produto} - R$ {preco:,.2f}"):
        selecionados[produto] = preco

# Cálculo
valor_unitario = sum(selecionados.values()) * qtd
valor_total = valor_unitario * int(temp.split()[0])

st.markdown("---")
st.success(f"✅ Valor Unitário: R$ {valor_unitario:,.2f}")
st.info(f"📄 Valor Total do Contrato ({temp}): R$ {valor_total:,.2f}")

if st.button("🔄 Limpar Seleção"):
    st.rerun()

if selecionados:
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    with st.form("formulario"):
        empresa = st.text_input("Nome da Empresa")
        responsavel = st.text_input("Nome do Responsável")
        consultor = st.text_input("Consultor Comercial")
        validade = st.date_input("Validade da Proposta", value=datetime.today())
        gerar = st.form_submit_button("Gerar PDF")

    if gerar:
        with open("modelo_proposta.html", "r", encoding="utf-8") as f:
            html_template = f.read()

        html_final = html_template \
            .replace("{{empresa}}", empresa) \
            .replace("{{responsavel}}", responsavel) \
            .replace("{{consultor}}", consultor) \
            .replace("{{validade}}", validade.strftime("%d/%m/%Y")) \
            .replace("{{qtd}}", str(qtd)) \
            .replace("{{contrato}}", temp) \
            .replace("{{total_contrato}}", f"{valor_total:,.2f}") \
            .replace("{{tabela_itens}}", gerar_tabela_html(selecionados, descricoes))

        # Geração do PDF com pdfkit
        options = {
            "page-size": "A4",
            "encoding": "UTF-8",
            "margin-top": "10mm",
            "margin-bottom": "10mm",
            "margin-left": "10mm",
            "margin-right": "10mm"
        }

        pdf_file = BytesIO()
        pdfkit.from_string(html_final, False, options=options, output_path=pdf_file)
        pdf_file.seek(0)

        st.download_button(
            label="📥 Baixar Proposta em PDF",
            data=pdf_file,
            file_name=f"Proposta_{empresa}.pdf",
            mime="application/pdf"
        )
