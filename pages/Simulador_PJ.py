import streamlit as st

# Ativar modo wide e definir título/ícone da página
st.set_page_config(layout="wide", page_title="Simulador PJ", page_icon="🛒", initial_sidebar_state="expanded")

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto", caption="")
st.markdown("## Simulador de Venda Verdio Pessoa Jurídica")

# Definição dos preços
gprs12, satelite12, rfid, redecan, mdvr = 80.88, 193.80, 19.25, 75.25, 409.11
gprs24, satelite24, rfid24, redecan24, mdvr24 = 53.92, 129.20, 12.83, 50.17, 272.74
gprs36, satelite36, rfid36, redecan36, mdvr36 = 44.93, 107.67, 10.69, 41.81, 227.28

st.text_input("Quantos Veículos deseja realizar cotação: ", value='1', key="qtd")

temp = st.selectbox("Tempo de Contrato: ", ("12 Meses", "24 Meses", "36 Meses"), placeholder="Selecione o Tempo de Contrato")
st.write(f"Contrato: {temp}")

# Define os valores conforme a escolha do contrato
if temp == "12 Meses":
    contrat = 12
    produtos = [
        (f"GPRS / Gsm R$ {gprs12:,.2f}", gprs12),
        (f"Satélite R$ {satelite12:,.2f}", satelite12),
        (f"Identificador de Motorista / RFID R$ {rfid:,.2f}", rfid),
        (f"Leitor de Rede CAN / Telemetria R$ {redecan:,.2f}", redecan),
        (f"Videomonitoramento + DMS + ADAS R$ {mdvr:,.2f}", mdvr),
    ]
elif temp == "24 Meses":
    contrat = 24
    produtos = [
        (f"GPRS / Gsm R$ {gprs24:,.2f}", gprs24),
        (f"Satélite R$ {satelite24:,.2f}", satelite24),
        (f"Identificador de Motorista / RFID R$ {rfid24:,.2f}", rfid24),
        (f"Leitor de Rede CAN / Telemetria R$ {redecan24:,.2f}", redecan24),
        (f"Videomonitoramento + DMS + ADAS R$ {mdvr24:,.2f}", mdvr24),
    ]
else:
    contrat = 36
    produtos = [
        (f"GPRS / Gsm R$ {gprs36:,.2f}", gprs36),
        (f"Satélite R$ {satelite36:,.2f}", satelite36),
        (f"Identificador de Motorista / RFID R$ {rfid36:,.2f}", rfid36),
        (f"Leitor de Rede CAN / Telemetria R$ {redecan36:,.2f}", redecan36),
        (f"Videomonitoramento + DMS + ADAS R$ {mdvr36:,.2f}", mdvr36),
    ]

# Criando duas colunas
col1, col2 = st.columns(2)

soma_total = 0
valor_total = 0

# Distribui os checkboxes entre as duas colunas
for i, (item, valor) in enumerate(produtos):
    col = col1 if i % 2 == 0 else col2
    if col.checkbox(item):
        soma_total += valor

# Calcula o valor total
valor_total = soma_total * int(st.session_state.qtd)
contrato_total = valor_total * contrat

# Exibe os valores finais
st.write(f"## Valor total Unitário: R$ {valor_total:,.2f}")
st.write(f"## Valor total do Contrato: R$ {contrato_total:,.2f}")
