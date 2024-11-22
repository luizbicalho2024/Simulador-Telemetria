import streamlit as st
import time

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto",  caption="")
st.markdown("## Simulador de Venda Verdio Pessoa Jurídica")
#st.sidebar.markdown("## Simulador de Venda")

gprs = 970.56
satelite = 2325.60
gprs12 = 80.88
satelite12 = 193.80
rfid = 19.25
redecan = 75.25
mdvr = 595.60
dms = 324.75

gprs24 = 53.92
satelite24 = 129.20
rfid24 = 12.83
redecan24 = 50.17
mdvr24 = 397.07
dms24 = 216.50

gprs36 = 44.93
satelite36 = 107.67
rfid36 = 10.69
redecan36 = 41.81
mdvr36 = 330.89
dms36 = 180.42

st.text_input("Quantos Veículos deseja realizar cotação: ", value='1', key="qtd")
        
temp = st.selectbox(
    "Tempo de Contrato: ",
        ("12 Meses", "24 Meses", "36 Meses"),
            #index=None,
        placeholder="Selecione o Tempo de Contrato",
)
st.write(f"Contrato: ", temp)
if temp == "12 Meses":   
    soma_total = 0
    valor_total = 0
    contrat = 12
    checkboxes = {
        f"GPRS / Gsm R$ {gprs12:,.2f}": gprs12,
        f"Satélite R$ {satelite12:,.2f}": satelite12,
        f"Identificador de Motorista / RFID R$ {rfid:,.2f}": rfid,
        f"Leitor de Rede CAN / Telemetria R$ {redecan:,.2f}": redecan,
        f"Videomonitoramento / MDVR R$ {mdvr:,.2f}":mdvr,
        f"Sensor de Fadiga / DMS R$ {dms:,.2f}":dms,
    }
    for item, valor in checkboxes.items():
        if st.checkbox(item):
            soma_total += valor
            valor_total = soma_total * int(st.session_state.qtd)
    contrato_total = valor_total * contrat
    st.write(f"## Valor total Unitário: R$ {valor_total:,.2f}")
    st.write(f"## Valor total do Contrato: R$ {contrato_total:,.2f}")
        
elif temp == "24 Meses":   
    soma_total = 0
    valor_total = 0
    contrat = 24
    checkboxes = {
        f"GPRS / Gsm R$ {gprs24:,.2f}": gprs24,
        f"Satélite R$ {satelite24:,.2f}": satelite24,
        f"Identificador de Motorista / RFID R$ {rfid24:,.2f}": rfid24,
        f"Leitor de Rede CAN / Telemetria R$ {redecan24:,.2f}": redecan24,
        f"Videomonitoramento / MDVR R$ {mdvr24:,.2f}":mdvr24,
        f"Sensor de Fadiga / DMS R$ {dms24:,.2f}":dms24,
    }
    for item, valor in checkboxes.items():
        if st.checkbox(item):
            soma_total += valor
            valor_total = soma_total * int(st.session_state.qtd)
    contrato_total = valor_total * contrat
    st.write(f"## Valor total Unitário: R$ {valor_total:,.2f}")
    st.write(f"## Valor total do Contrato: R$ {contrato_total:,.2f}")
else :   
    soma_total = 0
    valor_total = 0
    contrat = 36
    checkboxes = {
        f"GPRS / Gsm R$ {gprs36:,.2f}": gprs36,
        f"Satélite R$ {satelite36:,.2f}": satelite36,
        f"Identificador de Motorista / RFID R$ {rfid36:,.2f}": rfid36,
        f"Leitor de Rede CAN / Telemetria R$ {redecan36:,.2f}": redecan36,
        f"Videomonitoramento / MDVR R$ {mdvr36:,.2f}":mdvr36,
        f"Sensor de Fadiga / DMS R$ {dms36:,.2f}":dms36,
    }
    for item, valor in checkboxes.items():
        if st.checkbox(item):
            soma_total += valor
            valor_total = soma_total * int(st.session_state.qtd)
    contrato_total = valor_total * contrat
    st.write(f"## Valor total Unitário: R$ {valor_total:,.2f}")
    st.write(f"## Valor total do Contrato: R$ {contrato_total:,.2f}")