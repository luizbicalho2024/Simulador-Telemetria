import streamlit as st
from datetime import datetime
import base64

# Configuração Streamlit
st.set_page_config(layout="wide", page_title="Simulador PJ")
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Produtos
planos = {
    "12 Meses": {"GPRS / Gsm": 80.88, "Satélite": 193.80, "Identificador de Motorista / RFID": 19.25, "Leitor de Rede CAN / Telemetria": 75.25, "Videomonitoramento + DMS + ADAS": 409.11},
    "24 Meses": {"GPRS / Gsm": 53.92, "Satélite": 129.20, "Identificador de Motorista / RFID": 12.83, "Leitor de Rede CAN / Telemetria": 50.17, "Videomonitoramento + DMS + ADAS": 272.74},
    "36 Meses": {"GPRS / Gsm": 44.93, "Satélite": 107.67, "Identificador de Motorista / RFID": 10.69, "Leitor de Rede CAN / Telemetria": 41.81, "Videomonitoramento + DMS + ADAS": 227.28}
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
    st.subheader("📄 Gerar Proposta (HTML para Impressão)")

    with st.form("formulario_proposta"):
        nome_empresa = st.text_input("Nome da Empresa")
        nome_responsavel = st.text_input("Nome do Responsável")
        nome_consultor = st.text_input("Nome do Consultor Comercial")
        validade_proposta = st.date_input("Validade da Proposta", value=datetime.today())
        gerar = st.form_submit_button("Gerar Proposta")

    if gerar:
        # Ler template HTML
        with open("template.html", "r", encoding="utf-8") as file:
            template = file.read()

        # Montar itens
        itens_html = ""
        for produto, preco in selecionados.items():
            itens_html += f"""
            <tr>
                <td>{produto}</td>
                <td>{produtos_descricao[produto]}</td>
                <td>R$ {preco:,.2f}</td>
            </tr>
            """

        # Substituir placeholders
        html_content = template.replace("{{empresa}}", nome_empresa) \
                               .replace("{{responsavel}}", nome_responsavel) \
                               .replace("{{consultor}}", nome_consultor) \
                               .replace("{{validade}}", validade_proposta.strftime("%d/%m/%Y")) \
                               .replace("{{itens}}", itens_html) \
                               .replace("{{total}}", f"R$ {soma_total:,.2f}") \
                               .replace("{{tempo}}", temp) \
                               .replace("{{contrato_total}}", f"R$ {contrato_total:,.2f}")

        # Codificar HTML para base64 para abrir em nova aba
        b64 = base64.b64encode(html_content.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" target="_blank">📄 Visualizar Proposta</a>'

        st.markdown(href, unsafe_allow_html=True)
else:
    st.warning("⚠️ Selecione pelo menos um item para gerar a proposta.")
