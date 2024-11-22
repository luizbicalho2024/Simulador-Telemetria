import streamlit as st
import time

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto",  caption="")
st.markdown("## Simulador de Venda Verdio Pessoa Física")
#st.sidebar.markdown("## Simulador de Venda")

gprs = 970.56
satelite = 2325.60
    

modeloPF = st.selectbox(
            'Tipo de Rastreador: ',
            ("GPRS / Gsm", "Satelital"))

if modeloPF == "GPRS / Gsm":
    st.write(f"### Valor Anual À Vista: R$ {gprs:,.2f}")

    desconto = st.checkbox("Efetuar Desconto: ",value=False)
    if desconto:
        porcetagem = st.text_input(f'Qual Porcentagem de Desconto:',value='0')
        desconto_calc = gprs - (gprs * (int(porcetagem)/100))
        st.write(f"Porcentagem Selecionada: {int(porcetagem)}%")
        st.write(f"### Valor Anual com Desconto: R$ {desconto_calc:,.2f}")
                
else:
    st.write(f"### Valor Anual À Vista: R$ {satelite:,.2f}")

    desconto = st.checkbox("Efetuar Desconto: ",value=False)
    if desconto:
        porcetagem = st.text_input(f'Qual Porcentagem de Desconto:',value='0')
        desconto_calc = satelite - (satelite * (int(porcetagem)/100))
        st.write(f"Porcentagem Selecionada: {int(porcetagem)}%")
        st.write(f"### Valor Anual com Desconto: R$ {desconto_calc:,.2f}")

parcelamento = st.checkbox("Deseja Parcelar: ",value=False)

if parcelamento:
    if modeloPF == "GPRS / Gsm":
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
        st.write(f"{option} Parcelas no valor de: R$ {calc_par:,.2f}")  
        st.write(f"### Valor Anual: R$ {total:,.2f}") 
        
    else:
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
        st.write(f"{option} Parcelas no valor de: R$ {calc_par:,.2f}")  
        st.write(f"### Valor Anual: R$ {total:,.2f}") 