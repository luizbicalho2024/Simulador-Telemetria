import streamlit as st
import time

st.markdown("## Simulador de Venda Verdio Pessoa Física")
#st.sidebar.markdown("## Simulador de Venda")

gprs = 970.56
satelite = 2325.60


def calc ():
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


modeloPF = st.selectbox(
            'Tipo de Rastreador: ',
            ("GPRS / Gsm", "Satelital"))

if modeloPF == "GPRS / Gsm":
    st.write(f"### Valor Anual Unitário À Vista: R$ {gprs:,.2f}")
                
else:
    st.write(f"### Valor Anual Unitário À Vista: R$ {satelite:,.2f}")

parcelamento = st.checkbox("Deseja Parcelar: ",value=False)

if parcelamento:
    calc
    