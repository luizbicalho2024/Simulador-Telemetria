# pages/Dashboard.py
import streamlit as st
import pandas as pd
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Análises",
    page_icon="📊"
)

# Verifica se o utilizador está logado E se é um administrador
if not st.session_state.get("authentication_status") or st.session_state.get("role") != "admin":
    st.error("🔒 Acesso Negado! Esta página é restrita a administradores.")
    st.stop()

# --- 2. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

st.title("📊 Dashboard de Propostas")
st.markdown("Análise das propostas comerciais geradas pela plataforma.")

proposals_data = umdb.get_all_proposals()

if not proposals_data:
    st.info("Ainda não há propostas registadas para exibir no dashboard.")
    st.stop()

df = pd.DataFrame(proposals_data)

# Garante que a coluna de data está no formato correto
if 'data_geracao' in df.columns:
    df['data_geracao'] = pd.to_datetime(df['data_geracao'])
    df['mes_ano'] = df['data_geracao'].dt.to_period('M').astype(str)
else:
    st.error("Os dados das propostas não contêm a coluna 'data_geracao'.")
    st.stop()

# --- 3. FILTROS E EXIBIÇÃO ---
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
if not valor_por_mes.empty:
    st.bar_chart(valor_por_mes)

# Gráfico: Propostas por Consultor
st.subheader("Propostas por Consultor")
if not propostas_por_consultor.empty:
    st.bar_chart(propostas_por_consultor)

# Tabela de Dados Brutos
with st.expander("Ver todas as propostas registadas"):
    st.dataframe(df)
