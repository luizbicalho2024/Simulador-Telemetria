from __future__ import annotations

import io
from collections import defaultdict

import pandas as pd
import plotly.express as px
import streamlit as st

from app_core.auth import require_auth
from app_core.financeiro_firestore import (
    connection_diagnostics,
    get_month_closures,
    get_monthly_metrics,
    get_terminal_snapshots,
    period_display,
    previous_period,
)
from app_core.ui import (
    apply_branding,
    configure_page,
    money,
    render_hero,
    render_sidebar,
    style_plotly_figure,
)

configure_page("Churn e Base Ativa")
branding = apply_branding()
require_auth()
render_sidebar()
render_hero(
    "Churn e base ativa",
    "Entenda mês a mês o que fez a carteira e o faturamento crescerem ou caírem, com visão por cliente e terminal.",
)


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value, default=0) -> int:
    try:
        return int(round(float(value or 0)))
    except (TypeError, ValueError):
        return int(default)


def _metric_record(item: dict) -> dict:
    return {
        "period_key": str(item.get("period_key") or ""),
        "cliente": str(item.get("cliente") or "").strip(),
        "receita": _safe_float(item.get("receita") if "receita" in item else item.get("valor_total")),
        "veiculos_faturados": _safe_int(item.get("veiculos_faturados")),
        "veiculos_ativos_fim_mes": _safe_int(item.get("veiculos_ativos_fim_mes")),
        "ativacoes": _safe_int(item.get("ativacoes")),
        "desativacoes": _safe_int(item.get("desativacoes")),
        "suspensoes": _safe_int(item.get("suspensoes")),
        "data_quality": str(item.get("data_quality") or "não informado"),
        "source": str(item.get("source") or "analytics"),
    }


def _sum_metric(records: list[dict], field: str) -> float:
    return sum(_safe_float(record.get(field)) for record in records)


def _money_delta(value: float) -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{money(value)}"


def _pct(value: float) -> str:
    return f"{value:+.2f}%".replace(".", ",")


def _classification(
    *,
    cliente: str,
    current: dict,
    previous: dict,
    selected_period: str,
    is_closed: bool,
    historical_active_periods: dict[str, set[str]],
) -> str:
    current_active = _safe_int(current.get("veiculos_ativos_fim_mes"))
    previous_active = _safe_int(previous.get("veiculos_ativos_fim_mes"))
    current_revenue = _safe_float(current.get("receita"))
    previous_revenue = _safe_float(previous.get("receita"))

    if previous_active > 0 and current_active <= 0:
        return "Churn total" if is_closed else "Sem dados no mês"

    if previous_active <= 0 and current_active > 0:
        older_periods = {period for period in historical_active_periods.get(cliente, set()) if period < selected_period}
        prior_period = previous_period(selected_period)
        older_periods.discard(prior_period)
        return "Reativação" if older_periods else "Novo cliente"

    if previous_active > 0 and current_active > 0:
        if current_active > previous_active or current_revenue > previous_revenue * 1.005:
            return "Expansão"
        if current_active < previous_active or current_revenue < previous_revenue * 0.995:
            return "Contração"
        return "Estável"

    return "Sem movimento"


def _build_excel(detail: pd.DataFrame, monthly: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        detail.to_excel(writer, index=False, sheet_name="Churn_Clientes")
        monthly.to_excel(writer, index=False, sheet_name="Evolucao_Mensal")
        for worksheet in writer.sheets.values():
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, max(1, worksheet.dim_rowmax), max(0, worksheet.dim_colmax))
            worksheet.set_column(0, max(0, worksheet.dim_colmax), 18)
    return output.getvalue()


def _snapshot_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    frame = pd.DataFrame(records)
    rename = {
        "terminal": "Terminal",
        "equipamento": "Equipamento",
        "placa": "Placa",
        "frota": "Frota",
        "modelo": "Modelo",
        "tipo": "Tipo",
        "condicao": "Condição",
        "categoria": "Categoria",
        "data_ativacao": "Data Ativação",
        "data_desativacao": "Data Desativação",
        "suspenso_dias_mes": "Dias Suspensos",
        "dias_a_faturar": "Dias a Faturar",
        "valor_unitario": "Valor Unitário",
        "valor_faturado": "Valor Faturado",
    }
    frame = frame.rename(columns=rename)
    preferred = [
        "Terminal",
        "Equipamento",
        "Placa",
        "Frota",
        "Modelo",
        "Tipo",
        "Condição",
        "Categoria",
        "Data Ativação",
        "Data Desativação",
        "Dias Suspensos",
        "Dias a Faturar",
        "Valor Unitário",
        "Valor Faturado",
    ]
    cols = [column for column in preferred if column in frame.columns]
    return frame[cols] if cols else frame


