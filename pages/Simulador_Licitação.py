import streamlit as st
import time

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto",  caption="")
st.markdown("## Simulador para Licitações e Editais")
#st.sidebar.markdown("## Simulador de Venda")



precoCusto = {
        "GPRS/GSM": 216,
        "Satelital": 620,
        "TDI/CAN": 600,
        "RFID": 154,
        "Comunicação_GPRS": 5,
        "Comunicação_Satelital": 69.20,
        "Adesão_Satelital": 120,
    }



st.text_input("Quantos Veículos deseja realizar cotação: ", value='1', key="qtd")

 
soma_total = 0
valor_total = 0
contrat = 12

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
        
