from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

import pandas as pd
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Simulador de Licitações")
apply_branding()
require_auth()
render_sidebar()
render_hero("Simulador para licitações e editais", "Estruture custos, serviços, amortização e margem para estimar o valor global do contrato.")

pricing = db.get_pricing_config()
hardware_costs = {name: Decimal(str(value)) for name, value in pricing.get("PRECO_CUSTO_LICITACAO", {}).items()}
amortization_months = Decimal(str(pricing.get("AMORTIZACAO_HARDWARE_MESES", 12)))

if "bid_results" not in st.session_state:
    st.session_state.bid_results = None

with st.form("bid_simulation"):
    scope_col, cost_col = st.columns(2)
    with scope_col:
        st.markdown("#### Escopo")
        entity_name = st.text_input("Órgão ou identificação da licitação")
        vehicle_count = Decimal(st.number_input("Quantidade de veículos", min_value=1, value=1, step=1))
        contract_months = Decimal(st.number_input("Prazo do contrato (meses)", min_value=1, value=12, step=1))
        margin_percent = st.number_input("Margem sobre o custo (%)", min_value=0.0, max_value=500.0, value=30.0, step=1.0)
        margin = Decimal(str(margin_percent)) / Decimal("100")

    with cost_col:
        st.markdown("#### Serviços unitários")
        installation_cost = Decimal(str(st.number_input("Instalação", min_value=0.0, value=50.0, step=10.0, format="%.2f")))
        maintenance_cost = Decimal(str(st.number_input("Manutenção", min_value=0.0, value=50.0, step=10.0, format="%.2f")))
        removal_cost = Decimal(str(st.number_input("Desinstalação", min_value=0.0, value=50.0, step=10.0, format="%.2f")))

    product_col, services_col = st.columns(2)
    with product_col:
        st.markdown("#### Itens de locação")
        selected_items = [
            item
            for index, (item, cost) in enumerate(hardware_costs.items())
            if st.toggle(f"{item} — custo {money(cost)}", key=f"bid_item_{index}")
        ]

    with services_col:
        st.markdown("#### Serviços adicionais")
        include_installation = st.toggle("Incluir instalação")
        include_maintenance = st.toggle("Incluir manutenção")
        maintenance_quantity = Decimal(st.number_input("Quantidade de manutenções", min_value=1, value=1, step=1, disabled=not include_maintenance))
        include_removal = st.toggle("Incluir desinstalação")
        removal_quantity = Decimal(st.number_input("Quantidade de desinstalações", min_value=1, value=1, step=1, disabled=not include_removal))

    submitted = st.form_submit_button("Calcular e registrar proposta", type="primary", width="stretch")

if submitted:
    if not entity_name.strip():
        st.warning("Informe o órgão ou a identificação da licitação.")
    elif not selected_items and not any([include_installation, include_maintenance, include_removal]):
        st.warning("Selecione pelo menos um item ou serviço.")
    else:
        rows: list[dict] = []
        monthly_per_vehicle = Decimal("0")

        for item in selected_items:
            monthly_cost = (hardware_costs[item] / amortization_months).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            monthly_sale = (monthly_cost * (Decimal("1") + margin)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            item_total = monthly_sale * vehicle_count * contract_months
            monthly_per_vehicle += monthly_sale
            rows.append(
                {
                    "Item": f"Locação — {item}",
                    "Quantidade": f"{int(vehicle_count)} x {int(contract_months)} meses",
                    "Valor unitário": monthly_sale,
                    "Valor total": item_total,
                }
            )

        if include_installation:
            total = installation_cost * vehicle_count
            rows.append({"Item": "Instalação", "Quantidade": int(vehicle_count), "Valor unitário": installation_cost, "Valor total": total})
        if include_maintenance:
            total = maintenance_cost * maintenance_quantity
            rows.append({"Item": "Manutenção", "Quantidade": int(maintenance_quantity), "Valor unitário": maintenance_cost, "Valor total": total})
        if include_removal:
            total = removal_cost * removal_quantity
            rows.append({"Item": "Desinstalação", "Quantidade": int(removal_quantity), "Valor unitário": removal_cost, "Valor total": total})

        global_total = sum((row["Valor total"] for row in rows), Decimal("0"))
        st.session_state.bid_results = {
            "rows": rows,
            "monthly_per_vehicle": monthly_per_vehicle,
            "global_total": global_total,
        }
        db.upsert_proposal(
            {
                "tipo": "Licitação",
                "empresa": entity_name.strip(),
                "consultor": st.session_state.get("name", "N/A"),
                "valor_total": float(global_total),
            }
        )
        db.add_log(
            st.session_state.get("username", "sistema"),
            "Simulou licitação",
            {"licitacao": entity_name.strip(), "veiculos": int(vehicle_count), "valor_total": float(global_total)},
        )
        st.success("Estimativa registrada no dashboard.")

result = st.session_state.get("bid_results")
if result:
    st.markdown("### Resultado")
    metric_1, metric_2 = st.columns(2)
    metric_1.metric("Mensal por veículo em locação", money(result["monthly_per_vehicle"]))
    metric_2.metric("Valor global estimado", money(result["global_total"]))

    details = pd.DataFrame(result["rows"])
    st.dataframe(
        details,
        width="stretch",
        hide_index=True,
        column_config={
            "Item": "Produto ou serviço",
            "Quantidade": "Quantidade",
            "Valor unitário": st.column_config.NumberColumn("Valor unitário", format="R$ %.2f"),
            "Valor total": st.column_config.NumberColumn("Valor total", format="R$ %.2f"),
        },
    )

if st.button("Limpar simulação"):
    st.session_state.bid_results = None
    st.rerun()
