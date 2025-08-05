# pages/Logs.py
import streamlit as st
import pandas as pd
import user_management_db as umdb

st.set_page_config(layout="wide", page_title="Registos de Atividade", page_icon="📜")

if not st.session_state.get("authentication_status") or st.session_state.get("role") != "admin":
    st.error("🔒 Acesso Negado!"); st.stop()

st.title("📜 Registos de Atividade do Sistema")
st.markdown("Auditoria de todas as ações realizadas pelos utilizadores na plataforma.")

logs_data = umdb.get_all_logs()

if not logs_data:
    st.info("Nenhuma atividade registada até ao momento."); st.stop()

df = pd.DataFrame(logs_data)
df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
if '_id' in df.columns:
    df['_id'] = df['_id'].astype(str)

# --- Filtros ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.header("Filtros de Log")
users = sorted(df['user'].unique())
selected_user = st.sidebar.multiselect("Filtrar por Utilizador:", options=users, default=users)
actions = sorted(df['action'].unique())
selected_action = st.sidebar.multiselect("Filtrar por Ação:", options=actions, default=actions)
filtered_df = df[df['user'].isin(selected_user) & df['action'].isin(selected_action)]

st.dataframe(
    filtered_df[['timestamp', 'user', 'action']],
    use_container_width=True,
    hide_index=True,
    column_config={"timestamp": "Data e Hora", "user": "Utilizador", "action": "Ação"}
)

st.markdown("---")
st.subheader("Detalhes da Ação Selecionada")

if not filtered_df.empty:
    options_map = {
        f"{row['timestamp']} - {row['user']} - {row['action']}": index
        for index, row in filtered_df.iterrows()
    }
    selected_log_label = st.selectbox(
        "Selecione um registo para ver os detalhes:",
        options=options_map.keys()
    )
    if selected_log_label:
        selected_index = options_map[selected_log_label]
        details = filtered_df.loc[selected_index, 'details']
        if details and isinstance(details, dict) and details:
            st.json(details, expanded=True)
        else:
            st.info("Esta ação não tem detalhes adicionais registados.")
else:
    st.info("Nenhum registo corresponde aos filtros selecionados.")
