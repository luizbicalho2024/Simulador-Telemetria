from __future__ import annotations

import hashlib
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.pricing import (
    MIN_CUSTOM_MARGIN_PERCENT,
    break_even_vehicle_count,
    gross_margin_percent,
    gross_margin_value,
    minimum_sale_price,
    proposal_totals,
    quantity_scenarios,
    quantize_money,
    sale_price_from_margin,
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
        "range": "R$ 49–69/mês",
        "keywords": ("gprs", "gsm"),
    },
    "VERDIO Fleet": {
        "subtitle": "Start + CAN + RFID",
        "positioning": "Eficiência / combustível",
        "range": "R$ 89–129/mês",
        "keywords": ("gprs", "gsm", "can", "rfid", "identificador"),
    },
    "VERDIO Safety": {
        "subtitle": "Fleet + vídeo + DMS/ADAS",
        "positioning": "Risco, sinistro e jornada",
        "range": "R$ 179–299/mês",
        "keywords": ("gprs", "gsm", "can", "rfid", "identificador", "video", "vídeo", "dms", "adas"),
    },
    "VERDIO Sat": {
        "subtitle": "Cobertura satelital para operações críticas",
        "positioning": "Sombra de sinal / agro / rota longa",
        "range": "R$ 149–229/mês",
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


def _apply_preset(preset_name: str, contract_term: str) -> None:
    for product in plans.get(contract_term, {}):
        product_id = _product_key(product)
        st.session_state[f"pj_enabled_{contract_term}_{product_id}"] = _product_matches(product, preset_name)
        st.session_state.pop(f"pj_mode_{contract_term}_{product_id}", None)
        st.session_state.pop(f"pj_custom_value_{contract_term}_{product_id}", None)
        st.session_state.pop(f"pj_custom_margin_{contract_term}_{product_id}", None)
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
    st.caption("Mensalidades são unitárias por veículo; instalação é uma cobrança única.")

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
    "Use os pacotes como ponto de partida. As faixas abaixo são referência de posicionamento; "
    "a margem real calculada pelo simulador é quem determina a necessidade de aprovação."
)
preset_columns = st.columns(4)
for index, (preset_name, preset) in enumerate(OFFER_PRESETS.items()):
    with preset_columns[index]:
        with st.container(border=True):
            st.markdown(f"**{preset_name}**")
            st.caption(str(preset["subtitle"]))
            st.caption(str(preset["positioning"]))
            st.markdown(f"**{preset['range']}**")
            if st.button(
                f"Aplicar {preset_name.replace('VERDIO ', '')}",
                width="stretch",
                key=f"pj_preset_{index}",
            ):
                _apply_preset(preset_name, contract_term)
                st.rerun()

active_reference = st.session_state.get("pj_offer_reference")
if active_reference in OFFER_PRESETS:
    st.info(f"Referência ativa: {active_reference}. Você pode incluir, remover ou reprificar itens livremente.")

st.markdown("#### Produtos e serviços")
st.info(
    f"Piso de governança: {minimum_custom_margin:.2f}% de margem total da proposta. "
    "O comercial pode simular preços e margens abaixo desse piso. Quando a condição final ficar "
    "abaixo da política, a proposta será registrada para decisão do Head Comercial e o download "
    "permanecerá bloqueado até a aprovação."
)

selected: dict[str, dict[str, object]] = {}
current_plan_costs = costs_by_plan.get(contract_term, {})

