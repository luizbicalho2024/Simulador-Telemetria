import streamlit as st
import time

st.markdown("## Simulador de Venda")
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

if cliente == "Pessoa Física":
        modeloPF = st.radio(
            'Tipo de Rastreador: ',
            ("GPRS / Gsm", "Satelital"))
        if modeloPF == "GPRS / Gsm":
            st.write(f"### Valor Anual Unitário À Vista: R$ {gprs:,.2f}")
            option = st.selectbox(
                    "Deseja Parcelar: ",
                    ("2", "3", "4","5","6","7","8","9","10","11","12"),
                    #index="Avista",
                    placeholder="Selecione a quantidade de Parcelas",
                )
            st.write(f"Parcelamento: {option}x")
            margem = int(option) * 0.0408
            parce = gprs / int(option)
            calc_par = parce + (parce * margem)
            total = calc_par * int(option)
            st.write(f"{option} Parcelas de: R$ {calc_par:,.2f}")  
            st.write(f"### Valor Anual Unitário: R$ {total:,.2f}")             
        else:
            st.write(f"### Valor Anual Unitário À Vista: R$ {satelite:,.2f}")
            option = st.selectbox(
                    "Deseja Parcelar: ",
                    ("2", "3", "4","5","6","7","8","9","10","11","12"),
                    #index="Avista",
                    placeholder="Selecione a quantidade de Parcelas",
                )
            st.write(f"Parcelamento: {option}x")
            margem = int(option) * 0.0408
            parce = satelite / int(option)
            calc_par = parce + (parce * margem)
            total = calc_par * int(option)
            st.write(f"{option} Parcelas de: R$ {calc_par:,.2f}")  
            st.write(f"### Valor Anual Unitário: R$ {total:,.2f}")  