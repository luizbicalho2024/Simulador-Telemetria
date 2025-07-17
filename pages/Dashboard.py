# pages/Dashboard.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
from logger_config import log

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Dashboard de Análises", page_icon="📊")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

log.info(f"Utilizador '{st.session_state.get('name')}' acedeu ao dashboard.")

# --- 2. CARREGAMENTO E PROCESSAMENTO DE DADOS ---
st.title("📊 Dashboard de Propostas")
st.markdown("Análise das propostas comerciais geradas pela plataforma.")

proposals_data = umdb.get_all_proposals()

if not proposals_data:
    st.info("Ainda não há propostas registadas para exibir no dashboard.")
    st.stop()

df = pd.DataFrame(proposals_data)
df['data_geracao'] = pd.to_datetime(df['data_geracao'])
df['mes_ano'] = df['data_geracao'].dt.to_period('M').astype(str)

# --- 3. EXIBIÇÃO DAS MÉTRICAS E GRÁFICOS ---
total_propostas = len(df)
valor_total_gerado = df['valor_total'].sum()
propostas_por_consultor = df['consultor'].value_counts()

col1, col2 = st.columns(2)
col1.metric("Total de Propostas Geradas", f"{total_propostas}")
col2.metric("Valor Total em Propostas", f"R$ {valor_total_gerado:,.2f}")

st.markdown("---")

# Gráfico: Valor Gerado por Mês
st.subheader("Valor de Propostas por Mês")
valor_por_mes = df.groupby('mes_ano')['valor_total'].sum()
st.bar_chart(valor_por_mes)

# Gráfico: Propostas por Consultor
st.subheader("Propostas por Consultor")
st.bar_chart(propostas_por_consultor)

# Tabela de Dados Brutos
with st.expander("Ver todas as propostas registadas"):
    st.dataframe(df)
