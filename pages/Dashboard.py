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

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

st.title("📊 Dashboard de Propostas")
st.markdown("Análise das propostas comerciais geradas pela plataforma.")

proposals_cursor = umdb.get_all_proposals()
proposals_data = list(proposals_cursor)

if not proposals_data:
    st.info("Ainda não há propostas registadas para exibir no dashboard.")
    st.stop()

df = pd.DataFrame(proposals_data)

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

# --- 4. TABELA DE DADOS E GESTÃO PARA ADMINS ---
st.markdown("---")
st.subheader("Histórico de Propostas Registadas")

cols_to_show = ['data_geracao', 'consultor', 'empresa', 'tipo', 'valor_total']
st.dataframe(
    df[cols_to_show],
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

# Apenas administradores veem a secção de exclusão
if st.session_state.get("role") == "admin":
    with st.expander("🗑️ Excluir Proposta Registada"):
        
        # Cria uma lista de opções legíveis para o selectbox
        options_map = {
            f"{row['empresa']} - {row['data_geracao'].strftime('%d/%m/%Y')} (R$ {row['valor_total']:.2f})": row['_id']
            for index, row in df.iterrows()
        }
        
        # Verifica se há propostas para excluir
        if not options_map:
            st.warning("Não há propostas para excluir.")
        else:
            option_keys = list(options_map.keys())
            selected_option = st.selectbox(
                "Selecione a proposta que deseja excluir:",
                options=option_keys,
                index=None, # Nenhum selecionado por defeito
                placeholder="Escolha uma proposta..."
            )

            if selected_option:
                proposal_id_to_delete = options_map[selected_option]
                if st.button(f"Confirmar Exclusão de '{selected_option}'", type="primary"):
                    if umdb.delete_proposal(proposal_id_to_delete):
                        st.toast("Proposta excluída com sucesso! A página será recarregada.", icon="🗑️")
                        st.rerun()
                    else:
                        st.error("Falha ao excluir a proposta.")
