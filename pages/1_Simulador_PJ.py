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
    validate_minimum_margin,
)
from app_core.proposal_documents import generate_pj_proposal
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Simulador Pessoa Jurídica")
apply_branding()
require_auth()
render_sidebar()
render_hero(
    "Simulador de venda — Pessoa Jurídica",
    "Simule preço, instalação, rentabilidade, equilíbrio da frota e fluxo de aprovação comercial.",
)

ROLE = str(st.session_state.get("role") or "user")
USERNAME = str(st.session_state.get("username") or "").strip().lower()
USER_NAME = str(st.session_state.get("name") or USERNAME or "Usuário")
IS_APPROVER = ROLE in {"admin", "head_comercial"}

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

if "pj_results" not in st.session_state:
    st.session_state.pj_results = None


def _product_key(product: str) -> str:
    return hashlib.sha1(product.encode("utf-8")).hexdigest()[:10]


def _margin_label(percent: Decimal | None) -> str:
    return "Não disponível" if percent is None else f"{percent:.2f}%"


def _status_label(status: str) -> str:
    return {
        "approved": "Aprovada",
        "pending_approval": "Aguardando aprovação",
        "rejected": "Rejeitada",
    }.get(status, status or "Sem status")


def _safe_float(value: object) -> float:
    return float(to_decimal(value))


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

st.markdown("#### Produtos e serviços")
st.info(
    "O comercial pode usar preço ou margem personalizados, mas nenhuma condição personalizada "
    f"pode ficar abaixo de {minimum_custom_margin:.2f}% de margem. Descontos e isenção de "
    "instalação seguem para aprovação do Head Comercial."
)

selected: dict[str, dict[str, object]] = {}
current_plan_costs = costs_by_plan.get(contract_term, {})
validation_errors: list[str] = []

for product_index, (product, base_price) in enumerate(plans[contract_term].items()):
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
                    min_value=float(floor_price),
                    value=max(float(base_price), float(floor_price)),
                    step=1.0,
                    format="%.2f",
                    key=f"pj_custom_value_{contract_term}_{product_id}",
                    help=(
                        f"Preço mínimo permitido para manter {minimum_custom_margin:.2f}% de margem: "
                        f"{money(floor_price)}."
                    ),
                )
                effective_price = quantize_money(custom_value)
            elif pricing_mode == "Margem personalizada":
                default_margin = max(
                    float(minimum_custom_margin),
                    min(float(base_margin_percent or minimum_custom_margin), 99.0),
                )
                target_margin = st.number_input(
                    "Margem desejada sobre o preço de venda (%)",
                    min_value=float(minimum_custom_margin),
                    max_value=99.0,
                    value=default_margin,
                    step=0.5,
                    format="%.2f",
                    key=f"pj_custom_margin_{contract_term}_{product_id}",
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

            if pricing_mode != "Preço padrão" and recurring_cost_configured:
                valid_margin, calculated_percent = validate_minimum_margin(
                    effective_price,
                    recurring_cost,
                    minimum_custom_margin,
                )
                if not valid_margin:
                    validation_errors.append(
                        f"{product}: condição personalizada com margem "
                        f"{_margin_label(calculated_percent)}, abaixo do piso de "
                        f"{minimum_custom_margin:.2f}%."
                    )

            if effective_margin_value is not None:
                message = (
                    f"Margem simulada: {money(effective_margin_value)} "
                    f"({_margin_label(effective_margin_percent)}) por veículo/mês."
                )
                if effective_margin_percent is not None and effective_margin_percent >= minimum_custom_margin:
                    st.success(message)
                else:
                    st.warning(message)

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
                st.error(
                    f"A estrutura atual não alcança {minimum_custom_margin:.2f}% de margem, "
                    "mesmo aumentando a quantidade de veículos."
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
    has_personalized_condition = any(
        str(item["pricing_mode"]) != "Preço padrão" for item in selected.values()
    )
    installation_has_impact = (
        installation_sale_per_vehicle > 0 or installation_cost_per_vehicle > 0
    )
    installation_waived = not charge_installation and installation_has_impact
    approval_reasons: list[str] = []
    if custom_discount_products:
        approval_reasons.append(
            "Desconto personalizado em: " + ", ".join(custom_discount_products)
        )
    if installation_waived:
        approval_reasons.append("Isenção da cobrança de instalação")
    approval_required = bool(approval_reasons)

    chosen_margin_percent = chosen_totals["margin_percent"]
    if (has_personalized_condition or installation_waived) and (
        chosen_margin_percent is None or chosen_margin_percent < minimum_custom_margin
    ):
        validation_errors.append(
            "A condição final da proposta ficou com margem de "
            f"{_margin_label(chosen_margin_percent)}, abaixo do piso de "
            f"{minimum_custom_margin:.2f}% após considerar instalação e custos da implantação."
        )

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
        "approval_required": approval_required,
        "approval_reasons": approval_reasons,
    }

if validation_errors:
    st.error("A proposta possui condições comerciais inválidas:")
    for error in dict.fromkeys(validation_errors):
        st.markdown(f"- {error}")

submitted = st.button(
    "Calcular e registrar proposta",
    type="primary",
    width="stretch",
    key="pj_submit",
    disabled=not selected or bool(validation_errors),
)

if submitted and analysis is not None:
    if not company.strip() or not responsible.strip():
        st.warning("Informe a empresa e o responsável.")
    elif not bool(analysis["all_costs_configured"]):
        st.warning(
            "Cadastre os custos mensais de todos os produtos selecionados antes de registrar a proposta."
        )
    else:
        chosen_totals = analysis["chosen_totals"]
        approval_required = bool(analysis["approval_required"])
        approval_reasons = list(analysis["approval_reasons"])
        status = "approved" if not approval_required or IS_APPROVER else "pending_approval"
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
            "approved_by_username": USERNAME if status == "approved" and approval_required else None,
            "approved_by_name": USER_NAME if status == "approved" and approval_required else None,
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
                    "motivos_aprovacao": approval_reasons,
                },
            )
            if status == "pending_approval":
                st.warning(
                    "Proposta registrada e enviada para aprovação do Head Comercial. "
                    "O documento só poderá ser baixado depois da aprovação."
                )
            else:
                st.success("Proposta registrada e aprovada para emissão.")

result = st.session_state.get("pj_results")
if result:
    st.markdown("### Resultado registrado")
    status = str(result.get("status") or "")
    status_cols = st.columns(4)
    chosen = result["chosen_totals"]
    status_cols[0].metric("Status", _status_label(status))
    status_cols[1].metric("Receita total", money(chosen["total_revenue"]))
    status_cols[2].metric("Margem total", money(chosen["total_margin"]))
    status_cols[3].metric("Margem (%)", _margin_label(chosen["margin_percent"]))

    if result.get("approval_reasons"):
        st.caption("Motivos de aprovação: " + "; ".join(result["approval_reasons"]))

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
                "Baixar proposta aprovada em DOCX",
                data=document_bytes,
                file_name=f"Proposta_{safe_company}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
        except Exception as exc:
            st.error(f"Não foi possível gerar o documento: {exc}")
    else:
        st.info(
            "Acompanhe o andamento em Aprovações comerciais. O download será liberado após a aprovação."
        )
        st.page_link(
            "pages/12_Aprovacoes_Comerciais.py",
            label="Acompanhar aprovação",
            width="stretch",
        )
