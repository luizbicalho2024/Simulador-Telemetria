from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import user_management_db as db
from app_core.auth import require_auth
from app_core.pricing import (
    MIN_CUSTOM_MARGIN_PERCENT,
    break_even_vehicle_count,
    gross_margin_percent,
    gross_margin_value,
    minimum_sale_price,
    mixed_break_even_vehicle_count,
    mixed_proposal_totals,
    mixed_quantity_scenarios,
    quantize_money,
    sale_price_from_margin,
    summarize_cost_components,
    to_decimal,
)
from app_core.proposal_documents import generate_pj_proposal
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Simulador Pessoa Jurídica")
apply_branding()
require_auth()
render_sidebar()
render_hero(
    "Simulador de venda — Pessoa Jurídica",
    "Simule livremente qualquer condição comercial. O piso de margem é uma regra de aprovação, não um bloqueio de análise.",
)

ROLE = str(st.session_state.get("role") or "user")
USERNAME = str(st.session_state.get("username") or "").strip().lower()
USER_NAME = str(st.session_state.get("name") or USERNAME or "Usuário")

pricing_config = db.get_pricing_config()
plans = {
    plan: {product: quantize_money(value) for product, value in products.items()}
    for plan, products in pricing_config.get("PLANOS_PJ", {}).items()
}
costs_by_plan = {
    plan: {product: quantize_money(value) for product, value in products.items()}
    for plan, products in pricing_config.get("CUSTOS_PJ", {}).items()
}
installation_by_product = pricing_config.get("INSTALACAO_PJ", {})
detailed_costs_by_product = pricing_config.get("CUSTOS_DETALHADOS_PJ", {})
descriptions = pricing_config.get("PRODUTOS_PJ_DESCRICAO", {})
fixed_implementation_cost = quantize_money(
    pricing_config.get("CUSTO_FIXO_IMPLANTACAO_PJ", 0)
)
minimum_custom_margin = max(
    MIN_CUSTOM_MARGIN_PERCENT,
    to_decimal(pricing_config.get("MARGEM_MINIMA_PERSONALIZADA_PJ", 30)),
)
quantity_defaults = pricing_config.get("CENARIOS_QUANTIDADE_PJ", [1, 5, 10, 25, 50, 100, 200])

OFFER_PRESETS = {
    "VERDIO Start": {
        "subtitle": "Rastreamento + app + bloqueio",
        "positioning": "Entrada competitiva",
        "keywords": ("gprs", "gsm"),
    },
    "VERDIO Fleet": {
        "subtitle": "Start + CAN + RFID",
        "positioning": "Eficiência / combustível",
        "keywords": ("gprs", "gsm", "can", "rfid", "identificador"),
    },
    "VERDIO Safety": {
        "subtitle": "Fleet + vídeo + DMS/ADAS",
        "positioning": "Risco, sinistro e jornada",
        "keywords": ("gprs", "gsm", "can", "rfid", "identificador", "video", "vídeo", "dms", "adas"),
    },
    "VERDIO Sat": {
        "subtitle": "Cobertura satelital para operações críticas",
        "positioning": "Sombra de sinal / agro / rota longa",
        "keywords": ("sat", "satélite", "satelite"),
    },
}

if "pj_results" not in st.session_state:
    st.session_state.pj_results = None


def _product_key(product: str) -> str:
    return hashlib.sha1(product.encode("utf-8")).hexdigest()[:10]


def _margin_label(percent: Decimal | None) -> str:
    return "Não disponível" if percent is None else f"{percent:.2f}%"


def _status_label(status: str) -> str:
    return {
        "approved": "Liberada para emissão",
        "pending_approval": "Aguardando Head Comercial",
        "rejected": "Rejeitada",
    }.get(status, status or "Sem status")


def _safe_float(value: object) -> float:
    return float(to_decimal(value))



