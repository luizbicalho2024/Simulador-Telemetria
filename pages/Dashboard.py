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

# ALTERAÇÃO DE ACESSO: Agora apenas verifica se o utilizador está logado.
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

st.title("📊 Dashboard de Propostas")
st.markdown("Análise das propostas comerciais geradas pela plataforma.")

# Carrega os dados, incluindo o _id
proposals_cursor = umdb.get_all_proposals()
proposals_data = list(proposals_cursor) # Converte o cursor para uma lista

if not proposals_data:
    st.info("Ainda não há propostas registadas para exibir no dashboard.")
    st.stop()

df = pd.DataFrame(proposals_data)

# Converte o _id para string para ser usado como chave
if '_id' in df.columns:
    df['_id'] = df['_id'].astype(str)

if 'data_geracao' in df.columns:
    df['data_geracao'] = pd.to_datetime(df['data_geracao'])
    df['mes_ano'] = df['data_geracao'].dt.to_period('M').astype(str)
else:
    st.error("Os dados das propostas não contêm a coluna 'data_geracao'.")
    st.stop()

# --- 3. MÉTRICAS E GRÁFICOS ---
total_propostas = len(df)
valor_total_gerado = df['valor_total'].sum()
propostas_por_consultor = df['consultor'].value_counts()

col1, col2 = st.columns(2)
col1.metric("Total de Propostas Geradas", f"{total_propostas}")
col2.metric("Valor Total em Propostas", f"R$ {valor_total_gerado:,.2f}")

st.markdown("---")

st.subheader("Valor de Propostas por Mês")
valor_por_mes = df.groupby('mes_ano')['valor_total'].sum()
if not valor_por_mes.empty:
    st.bar_chart(valor_por_mes)

st.subheader("Propostas por Consultor")
if not propostas_por_consultor.empty:
    st.bar_chart(propostas_por_consultor)

# --- 4. TABELA DE DADOS COM OPÇÃO DE EXCLUIR PARA ADMINS ---
with st.expander("Ver e Gerir todas as propostas registadas", expanded=True):
    df_display = df.copy()
    
    # Apenas administradores veem a coluna de Ação
    if st.session_state.get("role") == "admin":
        # Adiciona a coluna de Ação ao DataFrame de exibição
        df_display['Ação'] = [None] * len(df_display)
        
        # Define a ordem das colunas para ter a Ação no final
        cols_order = ['data_geracao', 'consultor', 'empresa', 'tipo', 'valor_total', 'Ação', '_id']
        df_display = df_display[cols_order]
        
        st.data_editor(
            df_display,
            column_config={
                "_id": None, # Esconde a coluna de ID
                "Ação": st.column_config.ButtonColumn(
                    "Excluir",
                    help="Clique para excluir esta proposta permanentemente.",
                    on_click=lambda row: umdb.delete_proposal(row['_id']),
                    type="primary"
                ),
                "data_geracao": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                "consultor": "Consultor",
                "empresa": "Empresa/Licitação",
                "tipo": "Tipo",
                "valor_total": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True,
            key="proposals_editor"
        )
    else:
        # Utilizadores não-admin veem uma tabela simples, sem a coluna de Ação
        cols_to_show = ['data_geracao', 'consultor', 'empresa', 'tipo', 'valor_total']
        st.dataframe(
            df_display[cols_to_show],
            column_config={
                "data_geracao": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                "consultor": "Consultor",
                "empresa": "Empresa/Licitação",
                "tipo": "Tipo",
                "valor_total": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )
