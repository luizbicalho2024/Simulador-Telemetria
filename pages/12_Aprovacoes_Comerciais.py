from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.proposal_documents import generate_pj_proposal
from app_core.ui import apply_branding, configure_page, money, render_hero, render_sidebar

configure_page("Aprovações Comerciais")
apply_branding()
require_auth()
render_sidebar()
render_hero(
    "Aprovações comerciais",
    "Acompanhe descontos, isenções de instalação e decisões do Head Comercial.",
)

ROLE = str(st.session_state.get("role") or "user")
USERNAME = str(st.session_state.get("username") or "").strip().lower()
USER_NAME = str(st.session_state.get("name") or USERNAME or "Usuário")
IS_APPROVER = ROLE in {"admin", "head_comercial"}

STATUS_LABELS = {
    "approved": "Aprovada",
    "pending_approval": "Aguardando aprovação",
    "rejected": "Rejeitada",
}


def status_label(value: object) -> str:
    return STATUS_LABELS.get(str(value or ""), str(value or "Sem status"))


def proposal_label(proposal: dict) -> str:
    created = proposal.get("data_geracao")
    created_label = created.strftime("%d/%m/%Y %H:%M") if isinstance(created, datetime) else "Sem data"
    return (
        f"{proposal.get('proposal_code', str(proposal.get('_id', '')))} — "
        f"{proposal.get('empresa', 'Sem empresa')} — {created_label}"
    )


def proposal_table(proposals: list[dict]) -> pd.DataFrame:
    rows = []
    for proposal in proposals:
        rows.append(
            {
                "Código": proposal.get("proposal_code", str(proposal.get("_id", ""))),
                "Data": proposal.get("data_geracao"),
                "Empresa": proposal.get("empresa", ""),
                "Consultor": proposal.get("consultor", ""),
                "Veículos": proposal.get("quantidade_veiculos", 0),
                "Receita": proposal.get("receita_total", proposal.get("valor_total", 0)),
                "Margem": proposal.get("margem_total", 0),
                "Margem (%)": proposal.get("margem_percentual", 0),
                "Instalação": proposal.get("instalacao", ""),
                "Status": status_label(proposal.get("status")),
            }
        )
    return pd.DataFrame(rows)