def _safe_hex_color(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    if (
        len(text) == 7
        and text.startswith("#")
        and all(character in "0123456789abcdefABCDEF" for character in text[1:])
    ):
        return text
    return fallback


def _render_break_even_chart(
    quantities: list[int],
    *,
    portfolio_items: list[dict[str, object]],
    base_fleet_vehicles: Decimal,
    months: Decimal,
    fixed_cost: Decimal,
    minimum_margin_percent: Decimal,
) -> None:
    charged_rows = mixed_quantity_scenarios(
        quantities,
        items=portfolio_items,
        base_fleet_vehicles=base_fleet_vehicles,
        months=months,
        charge_installation=True,
        fixed_cost=fixed_cost,
    )
    waived_rows = mixed_quantity_scenarios(
        quantities,
        items=portfolio_items,
        base_fleet_vehicles=base_fleet_vehicles,
        months=months,
        charge_installation=False,
        fixed_cost=fixed_cost,
    )

    waived_by_quantity = {
        int(row["Veículos"]): row for row in waived_rows
    }
    chart_data: list[dict[str, float | int | None]] = []
    for charged_row in charged_rows:
        quantity = int(charged_row["Veículos"])
        waived_row = waived_by_quantity.get(quantity, {})
        chart_data.append(
            {
                "vehicles": quantity,
                "chargedMargin": charged_row.get("Margem (%)"),
                "waivedMargin": waived_row.get("Margem (%)"),
            }
        )

    if not chart_data:
        return

    branding = db.get_system_settings() or {}
    primary = _safe_hex_color(branding.get("primary_color"), "#0F766E")
    accent = _safe_hex_color(branding.get("accent_color"), "#2563EB")
    text_color = _safe_hex_color(branding.get("text_color"), "#0F172A")
    muted_color = _safe_hex_color(branding.get("muted_color"), "#64748B")
    surface_color = _safe_hex_color(branding.get("surface_color"), "#FFFFFF")
    policy_color = "#D97706"
    chart_id = "pj-break-even-" + hashlib.sha1(
        json.dumps(chart_data, sort_keys=True).encode("utf-8")
    ).hexdigest()[:10]

    chart_html = """
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
    border: 1px solid rgba(100, 116, 139, .20);
    border-radius: 14px;
    background: __SURFACE__;
    padding: 10px 10px 4px;
}
#__CHART_ID__ { width: 100%; height: 380px; }
.chart-fallback {
    color: __MUTED__;
    font-size: 13px;
    padding: 18px;
}
</style>
<script src="https://cdn.amcharts.com/lib/version/5.20.3/index.js"></script>
<script src="https://cdn.amcharts.com/lib/version/5.20.3/xy.js"></script>
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
        '<br><small>A tabela detalhada abaixo continua disponível para análise.</small></div>';
}

if (typeof am5 === "undefined" || typeof am5xy === "undefined") {
    showChartError(
        "Não foi possível carregar a biblioteca amCharts. Verifique bloqueio de CDN, proxy ou política de conteúdo do navegador."
    );
} else {
am5.ready(function() {
    try {
        const data = __DATA__;
        const minimumMargin = __MIN_MARGIN__;

    function color(hex) {
        return am5.color(parseInt(hex.replace("#", ""), 16));
    }

    const host = document.getElementById("__CHART_ID__");
    if (!host) {
        throw new Error("Container do gráfico não encontrado.");
    }
    host.replaceChildren();

    const root = am5.Root.new(host);
    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
        layout: root.verticalLayout,
        paddingLeft: 8,
        paddingRight: 18,
        paddingTop: 8
    }));

    const xRenderer = am5xy.AxisRendererX.new(root, { minGridDistance: 52 });
    xRenderer.labels.template.setAll({
        fill: color("__MUTED__"),
        fontSize: 12,
        paddingTop: 8
    });
    xRenderer.grid.template.setAll({
        stroke: color("__MUTED__"),
        strokeOpacity: 0.10
    });

    const xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
        min: 0,
        extraMax: 0.04,
        numberFormat: "#",
        renderer: xRenderer
    }));

    const yRenderer = am5xy.AxisRendererY.new(root, {});
    yRenderer.labels.template.setAll({
        fill: color("__MUTED__"),
        fontSize: 12,
        paddingRight: 8
    });
    yRenderer.grid.template.setAll({
        stroke: color("__MUTED__"),
        strokeOpacity: 0.10
    });

    const yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
        extraMin: 0.08,
        extraMax: 0.10,
        numberFormat: "#.0'%'",
        renderer: yRenderer
    }));

    function createSeries(name, field, seriesColor) {
        const series = chart.series.push(am5xy.LineSeries.new(root, {
            name: name,
            xAxis: xAxis,
            yAxis: yAxis,
            valueXField: "vehicles",
            valueYField: field,
            stroke: color(seriesColor),
            fill: color(seriesColor),
            tooltip: am5.Tooltip.new(root, {
                labelText: "[bold]" + name + "[/] · {valueX} veículos · {valueY}%"
            })
        }));

        series.strokes.template.setAll({
            strokeWidth: 3
        });

        series.bullets.push(function() {
            return am5.Bullet.new(root, {
                sprite: am5.Circle.new(root, {
                    radius: 4,
                    fill: series.get("fill"),
                    stroke: color("__SURFACE__"),
                    strokeWidth: 2
                })
            });
        });

        series.data.setAll(data.filter(function(row) {
            return row[field] !== null && row[field] !== undefined;
        }));
        return series;
    }

    createSeries("Cobrando instalação", "chargedMargin", "__PRIMARY__");
    createSeries("Isentando instalação", "waivedMargin", "__ACCENT__");

    const rangeDataItem = yAxis.makeDataItem({ value: minimumMargin });
    const range = yAxis.createAxisRange(rangeDataItem);
    range.get("grid").setAll({
        stroke: color("__POLICY__"),
        strokeWidth: 2,
        strokeOpacity: 0.95,
        strokeDasharray: [7, 5]
    });
    range.get("label").setAll({
        text: "Piso " + minimumMargin.toFixed(2) + "%",
        fill: color("__POLICY__"),
        fontSize: 12,
        fontWeight: "600",
        inside: true,
        location: 1,
        dx: -8
    });

    const legend = chart.children.push(am5.Legend.new(root, {
        centerX: am5.p50,
        x: am5.p50,
        marginTop: 10
    }));
    legend.labels.template.setAll({
        fill: color("__TEXT__"),
        fontSize: 12
    });
    legend.valueLabels.template.set("forceHidden", true);
    legend.data.setAll(chart.series.values);

    const cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
        behavior: "none"
    }));
    cursor.lineY.set("visible", false);
    cursor.lineX.setAll({
        stroke: color("__MUTED__"),
        strokeOpacity: 0.25
    });

        chart.appear(700, 80);
    } catch (error) {
        console.error("Falha ao renderizar o gráfico amCharts do Simulador PJ:", error);
        showChartError(
            "O amCharts foi carregado, mas ocorreu uma falha durante a renderização. Consulte o console do navegador para o detalhe técnico."
        );
    }
});
}
</script>
</body>
</html>
"""
    chart_html = (
        chart_html
        .replace("__CHART_ID__", chart_id)
        .replace("__DATA__", json.dumps(chart_data, ensure_ascii=False))
        .replace("__MIN_MARGIN__", str(float(minimum_margin_percent)))
        .replace("__PRIMARY__", primary)
        .replace("__ACCENT__", accent)
        .replace("__TEXT__", text_color)
        .replace("__MUTED__", muted_color)
        .replace("__SURFACE__", surface_color)
        .replace("__POLICY__", policy_color)
    )
    components.html(chart_html, height=410, scrolling=False)


def _product_matches(product: str, preset_name: str) -> bool:
    normalized = product.casefold()
    preset = OFFER_PRESETS[preset_name]
    if preset_name == "VERDIO Start":
        return any(keyword in normalized for keyword in preset["keywords"])
    if preset_name == "VERDIO Sat":
        return any(keyword in normalized for keyword in preset["keywords"])

    is_gsm = "gprs" in normalized or "gsm" in normalized
    is_can = "can" in normalized or "telemetria" in normalized
    is_rfid = "rfid" in normalized or "identificador" in normalized
    is_video = "video" in normalized or "vídeo" in normalized or "dms" in normalized or "adas" in normalized
    if preset_name == "VERDIO Fleet":
        return is_gsm or is_can or is_rfid
    if preset_name == "VERDIO Safety":
        return is_gsm or is_can or is_rfid or is_video
    return False


def _apply_preset(
    preset_name: str,
    contract_term: str,
    fleet_size: int,
) -> None:
    for product in plans.get(contract_term, {}):
        product_id = _product_key(product)
        matched = _product_matches(product, preset_name)

        st.session_state[
            f"pj_enabled_{contract_term}_{product_id}"
        ] = matched

        quantity_key = (
            f"pj_quantity_{contract_term}_{product_id}"
        )
        if matched:
            st.session_state[quantity_key] = max(
                1,
                int(fleet_size),
            )
        else:
            st.session_state.pop(quantity_key, None)

        st.session_state.pop(
            f"pj_mode_{contract_term}_{product_id}",
            None,
        )
        st.session_state.pop(
            f"pj_custom_value_{contract_term}_{product_id}",
            None,
        )
        st.session_state.pop(
            f"pj_custom_margin_{contract_term}_{product_id}",
            None,
        )

    st.session_state.pj_offer_reference = preset_name
    st.session_state.pj_results = None


def clear_simulation() -> None:
    for key in list(st.session_state):
        if key.startswith("pj_") and key != "pj_results":
            st.session_state.pop(key, None)
    st.session_state.pj_results = None


if not plans:
    st.warning("Não há planos PJ configurados. Solicite ao administrador a inclusão dos preços.")
    st.stop()

header_actions = st.columns([5, 1])
with header_actions[1]:
    if st.button("Limpar simulação", width="stretch"):
        clear_simulation()
        st.rerun()

config_col, client_col = st.columns([1, 1.4])
with config_col:
    st.markdown("#### Configuração comercial")
    vehicle_count = st.number_input(
        "Quantidade de veículos",
        min_value=1,
        max_value=100_000,
        value=1,
        step=1,
        key="pj_vehicle_count",
    )
    contract_term = st.selectbox(
        "Prazo do contrato",
        list(plans),
        key="pj_contract_term",
    )
    installation_policy = st.radio(
        "Condição da instalação",
        ["Cobrar instalação", "Isentar instalação"],
        horizontal=True,
        key="pj_installation_policy",
        help=(
            "Ao isentar, a receita da instalação é zerada, mas o custo interno de instalação "
            "continua sendo descontado da margem da proposta."
        ),
    )
    st.caption(
        "Mensalidades são unitárias por veículo; instalação é uma cobrança única."
    )
    if fixed_implementation_cost > 0:
        fixed_cost_per_vehicle = quantize_money(
            fixed_implementation_cost / Decimal(vehicle_count)
        )
        st.warning(
            f"Custo fixo interno aplicado à proposta: "
            f"{money(fixed_implementation_cost)}. "
            f"Com {vehicle_count} veículo(s), ele representa "
            f"{money(fixed_cost_per_vehicle)} por veículo nesta análise. "
            "Esse custo é aplicado uma única vez à proposta e entra na margem final."
        )

with client_col:
    st.markdown("#### Dados da proposta")
    company = st.text_input("Empresa", key="pj_company")
    responsible = st.text_input("Responsável", key="pj_responsible")
    validity_days = st.number_input(
        "Validade da proposta (dias)",
        min_value=1,
        max_value=90,
        value=15,
        key="pj_validity_days",
    )

st.markdown("### Arquitetura comercial Bionio Frotas")
st.caption(
    "Use os pacotes como ponto de partida. Os preços reais ficam em Produtos e serviços; "
    "a margem calculada pelo simulador determina a necessidade de aprovação."
)
preset_columns = st.columns(4)
for index, (preset_name, preset) in enumerate(OFFER_PRESETS.items()):
    with preset_columns[index]:
        with st.container(border=True):
            st.markdown(f"**{preset_name}**")
            st.caption(str(preset["subtitle"]))
            st.caption(str(preset["positioning"]))
            if st.button(
                f"Aplicar {preset_name.replace('VERDIO ', '')}",
                width="stretch",
                key=f"pj_preset_{index}",
            ):
                _apply_preset(
                    preset_name,
                    contract_term,
                    int(vehicle_count),
                )
                st.rerun()

active_reference = st.session_state.get("pj_offer_reference")
if active_reference in OFFER_PRESETS:
    st.info(
        f"Referência ativa: {active_reference}. "
        "Você pode incluir, remover, reprificar e ajustar "
        "a quantidade de cada item livremente."
    )


st.markdown("#### Produtos e serviços")
policy_col, selection_col = st.columns([3.4, 1])
with policy_col:
    st.caption(
        f"Piso de governança: {minimum_custom_margin:.2f}% de margem total. "
        "Valores abaixo do piso continuam simuláveis, mas exigem aprovação do Head Comercial para emissão."
    )
with selection_col:
    st.caption("Selecione os itens e ajuste apenas quando necessário.")

st.caption(
    "Cada produto pode ter uma quantidade própria, limitada ao tamanho da frota. "
    "As quantidades são independentes e podem se sobrepor no mesmo veículo."
)

selected: dict[str, dict[str, object]] = {}
current_plan_costs = costs_by_plan.get(contract_term, {})

header_cols = st.columns(
    [2.75, 0.72, 1.0, 1.0, 1.0, 1.1, 0.82],
    vertical_alignment="center",
)
for column, label in zip(
    header_cols,
    [
        "Produto",
        "Qtd.",
        "Padrão",
        "Aplicado",
        "Margem",
        "Instalação",
        "Ação",
    ],
):
    column.caption(label)

contract_months_for_cost = Decimal(contract_term.split()[0])

for product, base_price in plans[contract_term].items():
    product_id = _product_key(product)
    legacy_recurring_cost = quantize_money(
        current_plan_costs.get(product, 0)
    )
    detailed_cost_rows = detailed_costs_by_product.get(product, [])
    has_detailed_cost = bool(detailed_cost_rows)
    detailed_cost_summary = summarize_cost_components(
        detailed_cost_rows,
        contract_months_for_cost,
    )

    if has_detailed_cost:
        recurring_cost = detailed_cost_summary["recurring_monthly"]
        one_time_cost = detailed_cost_summary["one_time_per_vehicle"]
        pricing_cost = detailed_cost_summary["monthly_equivalent"]
    else:
        recurring_cost = legacy_recurring_cost
        one_time_cost = Decimal("0.00")
        pricing_cost = legacy_recurring_cost

    recurring_cost_configured = pricing_cost > 0
    installation_config = installation_by_product.get(product, {})
    installation_sale = quantize_money(installation_config.get("preco_venda", 0))
    installation_cost = quantize_money(installation_config.get("custo", 0))

    base_margin_value = (
        gross_margin_value(base_price, pricing_cost)
        if recurring_cost_configured
        else None
    )
    base_margin_percent = (
        gross_margin_percent(base_price, pricing_cost)
        if recurring_cost_configured
        else None
    )


    effective_price = base_price
    pricing_mode = "Preço padrão"
    custom_discount = False
    quantity = 0

    with st.container(border=True):
        row = st.columns(
            [2.75, 0.72, 1.0, 1.0, 1.0, 1.1, 0.82],
            vertical_alignment="center",
        )

        with row[0]:
            enabled = st.toggle(
                product,
                key=f"pj_enabled_{contract_term}_{product_id}",
            )
            st.caption(descriptions.get(product, product))

        quantity_key = (
            f"pj_quantity_{contract_term}_{product_id}"
        )
        with row[1]:
            if enabled:
                if quantity_key not in st.session_state:
                    st.session_state[quantity_key] = int(
                        vehicle_count
                    )

                current_quantity = int(
                    st.session_state.get(
                        quantity_key,
                        vehicle_count,
                    )
                    or 1
                )
                current_quantity = max(
                    1,
                    min(int(vehicle_count), current_quantity),
                )
                st.session_state[quantity_key] = current_quantity

                quantity = int(
                    st.number_input(
                        f"Quantidade {product}",
                        min_value=1,
                        max_value=int(vehicle_count),
                        step=1,
                        key=quantity_key,
                        label_visibility="collapsed",
                    )
                )
                st.caption(f"de {vehicle_count}")
            else:
                st.markdown("**—**")
                st.caption("não usado")

        modes = ["Preço padrão"]
        if recurring_cost_configured:
            modes.extend(
                ["Valor personalizado", "Margem personalizada"]
            )

        if enabled:
            with row[6]:
                with st.popover("Ajustar"):
                    st.caption(
                        f"Preço padrão: {money(base_price)} "
                        "por veículo/mês"
                    )

                    if has_detailed_cost:
                        st.caption(
                            f"Custo recorrente: "
                            f"{money(recurring_cost)}/mês"
                        )
                        st.caption(
                            f"Custo único por veículo: "
                            f"{money(one_time_cost)}"
                        )
                        st.caption(
                            f"Custo mensal equivalente em "
                            f"{int(contract_months_for_cost)} meses: "
                            f"{money(pricing_cost)}"
                        )
                    else:
                        st.caption(
                            "Custo mensal legado: "
                            + (
                                money(pricing_cost)
                                if recurring_cost_configured
                                else "não cadastrado"
                            )
                        )

                    if not recurring_cost_configured:
                        st.warning(
                            "Cadastre o custo mensal deste produto "
                            "antes de usar uma condição personalizada."
                        )

                    pricing_mode = st.radio(
                        "Condição comercial",
                        modes,
                        key=f"pj_mode_{contract_term}_{product_id}",
                    )

                    if pricing_mode == "Valor personalizado":
                        floor_price = minimum_sale_price(
                            pricing_cost,
                            minimum_custom_margin,
                        )
                        custom_value = st.number_input(
                            "Preço mensal personalizado por veículo",
                            min_value=0.01,
                            value=max(0.01, float(base_price)),
                            step=1.0,
                            format="%.2f",
                            key=(
                                f"pj_custom_value_{contract_term}_"
                                f"{product_id}"
                            ),
                            help=(
                                f"Referência para manter "
                                f"{minimum_custom_margin:.2f}% "
                                f"de margem unitária: "
                                f"{money(floor_price)}. "
                                "Valores menores continuam permitidos "
                                "para simulação."
                            ),
                        )
                        effective_price = quantize_money(custom_value)

                    elif pricing_mode == "Margem personalizada":
                        default_margin = min(
                            max(
                                float(
                                    base_margin_percent
                                    or minimum_custom_margin
                                ),
                                -500.0,
                            ),
                            99.0,
                        )
                        target_margin = st.number_input(
                            "Margem desejada sobre o preço de venda (%)",
                            min_value=-500.0,
                            max_value=99.0,
                            value=default_margin,
                            step=0.5,
                            format="%.2f",
                            key=(
                                f"pj_custom_margin_{contract_term}_"
                                f"{product_id}"
                            ),
                            help=(
                                "Margens abaixo do piso, inclusive "
                                "negativas, podem ser simuladas. "
                                "A proposta final seguirá a alçada "
                                "comercial quando necessário."
                            ),
                        )
                        effective_price = sale_price_from_margin(
                            pricing_cost,
                            target_margin,
                        )
                        st.caption(
                            f"Preço calculado: {money(effective_price)} "
                            "por veículo/mês"
                        )
        else:
            with row[6]:
                st.caption("Selecione")

        effective_margin_value = (
            gross_margin_value(
                effective_price,
                pricing_cost,
            )
            if recurring_cost_configured
            else None
        )
        effective_margin_percent = (
            gross_margin_percent(
                effective_price,
                pricing_cost,
            )
            if recurring_cost_configured
            else None
        )
        custom_discount = (
            pricing_mode != "Preço padrão"
            and effective_price < base_price
        )

        with row[2]:
            st.markdown(f"**{money(base_price)}**")
            if has_detailed_cost:
                st.caption(
                    f"Custo eq. {money(pricing_cost)}"
                )
                st.caption(
                    f"{money(recurring_cost)}/mês + "
                    f"{money(one_time_cost)} único"
                )
            else:
                st.caption(
                    "Custo "
                    + (
                        money(pricing_cost)
                        if recurring_cost_configured
                        else "pendente"
                    )
                )

        with row[3]:
            st.markdown(f"**{money(effective_price)}**")
            st.caption(
                pricing_mode if enabled else "Não selecionado"
            )

        with row[4]:
            st.markdown(
                f"**{_margin_label(effective_margin_percent)}**"
            )
            if effective_margin_percent is None:
                st.caption("Custo pendente")
            elif effective_margin_percent >= minimum_custom_margin:
                st.caption("Dentro da política")
            else:
                st.caption("Abaixo do piso")

        with row[5]:
            if installation_sale > 0 or installation_cost > 0:
                st.markdown(
                    f"**{money(installation_sale)}**"
                )
                st.caption(
                    f"Custo {money(installation_cost)}"
                )
            else:
                st.markdown("**—**")
                st.caption("Sem cobrança")

        if enabled and quantity > 0:
            selected[product] = {
                "quantity": quantity,
                "base_price": base_price,
                "price": effective_price,
                "recurring_cost": recurring_cost,
                "one_time_cost": one_time_cost,
                "pricing_cost": pricing_cost,
                "cost_details": [
                    dict(cost_row)
                    for cost_row in detailed_cost_rows
                    if isinstance(cost_row, dict)
                ],
                "cost_configured": recurring_cost_configured,
                "margin_value": effective_margin_value,
                "margin_percent": effective_margin_percent,
                "pricing_mode": pricing_mode,
                "custom_discount": custom_discount,
                "installation_sale": installation_sale,
                "installation_cost": installation_cost,
            }
if not selected:
    st.info("Selecione ao menos um produto para visualizar a análise de margem e equilíbrio.")

analysis: dict[str, object] | None = None
if selected:
    vehicle_decimal = Decimal(vehicle_count)
    months = Decimal(contract_term.split()[0])

    portfolio_items = [
        {
            "product": product,
            "quantity": int(item["quantity"]),
            "recurring_sale": item["price"],
            "recurring_cost": item["recurring_cost"],
            "one_time_cost": item["one_time_cost"],
            "installation_sale": item["installation_sale"],
            "installation_cost": item["installation_cost"],
        }
        for product, item in selected.items()
    ]

    def _weighted_fleet_value(field: str) -> Decimal:
        total = sum(
            (
                to_decimal(item[field])
                * Decimal(int(item["quantity"]))
                for item in selected.values()
            ),
            Decimal("0"),
        )
        return quantize_money(total / vehicle_decimal)

    recurring_sale_per_vehicle = _weighted_fleet_value("price")
    recurring_cost_per_vehicle = _weighted_fleet_value(
        "recurring_cost"
    )
    one_time_cost_per_vehicle = _weighted_fleet_value(
        "one_time_cost"
    )
    installation_sale_per_vehicle = _weighted_fleet_value(
        "installation_sale"
    )
    installation_cost_per_vehicle = _weighted_fleet_value(
        "installation_cost"
    )

    all_costs_configured = all(
        bool(item["cost_configured"])
        for item in selected.values()
    )

    charged_totals = mixed_proposal_totals(
        items=portfolio_items,
        months=months,
        charge_installation=True,
        fixed_cost=fixed_implementation_cost,
    )
    waived_totals = mixed_proposal_totals(
        items=portfolio_items,
        months=months,
        charge_installation=False,
        fixed_cost=fixed_implementation_cost,
    )

    charged_operational_totals = mixed_proposal_totals(
        items=portfolio_items,
        months=months,
        charge_installation=True,
        fixed_cost=0,
    )
    waived_operational_totals = mixed_proposal_totals(
        items=portfolio_items,
        months=months,
        charge_installation=False,
        fixed_cost=0,
    )

    charge_installation = (
        installation_policy == "Cobrar instalação"
    )
    chosen_totals = (
        charged_totals
        if charge_installation
        else waived_totals
    )
    chosen_operational_totals = (
        charged_operational_totals
        if charge_installation
        else waived_operational_totals
    )

    chosen_break_even = mixed_break_even_vehicle_count(
        items=portfolio_items,
        base_fleet_vehicles=vehicle_decimal,
        months=months,
        charge_installation=charge_installation,
        fixed_cost=fixed_implementation_cost,
        target_margin_percent=minimum_custom_margin,
    )

    st.markdown("### Resumo executivo da simulação")
    chosen_margin_percent = chosen_totals["margin_percent"]
    operational_margin_percent = chosen_operational_totals["margin_percent"]
    below_margin_floor = (
        chosen_margin_percent is None
        or chosen_margin_percent < minimum_custom_margin
    )
    fixed_cost_caused_policy_failure = bool(
        below_margin_floor
        and fixed_implementation_cost > 0
        and operational_margin_percent is not None
        and operational_margin_percent >= minimum_custom_margin
    )

    summary_cols = st.columns(6)
    summary_cols[0].metric(
        "Mensalidade da frota",
        money(chosen_totals["monthly_revenue"]),
    )
    summary_cols[1].metric(
        "Receita do contrato",
        money(chosen_totals["total_revenue"]),
    )
    summary_cols[2].metric(
        "Custo operacional",
        money(chosen_operational_totals["total_cost"]),
    )
    summary_cols[3].metric(
        "Custo fixo implantação",
        money(fixed_implementation_cost),
    )
    summary_cols[4].metric(
        "Margem operacional",
        _margin_label(operational_margin_percent),
    )
    summary_cols[5].metric(
        "Margem final",
        _margin_label(chosen_margin_percent),
    )
    st.caption(
        f"Margem final em valor: {money(chosen_totals['total_margin'])} · "
        f"Custo total consolidado: {money(chosen_totals['total_cost'])}"
    )

    if fixed_cost_caused_policy_failure:
        fixed_cost_impact_pp = (
            operational_margin_percent - chosen_margin_percent
            if chosen_margin_percent is not None
            else operational_margin_percent
        )
        fixed_cost_per_vehicle = quantize_money(
            fixed_implementation_cost / vehicle_decimal
        )
        equilibrium_text = (
            f" Mantidas as condições atuais, o piso de "
            f"{minimum_custom_margin:.2f}% é atingido a partir de "
            f"{chosen_break_even} veículo(s)."
            if chosen_break_even is not None
            else ""
        )
        st.warning(
            f"A oferta está dentro da política antes do custo fixo: "
            f"margem operacional de {_margin_label(operational_margin_percent)}. "
            f"O bloqueio ocorre porque existe um custo fixo de implantação de "
            f"{money(fixed_implementation_cost)} aplicado à proposta. "
            f"Com {int(vehicle_decimal)} veículo(s), esse custo equivale a "
            f"{money(fixed_cost_per_vehicle)} por veículo e reduz a margem final "
            f"para {_margin_label(chosen_margin_percent)} "
            f"(impacto de {fixed_cost_impact_pp:.2f} p.p.)."
            + equilibrium_text
        )
    elif below_margin_floor:
        gap = (
            minimum_custom_margin - chosen_margin_percent
            if chosen_margin_percent is not None
            else minimum_custom_margin
        )
        st.warning(
            f"A margem final ficou em {_margin_label(chosen_margin_percent)}, "
            f"abaixo do piso de {minimum_custom_margin:.2f}% "
            f"(diferença de {gap:.2f} p.p.). "
            "Revise preços, custos e instalação; se a condição comercial precisar "
            "ser mantida, a proposta seguirá para aprovação do Head Comercial."
        )
    else:
        st.success(
            f"Condição dentro da política: margem final de "
            f"{_margin_label(chosen_margin_percent)}, acima do piso de "
            f"{minimum_custom_margin:.2f}%."
        )

    with st.expander("Entenda a composição da margem", expanded=False):
        breakdown_1, breakdown_2, breakdown_3 = st.columns(3)
        breakdown_1.metric(
            "Receita recorrente",
            money(chosen_totals["recurring_revenue"]),
        )
        breakdown_1.metric(
            "Receita de instalação",
            money(chosen_totals["installation_revenue"]),
        )
        breakdown_2.metric(
            "Custo recorrente",
            money(chosen_totals["recurring_cost"]),
        )
        breakdown_2.metric(
            "Custo único dos rastreadores",
            money(chosen_totals["one_time_cost"]),
        )
        breakdown_2.metric(
            "Custo de instalação",
            money(chosen_totals["installation_cost"]),
        )
        breakdown_3.metric(
            "Custo fixo da proposta",
            money(chosen_totals["fixed_cost"]),
        )
        breakdown_3.metric(
            "Margem final",
            money(chosen_totals["total_margin"]),
        )

    st.markdown("### Comparativo de rentabilidade")
    normal_col, waived_col = st.columns(2)
    with normal_col:
        st.markdown("#### Margem cobrando instalação")
        m1, m2 = st.columns(2)
        m1.metric("Margem total", money(charged_totals["total_margin"]))
        m2.metric("Margem (%)", _margin_label(charged_totals["margin_percent"]))
        st.caption(
            f"Receita de instalação: {money(charged_totals['installation_revenue'])} · "
            f"Custo de instalação: {money(charged_totals['installation_cost'])} · "
            f"Custo fixo da proposta: {money(charged_totals['fixed_cost'])}"
        )
    with waived_col:
        st.markdown("#### Margem isentando instalação")
        m1, m2 = st.columns(2)
        m1.metric("Margem total", money(waived_totals["total_margin"]))
        m2.metric("Margem (%)", _margin_label(waived_totals["margin_percent"]))
        st.caption(
            f"Receita de instalação: {money(waived_totals['installation_revenue'])} · "
            f"Custo mantido na margem: {money(waived_totals['installation_cost'])} · "
            f"Custo fixo da proposta: {money(waived_totals['fixed_cost'])}"
        )
        if waived_totals["payback_months"] is not None:
            st.caption(
                f"Recuperação do subsídio da instalação: aproximadamente "
                f"{waived_totals['payback_months']} meses."
            )


    st.markdown(
        "### Ponto de equilíbrio mantendo o mix atual"
    )
    st.caption(
        "A projeção mantém a mesma proporção entre as quantidades dos produtos "
        "selecionados e escala esse mix conforme o tamanho da frota. "
        "A linha tracejada representa o piso de governança."
    )

    scenario_quantities = sorted(
        {
            *[
                int(value)
                for value in quantity_defaults
                if int(value) > 0
            ],
            int(vehicle_count),
        }
    )

    charged_break_even = mixed_break_even_vehicle_count(
        items=portfolio_items,
        base_fleet_vehicles=vehicle_decimal,
        months=months,
        charge_installation=True,
        fixed_cost=fixed_implementation_cost,
        target_margin_percent=minimum_custom_margin,
    )
    waived_break_even = mixed_break_even_vehicle_count(
        items=portfolio_items,
        base_fleet_vehicles=vehicle_decimal,
        months=months,
        charge_installation=False,
        fixed_cost=fixed_implementation_cost,
        target_margin_percent=minimum_custom_margin,
    )

    equilibrium_cols = st.columns(3)
    equilibrium_cols[0].metric(
        "Piso de governança",
        f"{minimum_custom_margin:.2f}%",
    )
    equilibrium_cols[1].metric(
        "Equilíbrio cobrando instalação",
        (
            f"{charged_break_even} veículo(s)"
            if charged_break_even is not None
            else "Não atinge"
        ),
    )
    equilibrium_cols[2].metric(
        "Equilíbrio isentando instalação",
        (
            f"{waived_break_even} veículo(s)"
            if waived_break_even is not None
            else "Não atinge"
        ),
    )

    _render_break_even_chart(
        scenario_quantities,
        portfolio_items=portfolio_items,
        base_fleet_vehicles=vehicle_decimal,
        months=months,
        fixed_cost=fixed_implementation_cost,
        minimum_margin_percent=minimum_custom_margin,
    )

    scenario_tabs = st.tabs(
        ["Cobrando instalação", "Isentando instalação"]
    )

    for tab, scenario_charge in zip(
        scenario_tabs,
        [True, False],
    ):
        with tab:
            break_even = (
                charged_break_even
                if scenario_charge
                else waived_break_even
            )

            if break_even is None:
                st.warning(
                    f"A estrutura atual não alcança "
                    f"{minimum_custom_margin:.2f}% de margem, "
                    "mesmo aumentando a frota mantendo o mix atual. "
                    "Isso não impede a simulação, mas exige "
                    "decisão comercial para emissão."
                )
            else:
                st.success(
                    f"Quantidade mínima de veículos para atingir "
                    f"{minimum_custom_margin:.2f}% mantendo o mix atual: "
                    f"{break_even} veículo(s)."
                )

            scenario_df = pd.DataFrame(
                mixed_quantity_scenarios(
                    scenario_quantities,
                    items=portfolio_items,
                    base_fleet_vehicles=vehicle_decimal,
                    months=months,
                    charge_installation=scenario_charge,
                    fixed_cost=fixed_implementation_cost,
                )
            )

            with st.expander("Ver tabela detalhada do cenário"):
                st.dataframe(
                    scenario_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Veículos": st.column_config.NumberColumn(
                            "Veículos",
                            format="%d",
                        ),
                        "Receita do contrato": (
                            st.column_config.NumberColumn(
                                "Receita do contrato",
                                format="R$ %.2f",
                            )
                        ),
                        "Custo total": (
                            st.column_config.NumberColumn(
                                "Custo total",
                                format="R$ %.2f",
                            )
                        ),
                        "Margem total": (
                            st.column_config.NumberColumn(
                                "Margem total",
                                format="R$ %.2f",
                            )
                        ),
                        "Margem (%)": (
                            st.column_config.NumberColumn(
                                "Margem (%)",
                                format="%.2f%%",
                            )
                        ),
                        "Payback instalação (meses)": (
                            st.column_config.NumberColumn(
                                "Payback instalação (meses)",
                                format="%.2f",
                            )
                        ),
                    },
                )

    custom_discount_products = [
        product for product, item in selected.items() if bool(item["custom_discount"])
    ]
    installation_has_impact = (
        installation_sale_per_vehicle > 0 or installation_cost_per_vehicle > 0
    )
    installation_waived = not charge_installation and installation_has_impact
    approval_reasons: list[str] = []
    if below_margin_floor:
        if fixed_cost_caused_policy_failure:
            approval_reasons.append(
                "Custo fixo de implantação reduz a margem final: "
                f"{money(fixed_implementation_cost)} por proposta; "
                f"margem operacional {_margin_label(operational_margin_percent)}; "
                f"margem final {_margin_label(chosen_margin_percent)}"
            )
        else:
            approval_reasons.append(
                "Margem final abaixo do piso: "
                f"{_margin_label(chosen_margin_percent)} < "
                f"{minimum_custom_margin:.2f}%"
            )
        if custom_discount_products:
            approval_reasons.append(
                "Desconto personalizado em: " + ", ".join(custom_discount_products)
            )
        if installation_waived:
            approval_reasons.append("Instalação isenta com impacto na rentabilidade")

    analysis = {
        "months": months,
        "portfolio_items": portfolio_items,
        "recurring_sale_per_vehicle": recurring_sale_per_vehicle,
        "recurring_cost_per_vehicle": recurring_cost_per_vehicle,
        "one_time_cost_per_vehicle": one_time_cost_per_vehicle,
        "installation_sale_per_vehicle": installation_sale_per_vehicle,
        "installation_cost_per_vehicle": installation_cost_per_vehicle,
        "all_costs_configured": all_costs_configured,
        "charged_totals": charged_totals,
        "waived_totals": waived_totals,
        "charged_operational_totals": charged_operational_totals,
        "waived_operational_totals": waived_operational_totals,
        "chosen_totals": chosen_totals,
        "chosen_operational_totals": chosen_operational_totals,
        "fixed_cost_caused_policy_failure": fixed_cost_caused_policy_failure,
        "charge_installation": charge_installation,
        "below_margin_floor": below_margin_floor,
        "approval_required": below_margin_floor,
        "approval_reasons": approval_reasons,
    }

