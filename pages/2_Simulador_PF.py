from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Simulador Pessoa Física")
apply_branding()
require_auth()
render_sidebar()
render_hero("Simulador de venda — Pessoa Física", "Calcule desconto, parcelamento e valor final para o cliente.")

pricing = db.get_pricing_config()
prices = {name: Decimal(str(value)) for name, value in pricing.get("PRECOS_PF", {}).items()}
installment_rates = {str(term): Decimal(str(rate)) for term, rate in pricing.get("TAXAS_PARCELAMENTO_PF", {}).items()}

if "pf_results" not in st.session_state:
    st.session_state.pf_results = None

if not prices:
    st.warning("Não há produtos PF configurados.")
    st.stop()

with st.form("pf_simulation"):
    product_col, payment_col = st.columns(2)
    with product_col:
        st.markdown("#### Produto e cliente")
        customer = st.text_input("Nome do cliente")
        product = st.selectbox("Produto", list(prices))
        base_price = prices[product]
        st.metric("Preço base", money(base_price))

    with payment_col:
        st.markdown("#### Condições de pagamento")
        discount_percent = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        installment_enabled = st.toggle("Venda parcelada")
        installments = st.selectbox(
            "Quantidade de parcelas",
            list(installment_rates),
            disabled=not installment_enabled,
            format_func=lambda value: f"{value} parcelas",
        )

    submitted = st.form_submit_button("Calcular e registrar", type="primary", width="stretch")

if submitted:
    if not customer.strip():
        st.warning("Informe o nome do cliente.")
    else:
        discount = (base_price * Decimal(str(discount_percent)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        discounted_price = (base_price - discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = discounted_price
        installment_value = None
        applied_rate = Decimal("0")
        if installment_enabled:
            applied_rate = installment_rates.get(installments, Decimal("0"))
            total = (discounted_price * (Decimal("1") + applied_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            installment_value = (total / Decimal(installments)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        st.session_state.pf_results = {
            "customer": customer.strip(),
            "product": product,
            "base_price": base_price,
            "discount": discount,
            "discounted_price": discounted_price,
            "installment_enabled": installment_enabled,
            "installments": int(installments) if installment_enabled else 1,
            "installment_value": installment_value,
            "applied_rate": applied_rate,
            "total": total,
        }
        db.upsert_proposal(
            {
                "tipo": "PF",
                "empresa": customer.strip(),
                "consultor": st.session_state.get("name", "N/A"),
                "valor_total": float(total),
            }
        )
        db.add_log(
            st.session_state.get("username", "sistema"),
            "Simulou proposta PF",
            {"cliente": customer.strip(), "produto": product, "valor_total": float(total)},
        )
        st.success("Simulação registrada no dashboard.")

result = st.session_state.get("pf_results")
if result:
    st.markdown("### Resultado")
    cols = st.columns(4)
    cols[0].metric("Preço base", money(result["base_price"]))
    cols[1].metric("Desconto", money(result["discount"]))
    cols[2].metric("Após desconto", money(result["discounted_price"]))
    cols[3].metric("Total da proposta", money(result["total"]))

    if result["installment_enabled"]:
        st.info(
            f"Pagamento em {result['installments']} parcelas de {money(result['installment_value'])}. "
            f"Taxa aplicada: {float(result['applied_rate']) * 100:.2f}%."
        )
    else:
        st.info("Pagamento à vista.")

if st.button("Limpar simulação"):
    st.session_state.pf_results = None
    st.rerun()