def render_proposal_details(proposal: dict) -> None:
    st.markdown(f"### {proposal.get('proposal_code', 'Proposta PJ')}")
    detail_1, detail_2, detail_3, detail_4 = st.columns(4)
    detail_1.metric("Empresa", proposal.get("empresa", ""))
    detail_2.metric("Consultor", proposal.get("consultor", ""))
    detail_3.metric("Veículos", int(proposal.get("quantidade_veiculos", 0) or 0))
    detail_4.metric("Status", status_label(proposal.get("status")))

    financial_1, financial_2, financial_3, financial_4 = st.columns(4)
    financial_1.metric("Receita total", money(proposal.get("receita_total", proposal.get("valor_total", 0))))
    financial_2.metric("Custo total", money(proposal.get("custo_total", 0)))
    financial_3.metric("Margem total", money(proposal.get("margem_total", 0)))
    financial_4.metric("Margem (%)", f"{float(proposal.get('margem_percentual', 0) or 0):.2f}%")

    st.caption(
        f"Prazo: {proposal.get('prazo_contrato', '')} · "
        f"Instalação: {proposal.get('instalacao', '')} · "
        f"Responsável no cliente: {proposal.get('responsavel', '')}"
    )

    reasons = proposal.get("approval_reasons") or []
    if reasons:
        st.warning("Motivos que exigiram aprovação: " + "; ".join(map(str, reasons)))

    items = proposal.get("itens") or []
    if items:
        item_rows = []
        for item in items:
            item_rows.append(
                {
                    "Produto": item.get("produto", ""),
                    "Condição": item.get("condicao", ""),
                    "Preço padrão": item.get("preco_padrao", 0),
                    "Preço aplicado": item.get("preco_mensal", 0),
                    "Custo mensal": item.get("custo_mensal", 0),
                    "Margem unitária": item.get("margem_unitaria", 0),
                    "Margem (%)": item.get("margem_percentual", 0),
                    "Preço instalação": item.get("preco_instalacao", 0),
                    "Custo instalação": item.get("custo_instalacao", 0),
                }
            )
        st.dataframe(
            pd.DataFrame(item_rows),
            width="stretch",
            hide_index=True,
            column_config={
                "Preço padrão": st.column_config.NumberColumn("Preço padrão", format="R$ %.2f"),
                "Preço aplicado": st.column_config.NumberColumn("Preço aplicado", format="R$ %.2f"),
                "Custo mensal": st.column_config.NumberColumn("Custo mensal", format="R$ %.2f"),
                "Margem unitária": st.column_config.NumberColumn("Margem unitária", format="R$ %.2f"),
                "Margem (%)": st.column_config.NumberColumn("Margem (%)", format="%.2f%%"),
                "Preço instalação": st.column_config.NumberColumn("Preço instalação", format="R$ %.2f"),
                "Custo instalação": st.column_config.NumberColumn("Custo instalação", format="R$ %.2f"),
            },
        )

    if proposal.get("status") == "rejected":
        st.error(
            "Rejeitada por "
            f"{proposal.get('decided_by_name', proposal.get('decided_by_username', 'Head Comercial'))}: "
            f"{proposal.get('decision_reason', 'Motivo não informado')}"
        )
    elif proposal.get("status") == "approved" and proposal.get("approved_by_name"):
        st.success(f"Aprovada por {proposal.get('approved_by_name')}.")

    if proposal.get("status") == "approved" and proposal.get("document_context"):
        try:
            document = generate_pj_proposal(proposal["document_context"])
            company = "_".join(str(proposal.get("empresa") or "Cliente").split())
            code = str(proposal.get("proposal_code") or "PJ")
            st.download_button(
                "Baixar proposta aprovada em DOCX",
                data=document,
                file_name=f"{code}_{company}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                key=f"download_{proposal.get('_id')}",
            )
        except Exception as exc:
            st.error(f"Não foi possível gerar o documento aprovado: {exc}")


