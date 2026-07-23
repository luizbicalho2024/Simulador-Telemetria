from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Dashboard de Propostas")
branding = apply_branding()
require_auth()
render_sidebar()
render_hero("Dashboard de propostas", "Acompanhe volume, valor, perfil de venda e desempenho por consultor.")

proposals = db.get_all_proposals()
if not proposals:
    st.info("Ainda não há propostas registradas.")
    st.stop()

df = pd.DataFrame(proposals)
df["_id"] = df["_id"].astype(str)
df["data_geracao"] = pd.to_datetime(df["data_geracao"], errors="coerce")
df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0.0)
df = df.dropna(subset=["data_geracao"])
df["mes"] = df["data_geracao"].dt.to_period("M").astype(str)

with st.expander("Filtros", expanded=False):
    filter_1, filter_2, filter_3 = st.columns(3)
    consultants = sorted(df["consultor"].dropna().astype(str).unique().tolist())
    types = sorted(df["tipo"].dropna().astype(str).unique().tolist())
    selected_consultants = filter_1.multiselect("Consultores", consultants, default=consultants)
    selected_types = filter_2.multiselect("Tipos", types, default=types)
    min_date = df["data_geracao"].min().date()
    max_date = df["data_geracao"].max().date()
    selected_dates = filter_3.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = df[df["consultor"].isin(selected_consultants) & df["tipo"].isin(selected_types)].copy()
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered = filtered[
        (filtered["data_geracao"].dt.date >= start_date)
        & (filtered["data_geracao"].dt.date <= end_date)
    ]

if filtered.empty:
    st.warning("Nenhuma proposta corresponde aos filtros selecionados.")
    st.stop()

average_ticket = filtered["valor_total"].mean()
top_consultant = filtered.groupby("consultor")["valor_total"].sum().sort_values(ascending=False).index[0]
metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Propostas", len(filtered))
metric_2.metric("Valor total", money(filtered["valor_total"].sum()))
metric_3.metric("Ticket médio", money(average_ticket))
metric_4.metric("Consultor líder", top_consultant)

chart_1, chart_2 = st.columns(2)
with chart_1:
    monthly = filtered.groupby("mes", as_index=False)["valor_total"].sum()
    fig_monthly = px.bar(monthly, x="mes", y="valor_total", title="Valor por mês")
    fig_monthly.update_traces(marker_color=branding["primary_color"])
    fig_monthly.update_layout(xaxis_title="Mês", yaxis_title="Valor", margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_monthly, width="stretch")

with chart_2:
    by_type = filtered.groupby("tipo", as_index=False)["valor_total"].sum()
    fig_type = px.pie(by_type, names="tipo", values="valor_total", hole=0.55, title="Participação por tipo")
    fig_type.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="Tipo")
    st.plotly_chart(fig_type, width="stretch")

consultant_summary = (
    filtered.groupby("consultor", as_index=False)
    .agg(Propostas=("_id", "count"), Valor_total=("valor_total", "sum"), Ticket_medio=("valor_total", "mean"))
    .sort_values("Valor_total", ascending=False)
)
st.markdown("### Desempenho por consultor")
st.dataframe(
    consultant_summary,
    width="stretch",
    hide_index=True,
    column_config={
        "consultor": "Consultor",
        "Propostas": "Propostas",
        "Valor_total": st.column_config.NumberColumn("Valor total", format="R$ %.2f"),
        "Ticket_medio": st.column_config.NumberColumn("Ticket médio", format="R$ %.2f"),
    },
)

st.markdown("### Histórico")
st.dataframe(
    filtered[["data_geracao", "consultor", "empresa", "tipo", "valor_total"]].sort_values("data_geracao", ascending=False),
    width="stretch",
    hide_index=True,
    column_config={
        "data_geracao": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
        "consultor": "Consultor",
        "empresa": "Cliente ou órgão",
        "tipo": "Tipo",
        "valor_total": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    },
)

if st.session_state.get("role") == "admin":
    with st.expander("Excluir proposta"):
        options = {
            f"{row['empresa']} — {row['tipo']} — {row['data_geracao'].strftime('%d/%m/%Y %H:%M')} — {money(row['valor_total'])}": row["_id"]
            for _, row in filtered.iterrows()
        }
        selected = st.selectbox("Proposta", list(options), index=None, placeholder="Selecione uma proposta")
        confirmation = st.checkbox("Confirmo a exclusão permanente")
        if st.button("Excluir proposta", type="primary", disabled=not selected or not confirmation):
            if db.delete_proposal(options[selected]):
                db.add_log(st.session_state.get("username", "sistema"), "Excluiu proposta", {"proposta": options[selected]})
                st.success("Proposta excluída.")
                st.rerun()
            else:
                st.error("Não foi possível excluir a proposta.")
