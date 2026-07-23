from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import docx
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Simulador Pessoa Jurídica")
apply_branding()
require_auth()
render_sidebar()
render_hero("Simulador de venda — Pessoa Jurídica", "Configure a frota, o prazo contratual e os serviços para gerar a proposta comercial.")

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "assets" / "templates" / "proposta_comercial_verdio.docx"

pricing_config = db.get_pricing_config()
plans = {
    plan: {product: Decimal(str(value)) for product, value in products.items()}
    for plan, products in pricing_config.get("PLANOS_PJ", {}).items()
}
descriptions = pricing_config.get("PRODUTOS_PJ_DESCRICAO", {})

if "pj_results" not in st.session_state:
    st.session_state.pj_results = None


def replace_in_paragraph(paragraph, replacements: dict[str, str]) -> None:
    full_text = paragraph.text
    if not any(token in full_text for token in replacements):
        return
    updated = full_text
    for token, value in replacements.items():
        updated = updated.replace(token, value)
    if paragraph.runs:
        paragraph.runs[0].text = updated
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = updated


@st.cache_data(show_spinner=False)
def generate_proposal(context: dict) -> bytes:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")

    document = docx.Document(str(TEMPLATE_PATH))
    replacements = {
        "{{" + key + "}}": str(value)
        for key, value in context.items()
        if key != "itens_proposta"
    }

    for paragraph in document.paragraphs:
        replace_in_paragraph(paragraph, replacements)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_in_paragraph(paragraph, replacements)

    if document.tables:
        product_table = document.tables[0]
        for item in context.get("itens_proposta", []):
            cells = product_table.add_row().cells
            if len(cells) >= 3:
                cells[0].text = item["nome"]
                cells[1].text = item["descricao"]
                cells[2].text = item["preco"]

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


if not plans:
    st.warning("Não há planos PJ configurados. Solicite ao administrador a inclusão dos preços.")
    st.stop()

with st.form("pj_simulation"):
    config_col, client_col = st.columns([1, 1.4])
    with config_col:
        st.markdown("#### Configuração comercial")
        vehicle_count = st.number_input("Quantidade de veículos", min_value=1, value=1, step=1)
        contract_term = st.selectbox("Prazo do contrato", list(plans))
        st.caption("Os valores abaixo são mensais e unitários.")

    with client_col:
        st.markdown("#### Dados da proposta")
        company = st.text_input("Empresa")
        responsible = st.text_input("Responsável")
        validity_days = st.number_input("Validade da proposta (dias)", min_value=1, max_value=90, value=15)

    st.markdown("#### Produtos e serviços")
    selected: dict[str, Decimal] = {}
    product_columns = st.columns(2)
    for index, (product, price) in enumerate(plans[contract_term].items()):
        label = f"{product} — {money(price)} por veículo/mês"
        if product_columns[index % 2].toggle(label, key=f"pj_product_{contract_term}_{index}"):
            selected[product] = price

    submitted = st.form_submit_button("Calcular e registrar proposta", type="primary", width="stretch")

if submitted:
    if not company.strip() or not responsible.strip():
        st.warning("Informe a empresa e o responsável.")
    elif not selected:
        st.warning("Selecione pelo menos um produto ou serviço.")
    else:
        monthly_per_vehicle = sum(selected.values(), Decimal("0"))
        monthly_fleet = monthly_per_vehicle * Decimal(vehicle_count)
        months = Decimal(contract_term.split()[0])
        contract_total = monthly_fleet * months
        validity_date = datetime.now().date().toordinal() + int(validity_days)
        validity_label = datetime.fromordinal(validity_date).strftime("%d/%m/%Y")

        context = {
            "NOME_EMPRESA": company.strip(),
            "NOME_RESPONSAVEL": responsible.strip(),
            "NOME_CONSULTOR": st.session_state.get("name", ""),
            "DATA_VALIDADE": validity_label,
            "QTD_VEICULOS": str(vehicle_count),
            "TEMPO_CONTRATO": contract_term,
            "VALOR_MENSAL_FROTA": money(monthly_fleet),
            "VALOR_TOTAL_CONTRATO": money(contract_total),
            "SOMA_TOTAL_MENSAL_VEICULO": money(monthly_per_vehicle),
            "itens_proposta": [
                {
                    "nome": product,
                    "descricao": descriptions.get(product, product),
                    "preco": money(price),
                }
                for product, price in selected.items()
            ],
        }
        st.session_state.pj_results = {
            "monthly_per_vehicle": monthly_per_vehicle,
            "monthly_fleet": monthly_fleet,
            "contract_total": contract_total,
            "context": context,
        }
        db.upsert_proposal(
            {
                "tipo": "PJ",
                "empresa": company.strip(),
                "consultor": st.session_state.get("name", "N/A"),
                "valor_total": float(contract_total),
            }
        )
        db.add_log(
            st.session_state.get("username", "sistema"),
            "Simulou proposta PJ",
            {"empresa": company.strip(), "veiculos": vehicle_count, "valor_total": float(contract_total)},
        )
        st.success("Proposta calculada e registrada.")

result = st.session_state.get("pj_results")
if result:
    st.markdown("### Resultado")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Mensal por veículo", money(result["monthly_per_vehicle"]))
    metric_2.metric("Mensal da frota", money(result["monthly_fleet"]))
    metric_3.metric("Valor do contrato", money(result["contract_total"]))

    try:
        document_bytes = generate_proposal(result["context"])
        safe_company = "_".join(result["context"]["NOME_EMPRESA"].split())
        st.download_button(
            "Baixar proposta em DOCX",
            data=document_bytes,
            file_name=f"Proposta_{safe_company}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
    except Exception as exc:
        st.error(f"Não foi possível gerar o documento: {exc}")

if st.button("Limpar simulação"):
    st.session_state.pj_results = None
    st.rerun()