diagnostics = connection_diagnostics()
if not diagnostics.get("ok"):
    st.error("O Simulador ainda não conseguiu acessar o Firestore do Financeiro.")
    st.code(
        "Adicione no Streamlit Cloud do Simulador a seção [financeiro_service_account] "
        "com a conta de serviço do projeto Firebase financeiro.",
        language="text",
    )
    with st.expander("Diagnóstico técnico"):
        st.write(diagnostics.get("error", "Falha não identificada."))
    st.stop()

raw_metrics = get_monthly_metrics()
metrics = [_metric_record(item) for item in raw_metrics]
metrics = [item for item in metrics if item["period_key"] and item["cliente"]]
if not metrics:
    st.info(
        "Ainda não há histórico financeiro suficiente para a análise. No Financeiro, salve um faturamento "
        "ou use a ação de reconstrução do histórico existente."
    )
    st.stop()

closures = {str(item.get("period_key") or ""): item for item in get_month_closures() if item.get("period_key")}
periods = sorted({item["period_key"] for item in metrics})
closed_periods = sorted(
    period for period, item in closures.items() if str(item.get("status") or "").lower() == "closed" and period in periods
)
default_period = closed_periods[-1] if closed_periods else periods[-1]

filter_1, filter_2, filter_3 = st.columns([1.2, 1.8, 1.4])
selected_period = filter_1.selectbox(
    "Mês de análise",
    periods,
    index=periods.index(default_period),
    format_func=period_display,
)
selected_previous = previous_period(selected_period)
clients = sorted({item["cliente"] for item in metrics})
selected_clients = filter_2.multiselect("Clientes", clients, default=[])
classification_filter = filter_3.multiselect(
    "Movimentos",
    ["Churn total", "Contração", "Estável", "Expansão", "Novo cliente", "Reativação", "Sem dados no mês", "Sem movimento"],
    default=[],
)

is_closed = str(closures.get(selected_period, {}).get("status") or "").lower() == "closed"
if not is_closed:
    st.warning(
        f"{period_display(selected_period)} não possui fechamento mensal registrado. Clientes ausentes no mês não serão "
        "tratados como churn total para evitar falso positivo."
    )

by_period_client = {(item["period_key"], item["cliente"]): item for item in metrics}
historical_active_periods: dict[str, set[str]] = defaultdict(set)
for item in metrics:
    if _safe_int(item.get("veiculos_ativos_fim_mes")) > 0:
        historical_active_periods[item["cliente"]].add(item["period_key"])

current_clients = {item["cliente"] for item in metrics if item["period_key"] == selected_period}
previous_clients = {item["cliente"] for item in metrics if item["period_key"] == selected_previous}
comparison_clients = current_clients | previous_clients

rows = []
for cliente in sorted(comparison_clients):
    current = by_period_client.get((selected_period, cliente), {})
    previous = by_period_client.get((selected_previous, cliente), {})
    classification = _classification(
        cliente=cliente,
        current=current,
        previous=previous,
        selected_period=selected_period,
        is_closed=is_closed,
        historical_active_periods=historical_active_periods,
    )
    current_revenue = _safe_float(current.get("receita"))
    previous_revenue = _safe_float(previous.get("receita"))
    previous_active = _safe_int(previous.get("veiculos_ativos_fim_mes"))
    current_active = _safe_int(current.get("veiculos_ativos_fim_mes"))
    rows.append(
        {
            "Cliente": cliente,
            "Classificação": classification,
            "Receita anterior": previous_revenue,
            "Receita atual": current_revenue,
            "Δ Receita": current_revenue - previous_revenue,
            "Δ Receita %": ((current_revenue / previous_revenue - 1) * 100) if previous_revenue > 0 else None,
            "Veículos anterior": previous_active,
            "Veículos atual": current_active,
            "Δ Veículos": current_active - previous_active,
            "Ativações": _safe_int(current.get("ativacoes")),
            "Desativações": _safe_int(current.get("desativacoes")),
            "Suspensões": _safe_int(current.get("suspensoes")),
            "Qualidade": str(current.get("data_quality") or previous.get("data_quality") or "sem dados"),
        }
    )

