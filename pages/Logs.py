# pages/Logs.py
import streamlit as st
import pandas as pd
import user_management_db as umdb

st.set_page_config(layout="wide", page_title="Registos de Atividade", page_icon="📜")

if not st.session_state.get("authentication_status") or st.session_state.get("role") != "admin":
    st.error("🔒 Acesso Negado! Esta página é restrita a administradores.")
    st.stop()

st.title("📜 Registos de Atividade do Sistema")
st.markdown("Auditoria de todas as ações realizadas pelos utilizadores na plataforma.")

logs_data = umdb.get_all_logs()

if not logs_data:
    st.info("Nenhuma atividade registada até ao momento.")
    st.stop()

df = pd.DataFrame(logs_data)
df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.header("Filtros de Log")

users = sorted(df['user'].unique())
selected_user = st.sidebar.multiselect("Filtrar por Utilizador:", options=users, default=users)

actions = sorted(df['action'].unique())
selected_action = st.sidebar.multiselect("Filtrar por Ação:", options=actions, default=actions)

filtered_df = df[df['user'].isin(selected_user) & df['action'].isin(selected_action)]

st.dataframe(
    filtered_df, use_container_width=True, hide_index=True,
    column_config={
        "timestamp": st.column_config.TextColumn("Data e Hora"),
        "user": st.column_config.TextColumn("Utilizador"),
        "action": st.column_config.TextColumn("Ação"),
        "details": st.column_config.TextColumn("Detalhes"),
    }
)
st.sidebar.info(f"A exibir {len(filtered_df)} de {len(df)} registos.")
