# pages/7_Historico_Faturamento.py
import streamlit as st
import pandas as pd
import user_management_db as umdb

st.set_page_config(
    layout="wide",
    page_title="Histórico de Faturamento",
    page_icon="🧾"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

st.title("🧾 Histórico de Faturamento")
st.markdown("Análise dos relatórios de faturamento gerados e salvos na plataforma.")

history_data = umdb.get_billing_history()

if not history_data:
    st.info("Nenhum histórico de faturamento encontrado.")
    st.stop()

df = pd.DataFrame(history_data)
df['data_geracao'] = pd.to_datetime(df['data_geracao'])
df['mes_ano'] = df['data_geracao'].dt.to_period('M').astype(str)

st.subheader("Evolução do Faturamento Total por Mês")
faturamento_mensal = df.groupby('mes_ano')['valor_total'].sum()
if not faturamento_mensal.empty:
    st.bar_chart(faturamento_mensal)

with st.expander("Ver todos os registos de faturamento", expanded=True):
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "data_geracao": st.column_config.DatetimeColumn("Data de Geração", format="DD/MM/YYYY HH:mm"),
            "cliente": "Cliente",
            "periodo_relatorio": "Período do Relatório",
            "valor_total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"),
            "terminais_cheio": "Nº Fat. Cheio",
            "terminais_proporcional": "Nº Fat. Proporcional",
            "gerado_por": "Gerado Por"
        }
    )