detail_all = pd.DataFrame(rows)
detail = detail_all.copy()
if selected_clients:
    detail = detail[detail["Cliente"].isin(selected_clients)]
if classification_filter:
    detail = detail[detail["Classificação"].isin(classification_filter)]

current_records = [item for item in metrics if item["period_key"] == selected_period]
previous_records = [item for item in metrics if item["period_key"] == selected_previous]
current_revenue = _sum_metric(current_records, "receita")
previous_revenue = _sum_metric(previous_records, "receita")
revenue_delta = current_revenue - previous_revenue
revenue_delta_pct = (revenue_delta / previous_revenue * 100) if previous_revenue else 0.0
current_active = int(_sum_metric(current_records, "veiculos_ativos_fim_mes"))
previous_active = int(_sum_metric(previous_records, "veiculos_ativos_fim_mes"))
deactivations = int(_sum_metric(current_records, "desativacoes"))
activations = int(_sum_metric(current_records, "ativacoes"))
client_churn = int((detail_all["Classificação"] == "Churn total").sum()) if not detail_all.empty else 0
vehicle_churn_rate = (deactivations / previous_active * 100) if previous_active else 0.0

metric_1, metric_2, metric_3, metric_4, metric_5, metric_6 = st.columns(6)
metric_1.metric("Faturamento", money(current_revenue), _money_delta(revenue_delta))
metric_2.metric("Variação M/M", _pct(revenue_delta_pct))
metric_3.metric("Clientes ativos", sum(1 for item in current_records if _safe_int(item.get("veiculos_ativos_fim_mes")) > 0))
metric_4.metric("Churn clientes", client_churn)
metric_5.metric("Base ativa", current_active, f"{current_active - previous_active:+d} veículos")
metric_6.metric("Churn veículos", _pct(vehicle_churn_rate), f"{deactivations} desativações")

st.markdown("### O que explica a variação")
impact = detail.groupby("Classificação", as_index=False)["Δ Receita"].sum() if not detail.empty else pd.DataFrame()
if not impact.empty:
    impact = impact.sort_values("Δ Receita")
    fig_impact = px.bar(
        impact,
        x="Classificação",
        y="Δ Receita",
        title=f"Impacto por movimento — {period_display(selected_period)} vs. {period_display(selected_previous)}",
        text_auto=".2s",
    )
    style_plotly_figure(fig_impact, branding)
    fig_impact.update_layout(xaxis_title="", yaxis_title="Variação de receita", margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig_impact, width="stretch")

monthly_rows = []
for period in periods:
    period_records = [item for item in metrics if item["period_key"] == period]
    monthly_rows.append(
        {
            "Período": period,
            "Mês": period_display(period),
            "Faturamento": _sum_metric(period_records, "receita"),
            "Base ativa": int(_sum_metric(period_records, "veiculos_ativos_fim_mes")),
            "Ativações": int(_sum_metric(period_records, "ativacoes")),
            "Desativações": int(_sum_metric(period_records, "desativacoes")),
            "Suspensões": int(_sum_metric(period_records, "suspensoes")),
        }
    )
monthly = pd.DataFrame(monthly_rows).sort_values("Período")

chart_1, chart_2 = st.columns(2)
with chart_1:
    fig_revenue = px.line(monthly, x="Mês", y="Faturamento", markers=True, title="Evolução do faturamento")
    style_plotly_figure(fig_revenue, branding)
    fig_revenue.update_layout(xaxis_title="", yaxis_title="Faturamento", margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig_revenue, width="stretch")
with chart_2:
    fig_base = px.line(monthly, x="Mês", y="Base ativa", markers=True, title="Evolução da base ativa")
    style_plotly_figure(fig_base, branding)
    fig_base.update_layout(xaxis_title="", yaxis_title="Veículos", margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig_base, width="stretch")

