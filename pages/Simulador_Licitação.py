import streamlit as st
import time

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto",  caption="")
st.markdown("## Simulador para Licitações e Editais")
#st.sidebar.markdown("## Simulador de Venda")



precoCusto = {
        "Rastreador GPRS/GSM 2G": 216,
        "Rastreador GPRS/GSM 4G": 379,
        "Rastreador Satelital": 620,
        "Telemetria/CAN": 600,
        "RFID ID Motorista": 154,
        "Dados Mensal Un GPRS": 5,
        "Dados Mensal Un Satélite": 69.20,
    }



st.text_input("Quantos Veículos deseja realizar cotação: ", value='1', key="qtd")

st.text_input("Tempo de Contrato deseja realizar cotação: ", value='12', key="contrato")

 
soma_total = 0
valor_total = 0


itens_selecionados = []
for item, preco in precoCusto.items():
    # Crear un checkbox por cada item
    if st.checkbox(f"{item} - R$ {preco:,.2f}"):
        itens_selecionados.append(item)


valor_total = 0
for item in itens_selecionados:
    valor_total += precoCusto[item]

# Mostrando o valor total na interface
st.write(f"## Valor total Un: R$ {valor_total:,.2f}")
        
