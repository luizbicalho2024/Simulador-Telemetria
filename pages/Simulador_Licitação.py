import streamlit as st

# Configuração inicial
logo = ("imgs/logo.png")
st.image("imgs/logo.png", width=200, caption=" ")
st.markdown("## Simulador para Licitações e Editais")

# Tabela de preços
precoCusto = {
    "Rastreador GPRS/GSM 2G": 216,
    "Rastreador GPRS/GSM 4G": 379,
    "Rastreador Satelital": 620,
    "Telemetria/CAN": 600,
    "RFID ID Motorista": 154,
}

# Entrada de dados
qtd_input = st.text_input("Quantos Veículos deseja realizar cotação: ", value="1", key="qtd")
contrato_input = st.text_input("Tempo de Contrato (meses): ", value="12", key="contrato")
margem_input = st.text_input("Margem de Lucro Desejado: ", value="30", key="margem")

# Validação de entradas
try:
    qtd = int(qtd_input) if qtd_input.isdigit() else 1  # Converte para inteiro ou usa 1 como padrão
    contrato = int(contrato_input) if contrato_input.isdigit() else 12  # Converte para inteiro ou usa 12 como padrão
    margem = int(margem_input) if margem_input.isdigit() else 30
except ValueError:
    st.error("Por favor, insira valores numéricos válidos para quantidade e contrato.")
    qtd, contrato = 1, 12, 30  # Valores padrão em caso de erro

# Seleção de itens
itens_selecionados = []
for item, preco in precoCusto.items():
    if st.checkbox(f"{item} - R$ {preco:,.2f}"):
        itens_selecionados.append(item)

# Cálculo do valor total
valor_total_unitario = sum(precoCusto[item] for item in itens_selecionados)
un_contrato = valor_total_unitario / contrato
un_margem = un_contrato + (un_contrato * margem)
valor_total = un_margem * qtd * contrato

# Exibição do resultado
st.write(f"## Valor total unitário: R$ {un_margem:,.2f}")
st.write(f"## Valor total: R$ {valor_total:,.2f}")
st.write(f"#### (considerando {qtd} veículos e {contrato} meses)")
