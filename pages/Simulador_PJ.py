import streamlit as st

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto", caption="")
st.markdown("## Simulador de Venda Verdio Pessoa Jurídica")

gprs12 = 80.88
satelite12 = 193.80
rfid = 19.25
redecan = 75.25
mdvr = 409.11

gprs24 = 53.92
satelite24 = 129.20
rfid24 = 12.83
redecan24 = 50.17
mdvr24 = 272.74

gprs36 = 44.93
satelite36 = 107.67
rfid36 = 10.69
redecan36 = 41.81
mdvr36 = 227.28

st.text_input("Quantos Veículos deseja realizar cotação: ", value='1', key="qtd")

temp = st.selectbox(
    "Tempo de Contrato: ",
    ("12 Meses", "24 Meses", "36 Meses"),
    placeholder="Selecione o Tempo de Contrato",
)
st.write(f"Contrato: {temp}")

if temp == "12 Meses":
    contrat = 12
    checkboxes = {
        "GPRS / Gsm": gprs12,
        "Satélite": satelite12,
        "Identificador de Motorista / RFID": rfid,
        "Leitor de Rede CAN / Telemetria": redecan,
        "Videomonitoramento + DMS + ADAS": mdvr,
    }
elif temp == "24 Meses":
    contrat = 24
    checkboxes = {
        "GPRS / Gsm": gprs24,
        "Satélite": satelite24,
        "Identificador de Motorista / RFID": rfid24,
        "Leitor de Rede CAN / Telemetria": redecan24,
        "Videomonitoramento + DMS + ADAS": mdvr24,
    }
else:
    contrat = 36
    checkboxes = {
        "GPRS / Gsm": gprs36,
        "Satélite": satelite36,
        "Identificador de Motorista / RFID": rfid36,
        "Leitor de Rede CAN / Telemetria": redecan36,
        "Videomonitoramento + DMS + ADAS": mdvr36,
    }

# Criando colunas para organizar os checkboxes horizontalmente
cols = st.columns(len(checkboxes))
soma_total = 0
valor_total = 0

for col, (item, valor) in zip(cols, checkboxes.items()):
    if col.checkbox(f"{item} R$ {valor:,.2f}"):
        soma_total += valor

valor_total = soma_total * int(st.session_state.qtd)
contrato_total = valor_total * contrat

st.write(f"## Valor total Unitário: R$ {valor_total:,.2f}")
st.write(f"## Valor total do Contrato: R$ {contrato_total:,.2f}")