if IS_APPROVER:
    pending = db.get_commercial_proposals(status="pending_approval", limit=2_000)
    history = db.get_commercial_proposals(status=None, limit=5_000)

    summary_1, summary_2, summary_3 = st.columns(3)
    summary_1.metric("Pendentes", len(pending))
    summary_2.metric(
        "Valor pendente",
        money(sum(float(item.get("receita_total", item.get("valor_total", 0)) or 0) for item in pending)),
    )
    summary_3.metric(
        "Margem média pendente",
        (
            f"{sum(float(item.get('margem_percentual', 0) or 0) for item in pending) / len(pending):.2f}%"
            if pending
            else "0,00%"
        ),
    )

    pending_tab, history_tab = st.tabs(["Fila de aprovação", "Histórico"])

    with pending_tab:
        if not pending:
            st.success("Não existem propostas aguardando aprovação.")
        else:
            st.dataframe(
                proposal_table(pending),
                width="stretch",
                hide_index=True,
                column_config={
                    "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                    "Receita": st.column_config.NumberColumn("Receita", format="R$ %.2f"),
                    "Margem": st.column_config.NumberColumn("Margem", format="R$ %.2f"),
                    "Margem (%)": st.column_config.NumberColumn("Margem (%)", format="%.2f%%"),
                },
            )
            pending_map = {proposal_label(item): item for item in pending}
            selected_label = st.selectbox(
                "Proposta para decisão",
                list(pending_map),
                key="approval_pending_select",
            )
            selected = pending_map[selected_label]
            render_proposal_details(selected)

            rejection_reason = st.text_area(
                "Justificativa da rejeição",
                key=f"approval_reason_{selected.get('_id')}",
                help="Obrigatória somente para rejeitar.",
            )
            approve_col, reject_col = st.columns(2)
            if approve_col.button(
                "Aprovar proposta",
                type="primary",
                width="stretch",
                key=f"approve_{selected.get('_id')}",
            ):
                if db.decide_commercial_proposal(
                    str(selected["_id"]),
                    decision="approved",
                    decided_by_username=USERNAME,
                    decided_by_name=USER_NAME,
                ):
                    db.add_log(
                        USERNAME,
                        "Aprovou proposta PJ",
                        {"proposta_id": str(selected["_id"]), "empresa": selected.get("empresa")},
                    )
                    st.success("Proposta aprovada.")
                    st.rerun()
                else:
                    st.error("A proposta não pôde ser aprovada. Ela pode já ter sido decidida.")

            if reject_col.button(
                "Rejeitar proposta",
                width="stretch",
                key=f"reject_{selected.get('_id')}",
                disabled=not rejection_reason.strip(),
            ):
                if db.decide_commercial_proposal(
                    str(selected["_id"]),
                    decision="rejected",
                    decided_by_username=USERNAME,
                    decided_by_name=USER_NAME,
                    reason=rejection_reason.strip(),
                ):
                    db.add_log(
                        USERNAME,
                        "Rejeitou proposta PJ",
                        {
                            "proposta_id": str(selected["_id"]),
                            "empresa": selected.get("empresa"),
                            "motivo": rejection_reason.strip(),
                        },
                    )
                    st.warning("Proposta rejeitada.")
                    st.rerun()
                else:
                    st.error("A proposta não pôde ser rejeitada. Ela pode já ter sido decidida.")

    with history_tab:
        if history:
            status_filter = st.multiselect(
                "Status",
                list(STATUS_LABELS),
                default=list(STATUS_LABELS),
                format_func=lambda value: STATUS_LABELS[value],
                key="approval_history_status",
            )
            filtered = [item for item in history if item.get("status") in status_filter]
            st.dataframe(
                proposal_table(filtered),
                width="stretch",
                hide_index=True,
                column_config={
                    "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                    "Receita": st.column_config.NumberColumn("Receita", format="R$ %.2f"),
                    "Margem": st.column_config.NumberColumn("Margem", format="R$ %.2f"),
                    "Margem (%)": st.column_config.NumberColumn("Margem (%)", format="%.2f%%"),
                },
            )
            if filtered:
                history_map = {proposal_label(item): item for item in filtered}
                history_label = st.selectbox(
                    "Visualizar proposta",
                    list(history_map),
                    key="approval_history_select",
                )
                render_proposal_details(history_map[history_label])
        else:
            st.info("Ainda não há propostas no histórico comercial.")
else:
    own_proposals = db.get_commercial_proposals(
        submitted_by_username=USERNAME,
        status=None,
        limit=2_000,
    )
    if not own_proposals:
        st.info("Você ainda não registrou propostas PJ com o novo fluxo comercial.")
    else:
        pending_count = sum(1 for proposal in own_proposals if proposal.get("status") == "pending_approval")
        approved_count = sum(1 for proposal in own_proposals if proposal.get("status") == "approved")
        rejected_count = sum(1 for proposal in own_proposals if proposal.get("status") == "rejected")
        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Aguardando aprovação", pending_count)
        metric_2.metric("Aprovadas", approved_count)
        metric_3.metric("Rejeitadas", rejected_count)

        st.dataframe(
            proposal_table(own_proposals),
            width="stretch",
            hide_index=True,
            column_config={
                "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                "Receita": st.column_config.NumberColumn("Receita", format="R$ %.2f"),
                "Margem": st.column_config.NumberColumn("Margem", format="R$ %.2f"),
                "Margem (%)": st.column_config.NumberColumn("Margem (%)", format="%.2f%%"),
            },
        )
        own_map = {proposal_label(item): item for item in own_proposals}
        own_label = st.selectbox("Visualizar proposta", list(own_map), key="own_proposal_select")
        render_proposal_details(own_map[own_label])