submitted = st.button(
    "Calcular e registrar proposta",
    type="primary",
    width="stretch",
    key="pj_submit",
    disabled=not selected,
)

if submitted and analysis is not None:
    if not company.strip() or not responsible.strip():
        st.warning("Informe a empresa e o responsável.")
    elif not bool(analysis["all_costs_configured"]):
        st.warning(
            "Cadastre os custos mensais de todos os produtos selecionados antes de registrar a proposta. "
            "A simulação visual continua disponível, mas não é seguro submeter uma proposta sem custo real."
        )
    else:
        chosen_totals = analysis["chosen_totals"]
        approval_required = bool(analysis["approval_required"])
        approval_reasons = list(analysis["approval_reasons"])
        status = "pending_approval" if approval_required else "approved"
        validity_label = (date.today() + timedelta(days=int(validity_days))).strftime("%d/%m/%Y")

        proposal_items: list[dict[str, str]] = []
        item_rows: list[dict[str, object]] = []
        database_items: list[dict[str, object]] = []
        for product, item in selected.items():
            effective_price = quantize_money(item["price"])
            pricing_cost = quantize_money(item["pricing_cost"])
            item_quantity = int(item["quantity"])
            margin_value = gross_margin_value(
                effective_price,
                pricing_cost,
            )
            margin_percent = gross_margin_percent(
                effective_price,
                pricing_cost,
            )
            proposal_items.append(
                {
                    "nome": product,
                    "descricao": (
                        f"{descriptions.get(product, product)} · "
                        f"Quantidade: {item_quantity}"
                    ),
                    "preco": (
                        f"{money(effective_price)} por unidade/mês · "
                        f"{item_quantity} un."
                    ),
                }
            )
            database_items.append(
                {
                    "produto": product,
                    "quantidade": item_quantity,
                    "condicao": str(item["pricing_mode"]),
                    "preco_padrao": _safe_float(item["base_price"]),
                    "preco_mensal": _safe_float(effective_price),
                    "custo_mensal": _safe_float(item["pricing_cost"]),
                    "custo_mensal_recorrente": _safe_float(
                        item["recurring_cost"]
                    ),
                    "custo_unico_veiculo": _safe_float(
                        item["one_time_cost"]
                    ),
                    "composicao_custos": list(item["cost_details"]),
                    "margem_unitaria": _safe_float(margin_value),
                    "margem_percentual": _safe_float(margin_percent or 0),
                    "preco_instalacao": _safe_float(item["installation_sale"]),
                    "custo_instalacao": _safe_float(item["installation_cost"]),
                    "desconto_personalizado": bool(item["custom_discount"]),
                }
            )
            item_rows.append(
                {
                    "Produto": product,
                    "Quantidade": item_quantity,
                    "Condição": str(item["pricing_mode"]),
                    "Preço padrão": _safe_float(item["base_price"]),
                    "Preço aplicado": _safe_float(effective_price),
                    "Custo mensal recorrente": _safe_float(
                        item["recurring_cost"]
                    ),
                    "Custo único/veículo": _safe_float(
                        item["one_time_cost"]
                    ),
                    "Custo mensal equivalente": _safe_float(
                        item["pricing_cost"]
                    ),
                    "Margem unitária": _safe_float(margin_value),
                    "Margem (%)": _safe_float(margin_percent or 0),
                    "Instalação cobrada": _safe_float(item["installation_sale"]),
                    "Custo de instalação": _safe_float(item["installation_cost"]),
                }
            )

        if to_decimal(analysis["installation_cost_per_vehicle"]) > 0 or to_decimal(
            analysis["installation_sale_per_vehicle"]
        ) > 0:
            proposal_items.append(
                {
                    "nome": "Instalação dos equipamentos",
                    "descricao": (
                        "Cobrança única conforme a quantidade de cada produto"
                        if bool(analysis["charge_installation"])
                        else "Instalação isenta para o cliente"
                    ),
                    "preco": (
                        f"{money(chosen_totals['installation_revenue'])} total"
                        if bool(analysis["charge_installation"])
                        else "Isenta"
                    ),
                }
            )

        context = {
            "NOME_EMPRESA": company.strip(),
            "NOME_RESPONSAVEL": responsible.strip(),
            "NOME_CONSULTOR": USER_NAME,
            "DATA_VALIDADE": validity_label,
            "QTD_VEICULOS": str(vehicle_count),
            "TEMPO_CONTRATO": contract_term,
            "VALOR_MENSAL_FROTA": money(chosen_totals["monthly_revenue"]),
            "VALOR_TOTAL_CONTRATO": money(chosen_totals["total_revenue"]),
            "SOMA_TOTAL_MENSAL_VEICULO": money(analysis["recurring_sale_per_vehicle"]),
            "CONDICAO_INSTALACAO": installation_policy,
            "itens_proposta": proposal_items,
        }

        proposal_document = {
            "tipo": "PJ",
            "empresa": company.strip(),
            "responsavel": responsible.strip(),
            "consultor": USER_NAME,
            "consultor_username": USERNAME,
            "submitted_by_name": USER_NAME,
            "submitted_by_username": USERNAME,
            "valor_total": _safe_float(chosen_totals["total_revenue"]),
            "status": status,
            "approval_required": approval_required,
            "approval_reasons": approval_reasons,
            "minimum_margin_percent": _safe_float(minimum_custom_margin),
            "below_margin_floor": bool(analysis["below_margin_floor"]),
            "pricing_policy_status": "requires_head_approval" if approval_required else "within_policy",
            "offer_reference": active_reference if active_reference in OFFER_PRESETS else None,
            "quantidade_veiculos": int(vehicle_count),
            "mix_dispositivos": {
                product: int(item["quantity"])
                for product, item in selected.items()
            },
            "prazo_contrato": contract_term,
            "instalacao": installation_policy,
            "preco_mensal_veiculo": _safe_float(analysis["recurring_sale_per_vehicle"]),
            "custo_mensal_veiculo": _safe_float(
                analysis["recurring_cost_per_vehicle"]
            ),
            "custo_unico_veiculo": _safe_float(
                analysis["one_time_cost_per_vehicle"]
            ),
            "preco_instalacao_veiculo": _safe_float(analysis["installation_sale_per_vehicle"]),
            "custo_instalacao_veiculo": _safe_float(analysis["installation_cost_per_vehicle"]),
            "custo_fixo_implantacao": _safe_float(fixed_implementation_cost),
            "receita_total": _safe_float(chosen_totals["total_revenue"]),
            "custo_operacional_total": _safe_float(
                analysis["chosen_operational_totals"]["total_cost"]
            ),
            "custo_total": _safe_float(chosen_totals["total_cost"]),
            "margem_operacional_total": _safe_float(
                analysis["chosen_operational_totals"]["total_margin"]
            ),
            "margem_operacional_percentual": _safe_float(
                analysis["chosen_operational_totals"]["margin_percent"] or 0
            ),
            "margem_total": _safe_float(chosen_totals["total_margin"]),
            "margem_percentual": _safe_float(chosen_totals["margin_percent"] or 0),
            "itens": database_items,
            "document_context": context,
        }

        proposal_id = db.create_pj_proposal(proposal_document)
        if not proposal_id:
            st.error("Não foi possível registrar a proposta no banco de dados.")
        else:
            st.session_state.pj_results = {
                "proposal_id": proposal_id,
                "status": status,
                "approval_required": approval_required,
                "approval_reasons": approval_reasons,
                "minimum_margin_percent": minimum_custom_margin,
                "chosen_totals": chosen_totals,
                "charged_totals": analysis["charged_totals"],
                "waived_totals": analysis["waived_totals"],
                "item_rows": item_rows,
                "context": context,
            }
            db.add_log(
                USERNAME,
                "Registrou proposta PJ",
                {
                    "proposta_id": proposal_id,
                    "empresa": company.strip(),
                    "veiculos": vehicle_count,
                    "prazo": contract_term,
                    "status": status,
                    "margem_percentual": _safe_float(chosen_totals["margin_percent"] or 0),
                    "piso_margem": _safe_float(minimum_custom_margin),
                    "motivos_aprovacao": approval_reasons,
                },
            )
            if status == "pending_approval":
                st.warning(
                    "Proposta registrada para aprovação do Head Comercial. Os valores simulados permanecem visíveis, "
                    "mas o documento comercial só poderá ser baixado depois da aprovação."
                )
            else:
                st.success("Proposta dentro da política e liberada para emissão.")