for product, base_price in plans[contract_term].items():
    product_id = _product_key(product)
    recurring_cost = quantize_money(current_plan_costs.get(product, 0))
    recurring_cost_configured = recurring_cost > 0
    installation_config = installation_by_product.get(product, {})
    installation_sale = quantize_money(installation_config.get("preco_venda", 0))
    installation_cost = quantize_money(installation_config.get("custo", 0))

    base_margin_value = (
        gross_margin_value(base_price, recurring_cost)
        if recurring_cost_configured
        else None
    )
    base_margin_percent = (
        gross_margin_percent(base_price, recurring_cost)
        if recurring_cost_configured
        else None
    )

    with st.container(border=True):
        enable_col, value_col = st.columns([1.65, 1])
        with enable_col:
            enabled = st.toggle(
                product,
                key=f"pj_enabled_{contract_term}_{product_id}",
            )
            st.caption(descriptions.get(product, product))
        with value_col:
            st.markdown(f"**Preço padrão: {money(base_price)}**")
            st.caption("por veículo/mês")

        info_1, info_2, info_3, info_4 = st.columns(4)
        info_1.metric(
            "Custo mensal",
            money(recurring_cost) if recurring_cost_configured else "Não cadastrado",
        )
        info_2.metric(
            "Margem padrão",
            money(base_margin_value) if base_margin_value is not None else "Pendente",
        )
        info_3.metric("Margem padrão (%)", _margin_label(base_margin_percent))
        info_4.metric(
            "Instalação",
            f"{money(installation_sale)} / custo {money(installation_cost)}",
        )

        effective_price = base_price
        pricing_mode = "Preço padrão"
        custom_discount = False

        if enabled:
            modes = ["Preço padrão"]
            if recurring_cost_configured:
                modes.extend(["Valor personalizado", "Margem personalizada"])
            else:
                st.warning(
                    "Cadastre o custo mensal deste produto antes de usar uma condição personalizada."
                )

            pricing_mode = st.selectbox(
                "Condição comercial",
                modes,
                key=f"pj_mode_{contract_term}_{product_id}",
            )

            if pricing_mode == "Valor personalizado":
                floor_price = minimum_sale_price(recurring_cost, minimum_custom_margin)
                custom_value = st.number_input(
                    "Preço mensal personalizado por veículo",
                    min_value=0.01,
                    value=max(0.01, float(base_price)),
                    step=1.0,
                    format="%.2f",
                    key=f"pj_custom_value_{contract_term}_{product_id}",
                    help=(
                        f"Referência para manter {minimum_custom_margin:.2f}% de margem unitária: "
                        f"{money(floor_price)}. Valores menores são permitidos para simulação."
                    ),
                )
                effective_price = quantize_money(custom_value)
            elif pricing_mode == "Margem personalizada":
                default_margin = min(
                    max(float(base_margin_percent or minimum_custom_margin), -500.0),
                    99.0,
                )
                target_margin = st.number_input(
                    "Margem desejada sobre o preço de venda (%)",
                    min_value=-500.0,
                    max_value=99.0,
                    value=default_margin,
                    step=0.5,
                    format="%.2f",
                    key=f"pj_custom_margin_{contract_term}_{product_id}",
                    help=(
                        "Margens abaixo do piso, inclusive negativas, podem ser simuladas. "
                        "A proposta final será submetida à alçada comercial quando necessário."
                    ),
                )
                effective_price = sale_price_from_margin(recurring_cost, target_margin)
                st.caption(f"Preço calculado: {money(effective_price)} por veículo/mês")

            effective_margin_value = (
                gross_margin_value(effective_price, recurring_cost)
                if recurring_cost_configured
                else None
            )
            effective_margin_percent = (
                gross_margin_percent(effective_price, recurring_cost)
                if recurring_cost_configured
                else None
            )
            custom_discount = pricing_mode != "Preço padrão" and effective_price < base_price

            if effective_margin_value is not None:
                message = (
                    f"Margem simulada: {money(effective_margin_value)} "
                    f"({_margin_label(effective_margin_percent)}) por veículo/mês."
                )
                if effective_margin_percent is not None and effective_margin_percent >= minimum_custom_margin:
                    st.success(message + " Dentro da política de margem.")
                else:
                    st.warning(message + " Abaixo do piso; a decisão será feita pela margem consolidada da proposta.")

            selected[product] = {
                "base_price": base_price,
                "price": effective_price,
                "recurring_cost": recurring_cost,
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
    recurring_sale_per_vehicle = quantize_money(
        sum((to_decimal(item["price"]) for item in selected.values()), Decimal("0"))
    )
    recurring_cost_per_vehicle = quantize_money(
        sum((to_decimal(item["recurring_cost"]) for item in selected.values()), Decimal("0"))
    )
    installation_sale_per_vehicle = quantize_money(
        sum((to_decimal(item["installation_sale"]) for item in selected.values()), Decimal("0"))
    )
    installation_cost_per_vehicle = quantize_money(
        sum((to_decimal(item["installation_cost"]) for item in selected.values()), Decimal("0"))
    )
    all_costs_configured = all(bool(item["cost_configured"]) for item in selected.values())

    charged_totals = proposal_totals(
        recurring_sale_per_vehicle=recurring_sale_per_vehicle,
        recurring_cost_per_vehicle=recurring_cost_per_vehicle,
        months=months,
        vehicles=vehicle_decimal,
        installation_sale_per_vehicle=installation_sale_per_vehicle,
        installation_cost_per_vehicle=installation_cost_per_vehicle,
        charge_installation=True,
        fixed_cost=fixed_implementation_cost,
    )
    waived_totals = proposal_totals(
        recurring_sale_per_vehicle=recurring_sale_per_vehicle,
        recurring_cost_per_vehicle=recurring_cost_per_vehicle,
        months=months,
        vehicles=vehicle_decimal,
        installation_sale_per_vehicle=installation_sale_per_vehicle,
        installation_cost_per_vehicle=installation_cost_per_vehicle,
        charge_installation=False,
        fixed_cost=fixed_implementation_cost,
    )
    charge_installation = installation_policy == "Cobrar instalação"
    chosen_totals = charged_totals if charge_installation else waived_totals

    st.markdown("### Resumo executivo da simulação")
    chosen_margin_percent = chosen_totals["margin_percent"]
    below_margin_floor = (
        chosen_margin_percent is None or chosen_margin_percent < minimum_custom_margin
    )
    summary_cols = st.columns(5)
    summary_cols[0].metric("Mensalidade da frota", money(chosen_totals["monthly_revenue"]))
    summary_cols[1].metric("Receita do contrato", money(chosen_totals["total_revenue"]))
    summary_cols[2].metric("Custo total", money(chosen_totals["total_cost"]))
    summary_cols[3].metric("Margem total", money(chosen_totals["total_margin"]))
    summary_cols[4].metric("Margem final", _margin_label(chosen_margin_percent))

    if below_margin_floor:
        gap = (
            minimum_custom_margin - chosen_margin_percent
            if chosen_margin_percent is not None
            else minimum_custom_margin
        )
        st.warning(
            f"Condição fora da política: margem final de {_margin_label(chosen_margin_percent)}; "
            f"piso {minimum_custom_margin:.2f}% (desvio de {gap:.2f} p.p.). "
            "A simulação continua disponível, mas a proposta ficará bloqueada para download até aprovação do Head Comercial."
        )
    else:
        st.success(
            f"Condição dentro da política: margem final de {_margin_label(chosen_margin_percent)}, "
            f"acima do piso de {minimum_custom_margin:.2f}%."
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
            f"Custo de instalação: {money(charged_totals['installation_cost'])}"
        )
    with waived_col:
        st.markdown("#### Margem isentando instalação")
        m1, m2 = st.columns(2)
        m1.metric("Margem total", money(waived_totals["total_margin"]))
        m2.metric("Margem (%)", _margin_label(waived_totals["margin_percent"]))
        st.caption(
            f"Receita de instalação: {money(waived_totals['installation_revenue'])} · "
            f"Custo mantido na margem: {money(waived_totals['installation_cost'])}"
        )
        if waived_totals["payback_months"] is not None:
            st.caption(
                f"Recuperação do subsídio da instalação: aproximadamente "
                f"{waived_totals['payback_months']} meses."
            )

    st.markdown("### Ponto de equilíbrio por tamanho da frota")
    st.caption(
        "A quantidade altera a margem percentual quando existe custo fixo de implantação. "
        "Sem custo fixo, o percentual tende a permanecer estável e apenas a margem total cresce."
    )
    scenario_tabs = st.tabs(["Cobrando instalação", "Isentando instalação"])
    scenario_quantities = sorted(
        {
            *[int(value) for value in quantity_defaults if int(value) > 0],
            int(vehicle_count),
        }
    )

    for tab, scenario_charge in zip(scenario_tabs, [True, False]):
        with tab:
            break_even = break_even_vehicle_count(
                recurring_sale_per_vehicle=recurring_sale_per_vehicle,
                recurring_cost_per_vehicle=recurring_cost_per_vehicle,
                months=months,
                installation_sale_per_vehicle=installation_sale_per_vehicle,
                installation_cost_per_vehicle=installation_cost_per_vehicle,
                charge_installation=scenario_charge,
                fixed_cost=fixed_implementation_cost,
                target_margin_percent=minimum_custom_margin,
            )
            if break_even is None:
                st.warning(
                    f"A estrutura atual não alcança {minimum_custom_margin:.2f}% de margem, "
                    "mesmo aumentando a quantidade de veículos. Isso não impede a simulação, "
                    "mas exige decisão comercial para emissão."
                )
            else:
                st.success(
                    f"Quantidade mínima para atingir {minimum_custom_margin:.2f}% de margem: "
                    f"{break_even} veículo(s)."
                )

            scenario_df = pd.DataFrame(
                quantity_scenarios(
                    scenario_quantities,
                    recurring_sale_per_vehicle=recurring_sale_per_vehicle,
                    recurring_cost_per_vehicle=recurring_cost_per_vehicle,
                    months=months,
                    installation_sale_per_vehicle=installation_sale_per_vehicle,
                    installation_cost_per_vehicle=installation_cost_per_vehicle,
                    charge_installation=scenario_charge,
                    fixed_cost=fixed_implementation_cost,
                )
            )
            st.dataframe(
                scenario_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Veículos": st.column_config.NumberColumn("Veículos", format="%d"),
                    "Receita do contrato": st.column_config.NumberColumn(
                        "Receita do contrato", format="R$ %.2f"
                    ),
                    "Custo total": st.column_config.NumberColumn("Custo total", format="R$ %.2f"),
                    "Margem total": st.column_config.NumberColumn("Margem total", format="R$ %.2f"),
                    "Margem (%)": st.column_config.NumberColumn("Margem (%)", format="%.2f%%"),
                    "Payback instalação (meses)": st.column_config.NumberColumn(
                        "Payback instalação (meses)", format="%.2f"
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
        approval_reasons.append(
            "Margem final abaixo do piso: "
            f"{_margin_label(chosen_margin_percent)} < {minimum_custom_margin:.2f}%"
        )
        if custom_discount_products:
            approval_reasons.append(
                "Desconto personalizado em: " + ", ".join(custom_discount_products)
            )
        if installation_waived:
            approval_reasons.append("Instalação isenta com impacto na rentabilidade")

    analysis = {
        "months": months,
        "recurring_sale_per_vehicle": recurring_sale_per_vehicle,
        "recurring_cost_per_vehicle": recurring_cost_per_vehicle,
        "installation_sale_per_vehicle": installation_sale_per_vehicle,
        "installation_cost_per_vehicle": installation_cost_per_vehicle,
        "all_costs_configured": all_costs_configured,
        "charged_totals": charged_totals,
        "waived_totals": waived_totals,
        "chosen_totals": chosen_totals,
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
            recurring_cost = quantize_money(item["recurring_cost"])
            margin_value = gross_margin_value(effective_price, recurring_cost)
            margin_percent = gross_margin_percent(effective_price, recurring_cost)
            proposal_items.append(
                {
                    "nome": product,
                    "descricao": descriptions.get(product, product),
                    "preco": f"{money(effective_price)} por veículo/mês",
                }
            )
            database_items.append(
                {
                    "produto": product,
                    "condicao": str(item["pricing_mode"]),
                    "preco_padrao": _safe_float(item["base_price"]),
                    "preco_mensal": _safe_float(effective_price),
                    "custo_mensal": _safe_float(recurring_cost),
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
                    "Condição": str(item["pricing_mode"]),
                    "Preço padrão": _safe_float(item["base_price"]),
                    "Preço aplicado": _safe_float(effective_price),
                    "Custo mensal": _safe_float(recurring_cost),
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
                        "Cobrança única por veículo"
                        if bool(analysis["charge_installation"])
                        else "Instalação isenta para o cliente"
                    ),
                    "preco": (
                        money(analysis["installation_sale_per_vehicle"])
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
            "prazo_contrato": contract_term,
            "instalacao": installation_policy,
            "preco_mensal_veiculo": _safe_float(analysis["recurring_sale_per_vehicle"]),
            "custo_mensal_veiculo": _safe_float(analysis["recurring_cost_per_vehicle"]),
            "preco_instalacao_veiculo": _safe_float(analysis["installation_sale_per_vehicle"]),
            "custo_instalacao_veiculo": _safe_float(analysis["installation_cost_per_vehicle"]),
            "custo_fixo_implantacao": _safe_float(fixed_implementation_cost),
            "receita_total": _safe_float(chosen_totals["total_revenue"]),
            "custo_total": _safe_float(chosen_totals["total_cost"]),
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
            "Preço padrão": st.column_config.NumberColumn("Preço padrão", format="R$ %.2f"),
            "Preço aplicado": st.column_config.NumberColumn("Preço aplicado", format="R$ %.2f"),
            "Custo mensal": st.column_config.NumberColumn("Custo mensal", format="R$ %.2f"),
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
