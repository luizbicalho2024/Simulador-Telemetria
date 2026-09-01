from __future__ import annotations

import hashlib
import html
import io
import json
from collections import defaultdict

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app_core.auth import require_auth
from app_core.financeiro_mongo import (
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
)

AMCHARTS_VERSION = "5.20.3"
MOVEMENT_ORDER = [
    "Churn total",
    "Contração",
    "Estável",
    "Expansão",
    "Novo cliente",
    "Reativação",
    "Sem dados no mês",
    "Sem movimento",
]
MOVEMENT_COLORS = {
    "Churn total": "#DC2626",
    "Contração": "#EA580C",
    "Estável": "#64748B",
    "Expansão": "#16A34A",
    "Novo cliente": "#2563EB",
    "Reativação": "#7C3AED",
    "Sem dados no mês": "#94A3B8",
    "Sem movimento": "#CBD5E1",
}

configure_page("Churn e Base Ativa")
branding = apply_branding()
require_auth()
render_sidebar()
render_hero(
    "Churn e base ativa",
    "Leia rapidamente o que fez a carteira crescer ou cair, identifique os clientes que mais impactaram a receita e acompanhe a evolução da base.",
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


def _safe_hex_color(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    if (
        len(text) == 7
        and text.startswith("#")
        and all(character in "0123456789abcdefABCDEF" for character in text[1:])
    ):
        return text
    return fallback


def _metric_record(item: dict) -> dict:
    return {
        "period_key": str(item.get("period_key") or ""),
        "cliente": str(item.get("cliente") or "").strip(),
        "receita": _safe_float(
            item.get("receita")
            if "receita" in item
            else item.get("valor_total")
        ),
        "veiculos_faturados": _safe_int(item.get("veiculos_faturados")),
        "veiculos_ativos_fim_mes": _safe_int(
            item.get("veiculos_ativos_fim_mes")
        ),
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
        older_periods = {
            period
            for period in historical_active_periods.get(cliente, set())
            if period < selected_period
        }
        prior_period = previous_period(selected_period)
        older_periods.discard(prior_period)
        return "Reativação" if older_periods else "Novo cliente"

    if previous_active > 0 and current_active > 0:
        if (
            current_active > previous_active
            or current_revenue > previous_revenue * 1.005
        ):
            return "Expansão"
        if (
            current_active < previous_active
            or current_revenue < previous_revenue * 0.995
        ):
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
            worksheet.autofilter(
                0,
                0,
                max(1, worksheet.dim_rowmax),
                max(0, worksheet.dim_colmax),
            )
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


def _chart_payload(data: list[dict]) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")


def _render_amcharts_chart(
    chart_kind: str,
    data: list[dict],
    *,
    height: int = 390,
) -> None:
    if not data:
        st.info("Não há dados suficientes para este gráfico.")
        return

    chart_id = "churn-" + hashlib.sha1(
        (chart_kind + "|" + _chart_payload(data)).encode("utf-8")
    ).hexdigest()[:12]

    primary = _safe_hex_color(branding.get("primary_color"), "#0F766E")
    secondary = _safe_hex_color(branding.get("secondary_color"), "#0F172A")
    accent = _safe_hex_color(branding.get("accent_color"), "#2563EB")
    surface = _safe_hex_color(branding.get("surface_color"), "#FFFFFF")
    text = _safe_hex_color(branding.get("text_color"), "#0F172A")
    muted = _safe_hex_color(branding.get("muted_color"), "#64748B")
    positive = "#16A34A"
    negative = "#DC2626"
    warning = "#D97706"
    violet = "#7C3AED"

    html = r'''
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
html, body { margin: 0; padding: 0; background: transparent; overflow: hidden; }
body { font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.chart-shell {
    width: 100%;
    box-sizing: border-box;
    border: 1px solid rgba(100, 116, 139, .18);
    border-radius: 16px;
    background: __SURFACE__;
    padding: 10px 10px 4px;
}
#__CHART_ID__ {
    width: 100%;
    height: __HEIGHT__px;
    min-height: __HEIGHT__px;
    position: relative;
    overflow: hidden;
}
#__CHART_ID__ > div {
    width: 100% !important;
    height: 100% !important;
}
.chart-fallback {
    color: __MUTED__;
    font-size: 13px;
    padding: 18px;
    box-sizing: border-box;
}
</style>
<script src="https://cdn.amcharts.com/lib/version/5.20.3/index.js"></script>
<script src="https://cdn.amcharts.com/lib/version/5.20.3/xy.js"></script>
<script src="https://cdn.amcharts.com/lib/version/5.20.3/percent.js"></script>
<script src="https://cdn.amcharts.com/lib/version/5.20.3/themes/Animated.js"></script>
</head>
<body>
<div class="chart-shell">
    <div id="__CHART_ID__"></div>
</div>

<script>
function showChartError(message) {
    const host = document.getElementById("__CHART_ID__");
    if (!host) return;
    host.innerHTML =
        '<div class="chart-fallback"><strong>Gráfico indisponível.</strong><br>' +
        message +
        '<br><small>Os indicadores e tabelas da página continuam disponíveis.</small></div>';
}

if (
    typeof am5 === "undefined" ||
    typeof am5xy === "undefined" ||
    typeof am5percent === "undefined"
) {
    showChartError(
        "Não foi possível carregar a biblioteca amCharts. Verifique bloqueio de CDN, proxy ou política de conteúdo do navegador."
    );
} else {
am5.ready(function() {
    try {
        const data = __DATA__;
        const kind = "__KIND__";

        function color(hex) {
            return am5.color(parseInt(hex.replace("#", ""), 16));
        }

        function styleCategoryRenderer(renderer) {
            renderer.labels.template.setAll({
                fill: color("__MUTED__"),
                fontSize: 11
            });
            renderer.grid.template.setAll({
                stroke: color("__MUTED__"),
                strokeOpacity: 0.08
            });
        }

        function styleValueRenderer(renderer) {
            renderer.labels.template.setAll({
                fill: color("__MUTED__"),
                fontSize: 11
            });
            renderer.grid.template.setAll({
                stroke: color("__MUTED__"),
                strokeOpacity: 0.10
            });
        }

        const host = document.getElementById("__CHART_ID__");
        if (!host) {
            throw new Error("Container do gráfico não encontrado.");
        }

        // O amCharts adiciona seus elementos ao container sem remover filhos
        // preexistentes. Mantemos o host totalmente limpo para evitar texto
        // residual e deslocamento do canvas.
        host.replaceChildren();
        host.setAttribute("aria-busy", "false");

        const root = am5.Root.new(host);
        root.setThemes([am5themes_Animated.new(root)]);

        if (kind === "impact") {
            const chart = root.container.children.push(
                am5xy.XYChart.new(root, {
                    panX: false,
                    panY: false,
                    wheelX: "none",
                    wheelY: "none",
                    paddingLeft: 4,
                    paddingRight: 18
                })
            );

            const yRenderer = am5xy.AxisRendererY.new(root, {
                inversed: true,
                minGridDistance: 28
            });
            styleCategoryRenderer(yRenderer);
            yRenderer.grid.template.set("forceHidden", true);

            const yAxis = chart.yAxes.push(
                am5xy.CategoryAxis.new(root, {
                    categoryField: "classification",
                    renderer: yRenderer
                })
            );
            yAxis.data.setAll(data);

            const xRenderer = am5xy.AxisRendererX.new(root, {});
            styleValueRenderer(xRenderer);
            const xAxis = chart.xAxes.push(
                am5xy.ValueAxis.new(root, {
                    renderer: xRenderer,
                    extraMin: 0.08,
                    extraMax: 0.08
                })
            );

            const zeroItem = xAxis.makeDataItem({ value: 0 });
            const zeroRange = xAxis.createAxisRange(zeroItem);
            zeroRange.get("grid").setAll({
                stroke: color("__MUTED__"),
                strokeOpacity: 0.55,
                strokeWidth: 1
            });

            const series = chart.series.push(
                am5xy.ColumnSeries.new(root, {
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueXField: "deltaRevenue",
                    categoryYField: "classification",
                    tooltip: am5.Tooltip.new(root, {
                        labelText: "[bold]{categoryY}[/] · Δ receita {deltaLabel} · {clients} cliente(s)"
                    })
                })
            );

            series.columns.template.setAll({
                height: am5.percent(68),
                cornerRadiusTR: 5,
                cornerRadiusBR: 5,
                cornerRadiusTL: 5,
                cornerRadiusBL: 5,
                strokeOpacity: 0
            });
            series.columns.template.adapters.add("fill", function(fill, target) {
                const ctx = target.dataItem && target.dataItem.dataContext;
                return ctx && ctx.color ? color(ctx.color) : color("__PRIMARY__");
            });
            series.columns.template.adapters.add("stroke", function(stroke, target) {
                const ctx = target.dataItem && target.dataItem.dataContext;
                return ctx && ctx.color ? color(ctx.color) : color("__PRIMARY__");
            });

            series.data.setAll(data);
            series.appear(600);
            chart.appear(600, 80);
            chart.set("cursor", am5xy.XYCursor.new(root, {
                behavior: "none",
                yAxis: yAxis
            }));
        }

        if (kind === "mix") {
            const chart = root.container.children.push(
                am5percent.PieChart.new(root, {
                    layout: root.verticalLayout,
                    innerRadius: am5.percent(60)
                })
            );

            const series = chart.series.push(
                am5percent.PieSeries.new(root, {
                    valueField: "clients",
                    categoryField: "classification",
                    alignLabels: false,
                    tooltip: am5.Tooltip.new(root, {
                        labelText: "[bold]{category}[/] · {value} cliente(s) · {valuePercentTotal.formatNumber('0.0')}%"
                    })
                })
            );

            series.labels.template.setAll({
                text: "{category}: {value}",
                fontSize: 11,
                fill: color("__TEXT__"),
                maxWidth: 160,
                oversizedBehavior: "truncate"
            });
            series.ticks.template.setAll({
                stroke: color("__MUTED__"),
                strokeOpacity: 0.45
            });
            series.slices.template.setAll({
                stroke: color("__SURFACE__"),
                strokeWidth: 2
            });
            series.slices.template.adapters.add("fill", function(fill, target) {
                const ctx = target.dataItem && target.dataItem.dataContext;
                return ctx && ctx.color ? color(ctx.color) : color("__ACCENT__");
            });
            series.slices.template.adapters.add("stroke", function() {
                return color("__SURFACE__");
            });

            series.data.setAll(data);

            chart.seriesContainer.children.push(
                am5.Label.new(root, {
                    text: data.reduce(function(total, row) {
                        return total + Number(row.clients || 0);
                    }, 0) + " clientes",
                    textAlign: "center",
                    centerX: am5.p50,
                    centerY: am5.p50,
                    x: am5.p50,
                    y: am5.p50,
                    fill: color("__TEXT__"),
                    fontSize: 18,
                    fontWeight: "600"
                })
            );

            series.appear(700, 80);
        }

        if (kind === "overview") {
            const chart = root.container.children.push(
                am5xy.XYChart.new(root, {
                    panX: true,
                    panY: false,
                    wheelX: "panX",
                    wheelY: "none",
                    layout: root.verticalLayout,
                    paddingLeft: 6,
                    paddingRight: 10
                })
            );

            const xRenderer = am5xy.AxisRendererX.new(root, {
                minGridDistance: 45
            });
            styleCategoryRenderer(xRenderer);
            xRenderer.labels.template.setAll({
                rotation: data.length > 12 ? -35 : 0,
                centerY: data.length > 12 ? am5.p50 : am5.p0,
                centerX: data.length > 12 ? am5.p100 : am5.p50,
                paddingTop: 8
            });
            const xAxis = chart.xAxes.push(
                am5xy.CategoryAxis.new(root, {
                    categoryField: "month",
                    renderer: xRenderer
                })
            );
            xAxis.data.setAll(data);

            const leftRenderer = am5xy.AxisRendererY.new(root, {});
            styleValueRenderer(leftRenderer);
            const revenueAxis = chart.yAxes.push(
                am5xy.ValueAxis.new(root, {
                    renderer: leftRenderer,
                    extraMax: 0.12
                })
            );

            const rightRenderer = am5xy.AxisRendererY.new(root, {
                opposite: true
            });
            styleValueRenderer(rightRenderer);
            rightRenderer.grid.template.set("forceHidden", true);
            const baseAxis = chart.yAxes.push(
                am5xy.ValueAxis.new(root, {
                    renderer: rightRenderer,
                    extraMax: 0.12
                })
            );

            const revenueSeries = chart.series.push(
                am5xy.LineSeries.new(root, {
                    name: "Faturamento",
                    xAxis: xAxis,
                    yAxis: revenueAxis,
                    categoryXField: "month",
                    valueYField: "revenue",
                    stroke: color("__PRIMARY__"),
                    fill: color("__PRIMARY__"),
                    tooltip: am5.Tooltip.new(root, {
                        labelText: "[bold]Faturamento[/] · {month} · {revenueLabel}"
                    })
                })
            );
            revenueSeries.strokes.template.setAll({ strokeWidth: 3 });
            revenueSeries.fills.template.setAll({
                visible: true,
                fillOpacity: 0.08
            });
            revenueSeries.bullets.push(function() {
                return am5.Bullet.new(root, {
                    sprite: am5.Circle.new(root, {
                        radius: 4,
                        fill: color("__PRIMARY__"),
                        stroke: color("__SURFACE__"),
                        strokeWidth: 2
                    })
                });
            });
            revenueSeries.data.setAll(data);

            const baseSeries = chart.series.push(
                am5xy.LineSeries.new(root, {
                    name: "Base ativa",
                    xAxis: xAxis,
                    yAxis: baseAxis,
                    categoryXField: "month",
                    valueYField: "activeBase",
                    stroke: color("__ACCENT__"),
                    fill: color("__ACCENT__"),
                    tooltip: am5.Tooltip.new(root, {
                        labelText: "[bold]Base ativa[/] · {month} · {activeBase} veículos"
                    })
                })
            );
            baseSeries.strokes.template.setAll({
                strokeWidth: 3,
                strokeDasharray: [7, 4]
            });
            baseSeries.bullets.push(function() {
                return am5.Bullet.new(root, {
                    sprite: am5.Circle.new(root, {
                        radius: 4,
                        fill: color("__ACCENT__"),
                        stroke: color("__SURFACE__"),
                        strokeWidth: 2
                    })
                });
            });
            baseSeries.data.setAll(data);

            const legend = chart.children.push(
                am5.Legend.new(root, {
                    centerX: am5.p50,
                    x: am5.p50,
                    marginTop: 8
                })
            );
            legend.labels.template.setAll({
                fill: color("__TEXT__"),
                fontSize: 11
            });
            legend.valueLabels.template.set("forceHidden", true);
            legend.data.setAll(chart.series.values);

            chart.set("cursor", am5xy.XYCursor.new(root, {
                behavior: "none",
                xAxis: xAxis
            }));
            revenueSeries.appear(650);
            baseSeries.appear(650);
            chart.appear(650, 80);
        }

        if (kind === "moves") {
            const chart = root.container.children.push(
                am5xy.XYChart.new(root, {
                    panX: true,
                    panY: false,
                    wheelX: "panX",
                    wheelY: "none",
                    layout: root.verticalLayout,
                    paddingLeft: 6,
                    paddingRight: 12
                })
            );

            const xRenderer = am5xy.AxisRendererX.new(root, {
                minGridDistance: 42
            });
            styleCategoryRenderer(xRenderer);
            xRenderer.labels.template.setAll({
                rotation: data.length > 12 ? -35 : 0,
                centerY: data.length > 12 ? am5.p50 : am5.p0,
                centerX: data.length > 12 ? am5.p100 : am5.p50,
                paddingTop: 8
            });
            const xAxis = chart.xAxes.push(
                am5xy.CategoryAxis.new(root, {
                    categoryField: "month",
                    renderer: xRenderer
                })
            );
            xAxis.data.setAll(data);

            const yRenderer = am5xy.AxisRendererY.new(root, {});
            styleValueRenderer(yRenderer);
            const yAxis = chart.yAxes.push(
                am5xy.ValueAxis.new(root, {
                    renderer: yRenderer,
                    extraMax: 0.12
                })
            );

            function addColumns(name, field, seriesColor) {
                const series = chart.series.push(
                    am5xy.ColumnSeries.new(root, {
                        name: name,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        categoryXField: "month",
                        valueYField: field,
                        clustered: true,
                        fill: color(seriesColor),
                        stroke: color(seriesColor),
                        tooltip: am5.Tooltip.new(root, {
                            labelText: "[bold]" + name + "[/] · {month} · {valueY}"
                        })
                    })
                );
                series.columns.template.setAll({
                    width: am5.percent(70),
                    strokeOpacity: 0,
                    cornerRadiusTL: 4,
                    cornerRadiusTR: 4
                });
                series.data.setAll(data);
                return series;
            }

            addColumns("Ativações", "activations", "__POSITIVE__");
            addColumns("Desativações", "deactivations", "__NEGATIVE__");
            addColumns("Suspensões", "suspensions", "__WARNING__");

            const netSeries = chart.series.push(
                am5xy.LineSeries.new(root, {
                    name: "Saldo líquido",
                    xAxis: xAxis,
                    yAxis: yAxis,
                    categoryXField: "month",
                    valueYField: "net",
                    stroke: color("__VIOLET__"),
                    fill: color("__VIOLET__"),
                    tooltip: am5.Tooltip.new(root, {
                        labelText: "[bold]Saldo líquido[/] · {month} · {net}"
                    })
                })
            );
            netSeries.strokes.template.setAll({ strokeWidth: 3 });
            netSeries.bullets.push(function() {
                return am5.Bullet.new(root, {
                    sprite: am5.Circle.new(root, {
                        radius: 4,
                        fill: color("__VIOLET__"),
                        stroke: color("__SURFACE__"),
                        strokeWidth: 2
                    })
                });
            });
            netSeries.data.setAll(data);

            const zeroItem = yAxis.makeDataItem({ value: 0 });
            const zeroRange = yAxis.createAxisRange(zeroItem);
            zeroRange.get("grid").setAll({
                stroke: color("__MUTED__"),
                strokeOpacity: 0.55,
                strokeWidth: 1
            });

            const legend = chart.children.push(
                am5.Legend.new(root, {
                    centerX: am5.p50,
                    x: am5.p50,
                    marginTop: 8
                })
            );
            legend.labels.template.setAll({
                fill: color("__TEXT__"),
                fontSize: 11
            });
            legend.valueLabels.template.set("forceHidden", true);
            legend.data.setAll(chart.series.values);

            chart.set("cursor", am5xy.XYCursor.new(root, {
                behavior: "none",
                xAxis: xAxis
            }));
            chart.appear(650, 80);
        }

        if (kind === "movers") {
            const chart = root.container.children.push(
                am5xy.XYChart.new(root, {
                    panX: false,
                    panY: true,
                    wheelX: "none",
                    wheelY: "panY",
                    paddingLeft: 6,
                    paddingRight: 18
                })
            );

            const yRenderer = am5xy.AxisRendererY.new(root, {
                inversed: true,
                minGridDistance: 25
            });
            styleCategoryRenderer(yRenderer);
            yRenderer.grid.template.set("forceHidden", true);
            yRenderer.labels.template.setAll({
                maxWidth: 220,
                oversizedBehavior: "truncate"
            });

            const yAxis = chart.yAxes.push(
                am5xy.CategoryAxis.new(root, {
                    categoryField: "client",
                    renderer: yRenderer
                })
            );
            yAxis.data.setAll(data);

            const xRenderer = am5xy.AxisRendererX.new(root, {});
            styleValueRenderer(xRenderer);
            const xAxis = chart.xAxes.push(
                am5xy.ValueAxis.new(root, {
                    renderer: xRenderer,
                    extraMin: 0.08,
                    extraMax: 0.08
                })
            );

            const zeroItem = xAxis.makeDataItem({ value: 0 });
            const zeroRange = xAxis.createAxisRange(zeroItem);
            zeroRange.get("grid").setAll({
                stroke: color("__MUTED__"),
                strokeOpacity: 0.65,
                strokeWidth: 1
            });

            const series = chart.series.push(
                am5xy.ColumnSeries.new(root, {
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueXField: "deltaRevenue",
                    categoryYField: "client",
                    tooltip: am5.Tooltip.new(root, {
                        labelText: "[bold]{client}[/] · {classification} · Δ {deltaLabel} · veículos {vehicleDeltaLabel}"
                    })
                })
            );
            series.columns.template.setAll({
                height: am5.percent(66),
                strokeOpacity: 0,
                cornerRadiusTR: 5,
                cornerRadiusBR: 5,
                cornerRadiusTL: 5,
                cornerRadiusBL: 5
            });
            series.columns.template.adapters.add("fill", function(fill, target) {
                const ctx = target.dataItem && target.dataItem.dataContext;
                if (!ctx) return color("__PRIMARY__");
                return Number(ctx.deltaRevenue || 0) < 0
                    ? color("__NEGATIVE__")
                    : color("__POSITIVE__");
            });
            series.columns.template.adapters.add("stroke", function(stroke, target) {
                const ctx = target.dataItem && target.dataItem.dataContext;
                if (!ctx) return color("__PRIMARY__");
                return Number(ctx.deltaRevenue || 0) < 0
                    ? color("__NEGATIVE__")
                    : color("__POSITIVE__");
            });
            series.data.setAll(data);

            chart.set("cursor", am5xy.XYCursor.new(root, {
                behavior: "none",
                yAxis: yAxis
            }));
            series.appear(650);
            chart.appear(650, 80);
        }
    } catch (error) {
        console.error("Falha ao renderizar gráfico amCharts de churn:", error);
        showChartError(
            error && error.message
                ? error.message
                : "Falha inesperada ao montar o gráfico."
        );
    }
});
}
</script>
</body>
</html>
'''

    replacements = {
        "__CHART_ID__": chart_id,
        "__HEIGHT__": str(int(height)),
        "__DATA__": _chart_payload(data),
        "__KIND__": chart_kind,
        "__PRIMARY__": primary,
        "__SECONDARY__": secondary,
        "__ACCENT__": accent,
        "__SURFACE__": surface,
        "__TEXT__": text,
        "__MUTED__": muted,
        "__POSITIVE__": positive,
        "__NEGATIVE__": negative,
        "__WARNING__": warning,
        "__VIOLET__": violet,
    }
    for key, value in replacements.items():
        html = html.replace(key, value)

    # O shell soma padding e borda à altura útil do gráfico.
    components.html(html, height=int(height) + 22, scrolling=False)


def _commercial_summary_cards(
    *,
    revenue_delta: float,
    revenue_delta_pct: float,
    active_delta: int,
    activations: int,
    deactivations: int,
    detail: pd.DataFrame,
) -> str:
    if revenue_delta > 0:
        result_title = f"Alta de {money(abs(revenue_delta))}"
        result_detail = f"{abs(revenue_delta_pct):.2f}% acima do mês anterior"
        result_tone = "positive"
    elif revenue_delta < 0:
        result_title = f"Queda de {money(abs(revenue_delta))}"
        result_detail = f"{abs(revenue_delta_pct):.2f}% abaixo do mês anterior"
        result_tone = "negative"
    else:
        result_title = "Faturamento estável"
        result_detail = "Sem variação relevante no mês"
        result_tone = "neutral"

    if active_delta > 0:
        base_title = f"+{active_delta} veículos"
        base_detail = "Crescimento da base"
        base_tone = "positive"
    elif active_delta < 0:
        base_title = f"{active_delta} veículos"
        base_detail = "Redução da base"
        base_tone = "negative"
    else:
        base_title = "Base estável"
        base_detail = "Sem variação no total de veículos"
        base_tone = "neutral"

    base_detail += f" · {activations} entradas / {deactivations} saídas"

    loss_client = "Sem perda relevante"
    loss_value = "R$ 0,00"
    gain_client = "Sem ganho relevante"
    gain_value = "R$ 0,00"

    if not detail.empty:
        negatives = detail[detail["Δ Receita"] < 0]
        positives = detail[detail["Δ Receita"] > 0]

        if not negatives.empty:
            top_loss = negatives.loc[negatives["Δ Receita"].idxmin()]
            loss_client = str(top_loss["Cliente"])
            loss_value = _money_delta(_safe_float(top_loss["Δ Receita"]))

        if not positives.empty:
            top_gain = positives.loc[positives["Δ Receita"].idxmax()]
            gain_client = str(top_gain["Cliente"])
            gain_value = _money_delta(_safe_float(top_gain["Δ Receita"]))

    def esc(value: object) -> str:
        return html.escape(str(value or ""))

    return f"""
<style>
.churn-commercial-summary {{ margin: 14px 0 8px; }}
.churn-commercial-title {{
    font-size: .92rem;
    font-weight: 700;
    margin: 0 0 9px;
    color: var(--app-text);
}}
.churn-commercial-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
}}
.churn-commercial-card {{
    background: var(--app-surface);
    border: 1px solid var(--app-border);
    border-radius: 12px;
    padding: 13px 14px;
    min-height: 112px;
    box-sizing: border-box;
}}
.churn-commercial-label {{
    color: var(--app-surface-muted);
    font-size: .76rem;
    font-weight: 650;
    text-transform: uppercase;
    letter-spacing: .035em;
    margin-bottom: 7px;
}}
.churn-commercial-value {{
    color: var(--app-surface-text);
    font-size: 1.08rem;
    line-height: 1.25;
    font-weight: 750;
}}
.churn-commercial-detail {{
    color: var(--app-surface-muted);
    font-size: .80rem;
    line-height: 1.35;
    margin-top: 5px;
}}
.churn-commercial-card.positive {{ border-top: 3px solid #16A34A; }}
.churn-commercial-card.negative {{ border-top: 3px solid #DC2626; }}
.churn-commercial-card.neutral {{ border-top: 3px solid #64748B; }}
.churn-commercial-client {{
    font-size: .90rem;
    line-height: 1.28;
    overflow-wrap: anywhere;
}}
@media (max-width: 900px) {{
    .churn-commercial-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
}}
@media (max-width: 560px) {{
    .churn-commercial-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
<div class="churn-commercial-summary">
  <div class="churn-commercial-title">Resumo comercial do mês</div>
  <div class="churn-commercial-grid">
    <div class="churn-commercial-card {result_tone}">
      <div class="churn-commercial-label">Resultado do mês</div>
      <div class="churn-commercial-value">{esc(result_title)}</div>
      <div class="churn-commercial-detail">{esc(result_detail)}</div>
    </div>
    <div class="churn-commercial-card {base_tone}">
      <div class="churn-commercial-label">Base de veículos</div>
      <div class="churn-commercial-value">{esc(base_title)}</div>
      <div class="churn-commercial-detail">{esc(base_detail)}</div>
    </div>
    <div class="churn-commercial-card negative">
      <div class="churn-commercial-label">Maior perda</div>
      <div class="churn-commercial-value churn-commercial-client">{esc(loss_client)}</div>
      <div class="churn-commercial-detail">{esc(loss_value)}</div>
    </div>
    <div class="churn-commercial-card positive">
      <div class="churn-commercial-label">Maior ganho</div>
      <div class="churn-commercial-value churn-commercial-client">{esc(gain_client)}</div>
      <div class="churn-commercial-detail">{esc(gain_value)}</div>
    </div>
  </div>
</div>
"""


diagnostics = connection_diagnostics()
if not diagnostics.get("ok"):
    st.error("O Simulador ainda não conseguiu acessar o MongoDB do Financeiro.")
    st.code(
        "Adicione no Streamlit Cloud do Simulador a seção "
        "[financeiro_service_account] com a conta de serviço do projeto "
        "MongoDB financeiro.",
        language="text",
    )
    with st.expander("Diagnóstico técnico"):
        st.write(diagnostics.get("error", "Falha não identificada."))
    st.stop()

raw_metrics = get_monthly_metrics()
metrics = [_metric_record(item) for item in raw_metrics]
metrics = [
    item
    for item in metrics
    if item["period_key"] and item["cliente"]
]
if not metrics:
    st.info(
        "Ainda não há histórico financeiro suficiente para a análise. "
        "No Financeiro, salve um faturamento ou use a ação de reconstrução "
        "do histórico existente."
    )
    st.stop()

closures = {
    str(item.get("period_key") or ""): item
    for item in get_month_closures()
    if item.get("period_key")
}
periods = sorted({item["period_key"] for item in metrics})
closed_periods = sorted(
    period
    for period, item in closures.items()
    if str(item.get("status") or "").lower() == "closed" and period in periods
)
default_period = closed_periods[-1] if closed_periods else periods[-1]

filter_1, filter_2, filter_3, filter_4 = st.columns([1.15, 1.85, 1.65, 0.9])
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
    MOVEMENT_ORDER,
    default=[],
)
top_n = filter_4.selectbox(
    "Top clientes",
    [5, 10, 15, 20, 30],
    index=2,
)

is_closed = (
    str(closures.get(selected_period, {}).get("status") or "").lower()
    == "closed"
)
if not is_closed:
    st.warning(
        f"{period_display(selected_period)} não possui fechamento mensal "
        "registrado. Clientes ausentes no mês não serão tratados como churn "
        "total para evitar falso positivo."
    )

by_period_client = {
    (item["period_key"], item["cliente"]): item
    for item in metrics
}
historical_active_periods: dict[str, set[str]] = defaultdict(set)
for item in metrics:
    if _safe_int(item.get("veiculos_ativos_fim_mes")) > 0:
        historical_active_periods[item["cliente"]].add(item["period_key"])

current_clients = {
    item["cliente"]
    for item in metrics
    if item["period_key"] == selected_period
}
previous_clients = {
    item["cliente"]
    for item in metrics
    if item["period_key"] == selected_previous
}
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
    current_revenue_client = _safe_float(current.get("receita"))
    previous_revenue_client = _safe_float(previous.get("receita"))
    previous_active_client = _safe_int(previous.get("veiculos_ativos_fim_mes"))
    current_active_client = _safe_int(current.get("veiculos_ativos_fim_mes"))
    rows.append(
        {
            "Cliente": cliente,
            "Classificação": classification,
            "Receita anterior": previous_revenue_client,
            "Receita atual": current_revenue_client,
            "Δ Receita": current_revenue_client - previous_revenue_client,
            "Δ Receita %": (
                (current_revenue_client / previous_revenue_client - 1) * 100
                if previous_revenue_client > 0
                else None
            ),
            "Veículos anterior": previous_active_client,
            "Veículos atual": current_active_client,
            "Δ Veículos": current_active_client - previous_active_client,
            "Ativações": _safe_int(current.get("ativacoes")),
            "Desativações": _safe_int(current.get("desativacoes")),
            "Suspensões": _safe_int(current.get("suspensoes")),
            "Qualidade": str(
                current.get("data_quality")
                or previous.get("data_quality")
                or "sem dados"
            ),
        }
    )

detail_all = pd.DataFrame(rows)
detail_scope = detail_all.copy()
if selected_clients:
    detail_scope = detail_scope[detail_scope["Cliente"].isin(selected_clients)]

detail = detail_scope.copy()
if classification_filter:
    detail = detail[detail["Classificação"].isin(classification_filter)]

scope_metrics = metrics
if selected_clients:
    selected_set = set(selected_clients)
    scope_metrics = [
        item
        for item in metrics
        if item["cliente"] in selected_set
    ]

current_records = [
    item
    for item in scope_metrics
    if item["period_key"] == selected_period
]
previous_records = [
    item
    for item in scope_metrics
    if item["period_key"] == selected_previous
]

current_revenue = _sum_metric(current_records, "receita")
previous_revenue = _sum_metric(previous_records, "receita")
revenue_delta = current_revenue - previous_revenue
revenue_delta_pct = (
    revenue_delta / previous_revenue * 100
    if previous_revenue
    else 0.0
)

current_active = int(
    _sum_metric(current_records, "veiculos_ativos_fim_mes")
)
previous_active = int(
    _sum_metric(previous_records, "veiculos_ativos_fim_mes")
)
active_delta = current_active - previous_active
deactivations = int(_sum_metric(current_records, "desativacoes"))
activations = int(_sum_metric(current_records, "ativacoes"))

current_active_clients = sum(
    1
    for item in current_records
    if _safe_int(item.get("veiculos_ativos_fim_mes")) > 0
)
previous_active_clients = sum(
    1
    for item in previous_records
    if _safe_int(item.get("veiculos_ativos_fim_mes")) > 0
)
client_churn = (
    int((detail_scope["Classificação"] == "Churn total").sum())
    if not detail_scope.empty
    else 0
)
client_churn_rate = (
    client_churn / previous_active_clients * 100
    if previous_active_clients
    else 0.0
)
vehicle_churn_rate = (
    deactivations / previous_active * 100
    if previous_active
    else 0.0
)

metric_1, metric_2, metric_3, metric_4, metric_5, metric_6 = st.columns(6)
metric_1.metric(
    "Faturamento",
    money(current_revenue),
    _money_delta(revenue_delta),
)
metric_2.metric("Variação M/M", _pct(revenue_delta_pct))
metric_3.metric(
    "Clientes ativos",
    current_active_clients,
    f"{current_active_clients - previous_active_clients:+d} clientes",
)
metric_4.metric(
    "Churn clientes",
    client_churn,
    f"{client_churn_rate:.2f}% da base anterior".replace(".", ","),
    delta_color="inverse",
)
metric_5.metric(
    "Base ativa",
    current_active,
    f"{active_delta:+d} veículos",
)
metric_6.metric(
    "Churn veículos",
    _pct(vehicle_churn_rate),
    f"{deactivations} desativações",
    delta_color="inverse",
)

st.markdown(
    _commercial_summary_cards(
        revenue_delta=revenue_delta,
        revenue_delta_pct=revenue_delta_pct,
        active_delta=active_delta,
        activations=activations,
        deactivations=deactivations,
        detail=detail,
    ),
    unsafe_allow_html=True,
)

st.markdown("### Diagnóstico do mês")
st.caption(
    "Os gráficos abaixo respeitam os filtros de Cliente e Movimento. "
    "Passe o mouse sobre os elementos para ver os valores."
)

impact = (
    detail.groupby("Classificação", as_index=False)
    .agg(
        **{
            "Δ Receita": ("Δ Receita", "sum"),
            "Clientes": ("Cliente", "nunique"),
        }
    )
    if not detail.empty
    else pd.DataFrame()
)

impact_data = []
mix_data = []
if not impact.empty:
    impact = impact.sort_values("Δ Receita", ascending=True)
    for _, row in impact.iterrows():
        classification = str(row["Classificação"])
        delta = _safe_float(row["Δ Receita"])
        clients_count = _safe_int(row["Clientes"])
        color_value = MOVEMENT_COLORS.get(
            classification,
            branding.get("primary_color", "#0F766E"),
        )
        impact_data.append(
            {
                "classification": classification,
                "deltaRevenue": delta,
                "deltaLabel": _money_delta(delta),
                "clients": clients_count,
                "color": color_value,
            }
        )
        mix_data.append(
            {
                "classification": classification,
                "clients": clients_count,
                "color": color_value,
            }
        )

diag_1, diag_2 = st.columns([1.35, 1])
with diag_1:
    st.markdown("#### Impacto na receita por movimento")
    _render_amcharts_chart("impact", impact_data, height=360)
with diag_2:
    st.markdown("#### Composição dos movimentos")
    _render_amcharts_chart("mix", mix_data, height=360)

monthly_rows = []
for period in periods:
    period_records = [
        item
        for item in scope_metrics
        if item["period_key"] == period
    ]
    revenue = _sum_metric(period_records, "receita")
    active_base = int(
        _sum_metric(period_records, "veiculos_ativos_fim_mes")
    )
    period_activations = int(_sum_metric(period_records, "ativacoes"))
    period_deactivations = int(_sum_metric(period_records, "desativacoes"))
    period_suspensions = int(_sum_metric(period_records, "suspensoes"))
    monthly_rows.append(
        {
            "Período": period,
            "Mês": period_display(period),
            "Faturamento": revenue,
            "Base ativa": active_base,
            "Ativações": period_activations,
            "Desativações": period_deactivations,
            "Suspensões": period_suspensions,
            "Saldo líquido": period_activations - period_deactivations,
        }
    )

monthly = pd.DataFrame(monthly_rows).sort_values("Período")

overview_data = [
    {
        "period": str(row["Período"]),
        "month": str(row["Mês"]),
        "revenue": _safe_float(row["Faturamento"]),
        "revenueLabel": money(_safe_float(row["Faturamento"])),
        "activeBase": _safe_int(row["Base ativa"]),
    }
    for _, row in monthly.iterrows()
]

movement_data = [
    {
        "period": str(row["Período"]),
        "month": str(row["Mês"]),
        "activations": _safe_int(row["Ativações"]),
        "deactivations": _safe_int(row["Desativações"]),
        "suspensions": _safe_int(row["Suspensões"]),
        "net": _safe_int(row["Saldo líquido"]),
    }
    for _, row in monthly.iterrows()
]

st.markdown("### Evolução da carteira")
if selected_clients:
    st.caption(
        "As séries históricas abaixo estão filtradas para os clientes selecionados."
    )
else:
    st.caption("As séries históricas abaixo representam a carteira completa.")

st.markdown("#### Faturamento e base ativa")
_render_amcharts_chart("overview", overview_data, height=410)

st.markdown("#### Entradas, saídas e saldo líquido")
_render_amcharts_chart("moves", movement_data, height=400)

st.markdown("### Clientes que explicam a mudança")
if detail.empty:
    st.info("Nenhum cliente corresponde aos filtros selecionados.")
else:
    detail_sorted = detail.reindex(
        detail["Δ Receita"].abs().sort_values(ascending=False).index
    )
    movers = detail_sorted.head(int(top_n))
    movers_data = [
        {
            "client": str(row["Cliente"]),
            "classification": str(row["Classificação"]),
            "deltaRevenue": _safe_float(row["Δ Receita"]),
            "deltaLabel": _money_delta(_safe_float(row["Δ Receita"])),
            "vehicleDelta": _safe_int(row["Δ Veículos"]),
            "vehicleDeltaLabel": f"{_safe_int(row['Δ Veículos']):+d}",
        }
        for _, row in movers.iterrows()
    ]

    _render_amcharts_chart(
        "movers",
        movers_data,
        height=max(330, min(680, 90 + len(movers_data) * 34)),
    )

    with st.expander("Ver tabela completa dos clientes", expanded=False):
        st.dataframe(
            detail_sorted,
            width="stretch",
            hide_index=True,
            column_config={
                "Receita anterior": st.column_config.NumberColumn(
                    format="R$ %.2f"
                ),
                "Receita atual": st.column_config.NumberColumn(
                    format="R$ %.2f"
                ),
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
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
    )

st.markdown("---")
st.markdown("### Drill-down por cliente")

drill_clients = (
    sorted(detail_scope["Cliente"].tolist())
    if not detail_scope.empty
    else sorted(comparison_clients)
)
selected_client = st.selectbox(
    "Cliente",
    drill_clients,
    index=None,
    placeholder="Selecione um cliente",
)

if selected_client:
    row = next(
        (
            item
            for item in rows
            if item["Cliente"] == selected_client
        ),
        None,
    )
    if row:
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Classificação", row["Classificação"])
        d2.metric(
            "Receita",
            money(row["Receita atual"]),
            _money_delta(row["Δ Receita"]),
        )
        d3.metric(
            "Base ativa",
            row["Veículos atual"],
            f"{row['Δ Veículos']:+d}",
        )
        d4.metric(
            "Ativações / desativações",
            f"{row['Ativações']} / {row['Desativações']}",
        )

    current_snapshots = [
        item
        for item in get_terminal_snapshots(selected_period)
        if str(item.get("cliente") or "").strip() == selected_client
    ]
    previous_snapshots = [
        item
        for item in get_terminal_snapshots(selected_previous)
        if str(item.get("cliente") or "").strip() == selected_client
    ]

    tab_current, tab_previous = st.tabs(
        [
            period_display(selected_period),
            period_display(selected_previous),
        ]
    )

    with tab_current:
        current_frame = _snapshot_dataframe(current_snapshots)
        if current_frame.empty:
            st.info(
                "Não há snapshot item a item deste cliente neste período."
            )
        else:
            st.dataframe(
                current_frame,
                width="stretch",
                hide_index=True,
                column_config={
                    "Valor Unitário": st.column_config.NumberColumn(
                        format="R$ %.2f"
                    ),
                    "Valor Faturado": st.column_config.NumberColumn(
                        format="R$ %.2f"
                    ),
                    "Data Ativação": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    ),
                    "Data Desativação": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    ),
                },
            )

    with tab_previous:
        previous_frame = _snapshot_dataframe(previous_snapshots)
        if previous_frame.empty:
            st.info(
                "Não há snapshot item a item deste cliente no período anterior."
            )
        else:
            st.dataframe(
                previous_frame,
                width="stretch",
                hide_index=True,
                column_config={
                    "Valor Unitário": st.column_config.NumberColumn(
                        format="R$ %.2f"
                    ),
                    "Valor Faturado": st.column_config.NumberColumn(
                        format="R$ %.2f"
                    ),
                    "Data Ativação": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    ),
                    "Data Desativação": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    ),
                },
            )

with st.expander("Qualidade e origem dos dados", expanded=False):
    quality = pd.DataFrame(metrics)
    summary = (
        quality.groupby("data_quality", as_index=False)
        .agg(
            Registros=("cliente", "count"),
            Clientes=("cliente", "nunique"),
            Periodos=("period_key", "nunique"),
        )
        .sort_values("Registros", ascending=False)
    )
    st.dataframe(summary, width="stretch", hide_index=True)
    st.caption(
        "detalhado/historico_detalhado: possui item a item e permite churn "
        "de terminais com maior precisão. resumo_legado: registro antigo sem "
        "detalhe; receita é válida, mas base e movimentos podem ser aproximados."
    )