result = st.session_state.get("pj_results")
if result:
    st.markdown("### Resultado registrado")
    status = str(result.get("status") or "")
    status_cols = st.columns(5)
    chosen = result["chosen_totals"]
    status_cols[0].metric("Status", _status_label(status))
    status_cols[1].metric("Receita total", money(chosen["total_revenue"]))
    status_cols[2].metric("Margem total", money(chosen["total_margin"]))
    status_cols[3].metric("Margem (%)", _margin_label(chosen["margin_percent"]))
    status_cols[4].metric("Piso", f"{to_decimal(result.get('minimum_margin_percent', minimum_custom_margin)):.2f}%")

    if result.get("approval_reasons"):
        st.warning("Motivos de aprovação: " + "; ".join(result["approval_reasons"]))

    st.dataframe(
        pd.DataFrame(result["item_rows"]),
        width="stretch",
        hide_index=True,
        column_config={
            "Quantidade": st.column_config.NumberColumn(
                "Quantidade",
                format="%d",
            ),
            "Preço padrão": st.column_config.NumberColumn("Preço padrão", format="R$ %.2f"),
            "Preço aplicado": st.column_config.NumberColumn("Preço aplicado", format="R$ %.2f"),
            "Custo mensal recorrente": st.column_config.NumberColumn(
                "Custo mensal recorrente",
                format="R$ %.2f",
            ),
            "Custo único/veículo": st.column_config.NumberColumn(
                "Custo único/veículo",
                format="R$ %.2f",
            ),
            "Custo mensal equivalente": st.column_config.NumberColumn(
                "Custo mensal equivalente",
                format="R$ %.2f",
            ),
            "Margem unitária": st.column_config.NumberColumn("Margem unitária", format="R$ %.2f"),
            "Margem (%)": st.column_config.NumberColumn("Margem (%)", format="%.2f%%"),
            "Instalação cobrada": st.column_config.NumberColumn("Instalação cobrada", format="R$ %.2f"),
            "Custo de instalação": st.column_config.NumberColumn("Custo de instalação", format="R$ %.2f"),
        },
    )

    if status == "approved":
        try:
            document_bytes = generate_pj_proposal(result["context"])
            safe_company = "_".join(result["context"]["NOME_EMPRESA"].split())
            st.download_button(
                "Baixar proposta liberada em DOCX",
                data=document_bytes,
                file_name=f"Proposta_{safe_company}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
        except Exception as exc:
            st.error(f"Não foi possível gerar o documento: {exc}")
    else:
        st.info(
            "O resultado econômico continua disponível nesta tela. O arquivo da proposta permanece bloqueado "
            "até a decisão do Head Comercial."
        )
        st.page_link(
            "pages/12_Aprovacoes_Comerciais.py",
            label="Acompanhar aprovação",
            width="stretch",
        )
