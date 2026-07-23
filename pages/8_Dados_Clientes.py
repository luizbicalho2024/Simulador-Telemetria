from __future__ import annotations

import io
import re

import pandas as pd
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Organizador de Dados de Clientes")
apply_branding()
require_auth()
render_sidebar()
render_hero("Organizador de dados de clientes", "Transforme o relatório exportado pelo sistema em uma base consolidada de clientes PF e PJ.")

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def is_valid_email(value: object) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    return bool(text and text.lower() not in {"e-mail", "email", "cpf/cnpj"} and EMAIL_RE.fullmatch(text))


@st.cache_data(show_spinner=False)
def process_spreadsheet(file_bytes: bytes) -> pd.DataFrame:
    frame = pd.read_excel(io.BytesIO(file_bytes), header=11)
    frame = frame.loc[:, ~frame.columns.astype(str).str.contains(r"^Unnamed", na=False)]
    frame.dropna(axis="rows", how="all", inplace=True)
    frame.columns = frame.columns.astype(str).str.strip().str.lower()
    frame.rename(
        columns={
            "razão social": "nome_cliente",
            "nome do cliente": "nome_cliente",
            "cnpj": "cpf_cnpj",
            "cpf/cnpj": "cpf_cnpj",
            "tipo cliente": "tipo_cliente",
            "tipo de cliente": "tipo_cliente",
            "tipo": "tipo_cliente",
            "telefone": "telefone",
            "fone": "telefone",
        },
        inplace=True,
    )

    required = {"nome_cliente", "cpf_cnpj", "tipo_cliente"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias não encontradas: {', '.join(sorted(missing))}.")

    frame["tipo_cliente"] = frame["tipo_cliente"].astype(str).str.strip()
    starts_client = frame["tipo_cliente"].str.contains(r"Jurídica|Jurídico|Física|Físico", case=False, na=False)
    if not starts_client.any():
        raise ValueError("Nenhum marcador de Pessoa Física ou Pessoa Jurídica foi encontrado na coluna de tipo.")

    frame["client_group_id"] = starts_client.cumsum()
    clients: list[dict] = []
    for _, group in frame[frame["client_group_id"] > 0].groupby("client_group_id"):
        if group.empty:
            continue
        main = group.iloc[0]
        type_text = str(main.get("tipo_cliente", "")).lower()
        client = {
            "Nome do Cliente": main.get("nome_cliente"),
            "CPF/CNPJ": main.get("cpf_cnpj"),
            "Tipo Cliente": "Pessoa Física" if "fís" in type_text or "fis" in type_text else "Pessoa Jurídica",
            "Telefone": main.get("telefone", ""),
        }
        emails: list[str] = []
        for _, row in group.iloc[1:].iterrows():
            candidate = row.get("cpf_cnpj")
            if is_valid_email(candidate):
                normalized = str(candidate).strip().lower()
                if normalized not in emails:
                    emails.append(normalized)
        for index, email in enumerate(emails, start=1):
            client[f"E-mail Usuário {index}"] = email
        clients.append(client)

    if not clients:
        raise ValueError("Nenhum cliente válido foi identificado no arquivo.")

    result = pd.DataFrame(clients)
    base_columns = ["Nome do Cliente", "CPF/CNPJ", "Tipo Cliente", "Telefone"]
    email_columns = sorted(
        [column for column in result.columns if column.startswith("E-mail Usuário")],
        key=lambda column: int(column.rsplit(" ", 1)[-1]),
    )
    return result[base_columns + email_columns]


@st.cache_data(show_spinner=False)
def to_excel(frame: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        frame.to_excel(writer, index=False, sheet_name="Clientes_Organizados")
        worksheet = writer.sheets["Clientes_Organizados"]
        for index, column in enumerate(frame.columns):
            width = min(max(len(str(column)) + 2, frame[column].astype(str).map(len).max() + 2), 50)
            worksheet.set_column(index, index, width)
    return output.getvalue()


st.info("O arquivo deve possuir o cabeçalho da tabela na linha 12, conforme o relatório original do sistema.")
uploaded = st.file_uploader("Planilha de clientes", type=["xlsx"], key="customer_data_upload")

if uploaded:
    try:
        file_bytes = uploaded.getvalue()
        result = process_spreadsheet(file_bytes)
        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Clientes processados", len(result))
        metric_2.metric("Pessoas jurídicas", int((result["Tipo Cliente"] == "Pessoa Jurídica").sum()))
        metric_3.metric("Pessoas físicas", int((result["Tipo Cliente"] == "Pessoa Física").sum()))
        st.dataframe(result.fillna(""), width="stretch", hide_index=True)

        signature = f"{uploaded.name}:{len(file_bytes)}"
        if st.session_state.get("customer_file_logged") != signature:
            db.add_log(
                st.session_state.get("username", "sistema"),
                "Processou planilha de clientes",
                {"arquivo": uploaded.name, "clientes": len(result)},
            )
            st.session_state.customer_file_logged = signature

        st.download_button(
            "Baixar planilha organizada",
            data=to_excel(result),
            file_name="relatorio_clientes_organizados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    except Exception as exc:
        st.error(f"Não foi possível processar a planilha: {exc}")
else:
    st.caption("Carregue um arquivo para iniciar o processamento.")
