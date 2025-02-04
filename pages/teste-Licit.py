import streamlit as st
import pandas as pd

# Função para calcular custos, receitas e lucros
def calcular_precificacao(qtd_veiculos, custo_unitario, receita_unitaria, impostos_percentual, outros_custos):
    # Custos diretos
    custo_total = qtd_veiculos * custo_unitario

    # Receita bruta
    receita_bruta = qtd_veiculos * receita_unitaria

    # Impostos
    impostos = receita_bruta * (impostos_percentual / 100)

    # Custos totais
    custos_totais = custo_total + outros_custos + impostos

    # Lucro líquido
    lucro_liquido = receita_bruta - custos_totais

    # Margem de lucro
    margem_lucro = (lucro_liquido / receita_bruta) * 100 if receita_bruta > 0 else 0

    return custo_total, receita_bruta, impostos, custos_totais, lucro_liquido, margem_lucro

# Configuração do Streamlit
st.title("Simulador de Precificação para Licitações")
st.sidebar.header("Parâmetros de Entrada")

# Entrada de parâmetros
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos/Assinaturas", min_value=1, value=100)
custo_unitario = st.sidebar.number_input("Custo Unitário por Veículo (R$)", min_value=0.0, value=150.0, step=10.0)
receita_unitaria = st.sidebar.number_input("Receita Unitária por Veículo (R$)", min_value=0.0, value=300.0, step=10.0)
impostos_percentual = st.sidebar.number_input("Percentual de Impostos (%)", min_value=0.0, value=10.0, step=1.0)
outros_custos = st.sidebar.number_input("Outros Custos Operacionais (R$)", min_value=0.0, value=5000.0, step=100.0)

# Cálculo
total_custo, total_receita, total_impostos, total_custos, lucro_liquido, margem_lucro = calcular_precificacao(
    qtd_veiculos, custo_unitario, receita_unitaria, impostos_percentual, outros_custos
)

# Exibição dos resultados
st.header("Resultados da Simulação")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Receitas e Custos")
    st.metric("Receita Bruta (R$)", f"{total_receita:,.2f}")
    st.metric("Custos Totais (R$)", f"{total_custos:,.2f}")
    st.metric("Impostos (R$)", f"{total_impostos:,.2f}")

with col2:
    st.subheader("Lucro e Margem")
    st.metric("Lucro Líquido (R$)", f"{lucro_liquido:,.2f}")
    st.metric("Margem de Lucro (%)", f"{margem_lucro:.2f}%")

# Exibição detalhada em tabela
data = {
    "Descrição": ["Custo Total", "Receita Bruta", "Impostos", "Custos Totais", "Lucro Líquido", "Margem de Lucro"],
    "Valores (R$ ou %)": [
        f"{total_custo:,.2f}",
        f"{total_receita:,.2f}",
        f"{total_impostos:,.2f}",
        f"{total_custos:,.2f}",
        f"{lucro_liquido:,.2f}",
        f"{margem_lucro:.2f}%",
    ],
}

df = pd.DataFrame(data)

st.subheader("Resumo Detalhado")
st.dataframe(df, use_container_width=True)

# Conclusão
st.info(
    "Este simulador é genérico e pode ser ajustado para diferentes editais. Insira os valores reais de acordo com as especificações do edital para obter resultados mais precisos."
)
