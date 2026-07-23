from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Auditoria e Logs")
apply_branding()
require_auth("admin")
render_sidebar()
render_hero("Auditoria e logs", "Consulte as ações registradas na plataforma e exporte os dados para análise.")

limit = st.selectbox("Quantidade máxima de registros", [500, 1_000, 2_000, 5_000], index=2)
logs = db.get_all_logs(limit=limit)
if not logs:
    st.info("Nenhuma atividade foi registrada.")
    st.stop()

frame = pd.DataFrame(logs)
frame["_id"] = frame["_id"].astype(str)
frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
frame["details_text"] = frame["details"].apply(lambda value: json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (dict, list)) else str(value or ""))

filter_1, filter_2, filter_3 = st.columns(3)
users = sorted(frame["user"].dropna().astype(str).unique().tolist())
actions = sorted(frame["action"].dropna().astype(str).unique().tolist())
selected_users = filter_1.multiselect("Usuários", users, default=users)
selected_actions = filter_2.multiselect("Ações", actions, default=actions)
search = filter_3.text_input("Pesquisar nos detalhes")

filtered = frame[frame["user"].isin(selected_users) & frame["action"].isin(selected_actions)].copy()
if search.strip():
    term = search.strip().casefold()
    filtered = filtered[
        filtered["details_text"].str.casefold().str.contains(term, regex=False)
        | filtered["action"].astype(str).str.casefold().str.contains(term, regex=False)
    ]

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Registros exibidos", len(filtered))
metric_2.metric("Usuários distintos", filtered["user"].nunique())
metric_3.metric("Tipos de ação", filtered["action"].nunique())

st.dataframe(
    filtered[["timestamp", "user", "action", "details_text"]],
    width="stretch",
    hide_index=True,
    column_config={
        "timestamp": st.column_config.DatetimeColumn("Data e hora", format="DD/MM/YYYY HH:mm:ss"),
        "user": "Usuário",
        "action": "Ação",
        "details_text": "Detalhes",
    },
)

if not filtered.empty:
    labels = {
        f"{row['timestamp'].strftime('%d/%m/%Y %H:%M:%S')} — {row['user']} — {row['action']}": index
        for index, row in filtered.iterrows()
        if pd.notna(row["timestamp"])
    }
    selected = st.selectbox("Detalhes de um registro", list(labels), index=None, placeholder="Selecione um registro")
    if selected:
        details = filtered.loc[labels[selected], "details"]
        if isinstance(details, (dict, list)):
            st.json(details, expanded=True)
        else:
            st.code(str(details or "Sem detalhes"), language="text")

csv = filtered[["timestamp", "user", "action", "details_text"]].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button("Exportar logs em CSV", csv, "auditoria_simulador.csv", "text/csv")
