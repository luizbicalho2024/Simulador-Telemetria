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
render_hero(
    "Dashboard de propostas",
    "Acompanhe volume, valor, perfil de venda, aprovação e desempenho por consultor.",
)

STATUS_LABELS = {
    "approved": "Aprovada",
    "pending_approval": "Aguardando aprovação",
    "rejected": "Rejeitada",
    "legacy": "Legado / sem aprovação",
}

proposals = db.get_all_proposals()
if not proposals:
    st.info("Ainda não há propostas registradas.")
    st.stop()

df = pd.DataFrame(proposals)
df["_id"] = df["_id"].astype(str)
df["data_geracao"] = pd.to_datetime(df["data_geracao"], errors="coerce")
df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0.0)
df = df.dropna(subset=["data_geracao"])
for text_column, fallback in (
    ("consultor", "Não informado"),
    ("tipo", "Não informado"),
    ("empresa", "Não informado"),
):
    if text_column not in df.columns:
        df[text_column] = fallback
    else:
        df[text_column] = df[text_column].fillna(fallback).astype(str)
df["mes"] = df["data_geracao"].dt.to_period("M").astype(str)
if "status" not in df.columns:
    df["status"] = "legacy"
else:
    df["status"] = df["status"].fillna("legacy").astype(str)
df["status_label"] = df["status"].map(STATUS_LABELS).fillna(df["status"])

with st.expander("Filtros", expanded=False):
    filter_1, filter_2, filter_3, filter_4 = st.columns(4)
    consultants = sorted(df["consultor"].dropna().astype(str).unique().tolist())
    types = sorted(df["tipo"].dropna().astype(str).unique().tolist())
    statuses = sorted(df["status"].dropna().astype(str).unique().tolist())
    selected_consultants = filter_1.multiselect("Consultores", consultants, default=consultants)
    selected_types = filter_2.multiselect("Tipos", types, default=types)
    selected_statuses = filter_3.multiselect(
        "Status",
        statuses,
        default=statuses,
        format_func=lambda value: STATUS_LABELS.get(value, value),
    )
    min_date = df["data_geracao"].min().date()
    max_date = df["data_geracao"].max().date()
    selected_dates = filter_4.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

filtered = df[
    df["consultor"].isin(selected_consultants)
    & df["tipo"].isin(selected_types)
    & df["status"].isin(selected_statuses)
].copy()
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
pending_count = int((filtered["status"] == "pending_approval").sum())
metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
metric_1.metric("Propostas", len(filtered))
metric_2.metric("Valor total", money(filtered["valor_total"].sum()))
metric_3.metric("Ticket médio", money(average_ticket))
metric_4.metric("Pendentes", pending_count)
metric_5.metric("Consultor líder", top_consultant)

chart_1, chart_2 = st.columns(2)
with chart_1:
    monthly = filtered.groupby("mes", as_index=False)["valor_total"].sum()
    fig_monthly = px.bar(monthly, x="mes", y="valor_total", title="Valor por mês")
    fig_monthly.update_traces(marker_color=branding["primary_color"])
    fig_monthly.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valor",
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor=branding["background_color"],
        plot_bgcolor=branding["background_color"],
        font_color=branding["text_color"],
    )
    st.plotly_chart(fig_monthly, width="stretch")

with chart_2:
    by_status = filtered.groupby("status_label", as_index=False)["valor_total"].sum()
    color_sequence = [
        branding["primary_color"],
        branding["accent_color"],
        branding["secondary_color"],
        branding["muted_color"],
    ]
    fig_status = px.pie(
        by_status,
        names="status_label",
        values="valor_total",
        hole=0.55,
        title="Participação por status",
        color_discrete_sequence=color_sequence,
    )
    fig_status.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        legend_title_text="Status",
        paper_bgcolor=branding["background_color"],
        font_color=branding["text_color"],
    )
    st.plotly_chart(fig_status, width="stretch")

consultant_summary = (
    filtered.groupby("consultor", as_index=False)
    .agg(
        Propostas=("_id", "count"),
        Valor_total=("valor_total", "sum"),
        Ticket_medio=("valor_total", "mean"),
        Pendentes=("status", lambda values: int((values == "pending_approval").sum())),
    )
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
        "Pendentes": "Pendentes",
        "Valor_total": st.column_config.NumberColumn("Valor total", format="R$ %.2f"),
        "Ticket_medio": st.column_config.NumberColumn("Ticket médio", format="R$ %.2f"),
    },
)

st.markdown("### Histórico")
history_columns = [
    "data_geracao",
    "consultor",
    "empresa",
    "tipo",
    "status_label",
    "valor_total",
]
st.dataframe(
    filtered[history_columns].sort_values("data_geracao", ascending=False),
    width="stretch",
    hide_index=True,
    column_config={
        "data_geracao": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
        "consultor": "Consultor",
        "empresa": "Cliente ou órgão",
        "tipo": "Tipo",
        "status_label": "Status",
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
                db.add_log(
                    st.session_state.get("username", "sistema"),
                    "Excluiu proposta",
                    {"proposta": options[selected]},
                )
                st.success("Proposta excluída.")
                st.rerun()
            else:
                st.error("Não foi possível excluir a proposta.")