fig_moves = px.bar(
    monthly,
    x="Mês",
    y=["Ativações", "Desativações"],
    barmode="group",
    title="Ativações x desativações",
)
style_plotly_figure(fig_moves, branding)
fig_moves.update_layout(xaxis_title="", yaxis_title="Terminais", legend_title_text="", margin=dict(l=10, r=10, t=55, b=10))
st.plotly_chart(fig_moves, width="stretch")

st.markdown("### Clientes que explicam a mudança")
if detail.empty:
    st.info("Nenhum cliente corresponde aos filtros selecionados.")
else:
    detail_sorted = detail.reindex(detail["Δ Receita"].abs().sort_values(ascending=False).index)
    st.dataframe(
        detail_sorted,
        width="stretch",
        hide_index=True,
        column_config={
            "Receita anterior": st.column_config.NumberColumn(format="R$ %.2f"),
            "Receita atual": st.column_config.NumberColumn(format="R$ %.2f"),
            "Δ Receita": st.column_config.NumberColumn(format="R$ %.2f"),
            "Δ Receita %": st.column_config.NumberColumn(format="%.2f%%"),
            "Veículos anterior": st.column_config.NumberColumn(format="%d"),
            "Veículos atual": st.column_config.NumberColumn(format="%d"),
            "Δ Veículos": st.column_config.NumberColumn(format="%d"),
            "Ativações": st.column_config.NumberColumn(format="%d"),
            "Desativações": st.column_config.NumberColumn(format="%d"),
            "Suspensões": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.download_button(
        "Exportar análise em Excel",
        data=_build_excel(detail_sorted, monthly),
        file_name=f"churn_comercial_{selected_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

st.markdown("---")
st.markdown("### Drill-down por cliente")
drill_clients = sorted(detail["Cliente"].tolist()) if not detail.empty else sorted(comparison_clients)
selected_client = st.selectbox("Cliente", drill_clients, index=None, placeholder="Selecione um cliente")
if selected_client:
    row = next((item for item in rows if item["Cliente"] == selected_client), None)
    if row:
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Classificação", row["Classificação"])
        d2.metric("Receita", money(row["Receita atual"]), _money_delta(row["Δ Receita"]))
        d3.metric("Base ativa", row["Veículos atual"], f"{row['Δ Veículos']:+d}")
        d4.metric("Ativações / desativações", f"{row['Ativações']} / {row['Desativações']}")

    current_snapshots = [
        item for item in get_terminal_snapshots(selected_period) if str(item.get("cliente") or "").strip() == selected_client
    ]
    previous_snapshots = [
        item for item in get_terminal_snapshots(selected_previous) if str(item.get("cliente") or "").strip() == selected_client
    ]

    tab_current, tab_previous = st.tabs(
        [f"{period_display(selected_period)}", f"{period_display(selected_previous)}"]
    )
    with tab_current:
        current_frame = _snapshot_dataframe(current_snapshots)
        if current_frame.empty:
            st.info("Não há snapshot item a item deste cliente neste período.")
        else:
            st.dataframe(
                current_frame,
                width="stretch",
                hide_index=True,
                column_config={
                    "Valor Unitário": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Valor Faturado": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Data Ativação": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                    "Data Desativação": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                },
            )
    with tab_previous:
        previous_frame = _snapshot_dataframe(previous_snapshots)
        if previous_frame.empty:
            st.info("Não há snapshot item a item deste cliente no período anterior.")
        else:
            st.dataframe(
                previous_frame,
                width="stretch",
                hide_index=True,
                column_config={
                    "Valor Unitário": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Valor Faturado": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Data Ativação": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                    "Data Desativação": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                },
            )

with st.expander("Qualidade e origem dos dados", expanded=False):
    quality = pd.DataFrame(metrics)
    summary = (
        quality.groupby("data_quality", as_index=False)
        .agg(Registros=("cliente", "count"), Clientes=("cliente", "nunique"), Periodos=("period_key", "nunique"))
        .sort_values("Registros", ascending=False)
    )
    st.dataframe(summary, width="stretch", hide_index=True)
    st.caption(
        "detalhado/historico_detalhado: possui item a item e permite churn de terminais com maior precisão. "
        "resumo_legado: registro antigo sem detalhe; receita é válida, mas base e movimentos podem ser aproximados."
    )
