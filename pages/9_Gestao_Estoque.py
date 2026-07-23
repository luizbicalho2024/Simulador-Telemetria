from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Gestão de Estoque")
branding = apply_branding()
require_auth()
render_sidebar()
render_hero("Gestão de estoque", "Concilie o estoque registrado no sistema com a contagem física e identifique divergências.")


@st.cache_data(show_spinner=False)
def read_system_stock(file_bytes: bytes) -> pd.DataFrame:
    frame = pd.read_excel(io.BytesIO(file_bytes), header=11, engine="openpyxl")
    frame.rename(columns={"Nº Série": "Serial", "N° Série": "Serial"}, inplace=True)
    required = {"Serial", "Status", "Modelo"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no relatório do sistema: {', '.join(sorted(missing))}.")
    frame = frame.dropna(subset=["Serial"]).copy()
    frame["Serial"] = frame["Serial"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    frame = frame[frame["Serial"] != ""]
    return frame


@st.cache_data(show_spinner=False)
def read_physical_stock(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buffer = io.BytesIO(file_bytes)
    if filename.lower().endswith(".csv"):
        try:
            frame = pd.read_csv(buffer, sep=None, engine="python")
        except UnicodeDecodeError:
            buffer.seek(0)
            frame = pd.read_csv(buffer, sep=None, engine="python", encoding="latin-1")
    else:
        frame = pd.read_excel(buffer)
    if frame.empty:
        raise ValueError("A planilha de estoque físico está vazia.")
    serial_column = next((column for column in frame.columns if str(column).strip().lower() in {"serial", "nº série", "n° série", "numero de serie"}), frame.columns[0])
    result = frame[[serial_column]].rename(columns={serial_column: "Serial"}).copy()
    result["Serial"] = result["Serial"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    result = result[(result["Serial"] != "") & (result["Serial"].str.lower() != "nan")]
    return result.drop_duplicates("Serial")


@st.cache_data(show_spinner=False)
def to_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


system_col, physical_col = st.columns(2)
with system_col:
    st.markdown("#### Estoque do sistema")
    st.caption("Exporte o relatório e salve-o como .xlsx. O cabeçalho deve estar na linha 12.")
    system_file = st.file_uploader("Relatório do sistema", type=["xlsx"], key="system_stock")
with physical_col:
    st.markdown("#### Estoque físico")
    st.caption("A primeira coluna deve conter os números de série, ou possuir o cabeçalho Serial.")
    physical_file = st.file_uploader("Inventário físico", type=["xlsx", "csv"], key="physical_stock")

if system_file and physical_file:
    try:
        system_stock = read_system_stock(system_file.getvalue())
        physical_stock = read_physical_stock(physical_file.getvalue(), physical_file.name)

        reconciled = physical_stock.merge(system_stock[["Serial", "Status", "Modelo"]], on="Serial", how="left")
        reconciled["Status"] = reconciled["Status"].fillna("Não encontrado no sistema")
        reconciled["Modelo"] = reconciled["Modelo"].fillna("Não identificado")

        expected_in_stock = system_stock[~system_stock["Status"].astype(str).str.casefold().eq("indisponível")]
        missing_serials = set(expected_in_stock["Serial"]) - set(physical_stock["Serial"])
        missing_physical = expected_in_stock[expected_in_stock["Serial"].isin(missing_serials)].copy()
        unknown_system = reconciled[reconciled["Status"] == "Não encontrado no sistema"].copy()

        metrics = st.columns(4)
        metrics[0].metric("Contagem física", len(physical_stock))
        metrics[1].metric("Registros no sistema", len(system_stock))
        metrics[2].metric("Não cadastrados", len(unknown_system))
        metrics[3].metric("Faltando no físico", len(missing_physical))

        chart_col, model_col = st.columns(2)
        with chart_col:
            status_counts = reconciled["Status"].value_counts().rename_axis("Status").reset_index(name="Quantidade")
            fig_status = px.pie(status_counts, names="Status", values="Quantidade", hole=0.5, title="Distribuição por status")
            st.plotly_chart(fig_status, width="stretch")
        with model_col:
            model_counts = reconciled["Modelo"].value_counts().head(12).rename_axis("Modelo").reset_index(name="Quantidade")
            fig_models = px.bar(model_counts, x="Modelo", y="Quantidade", title="Modelos no estoque físico")
            fig_models.update_traces(marker_color=branding["primary_color"])
            st.plotly_chart(fig_models, width="stretch")

        tab_reconciliation, tab_unknown, tab_missing = st.tabs(["Conciliação", "Não cadastrados", "Faltando no físico"])
        with tab_reconciliation:
            st.dataframe(reconciled, width="stretch", hide_index=True)
        with tab_unknown:
            if unknown_system.empty:
                st.success("Todos os seriais físicos foram encontrados no sistema.")
            else:
                st.warning(f"{len(unknown_system)} serial(is) da contagem física não foram encontrados no sistema.")
                st.dataframe(unknown_system[["Serial"]], width="stretch", hide_index=True)
                st.download_button("Exportar não cadastrados", to_csv(unknown_system[["Serial"]]), "seriais_nao_cadastrados.csv", "text/csv")
        with tab_missing:
            if missing_physical.empty:
                st.success("Todos os equipamentos esperados foram localizados na contagem física.")
            else:
                visible = [column for column in ["Serial", "Status", "Modelo", "Última Transmissão"] if column in missing_physical.columns]
                st.error(f"{len(missing_physical)} equipamento(s) esperados não aparecem na contagem física.")
                st.dataframe(missing_physical[visible], width="stretch", hide_index=True)
                st.download_button("Exportar faltantes", to_csv(missing_physical[visible]), "equipamentos_faltantes.csv", "text/csv")

        signature = f"{system_file.name}:{len(system_file.getvalue())}:{physical_file.name}:{len(physical_file.getvalue())}"
        if st.session_state.get("stock_reconciliation_logged") != signature:
            db.add_log(
                st.session_state.get("username", "sistema"),
                "Executou conciliação de estoque",
                {"fisico": len(physical_stock), "sistema": len(system_stock), "nao_cadastrados": len(unknown_system), "faltantes": len(missing_physical)},
            )
            st.session_state.stock_reconciliation_logged = signature
    except Exception as exc:
        st.error(f"Não foi possível conciliar os arquivos: {exc}")
else:
    st.caption("Carregue os dois arquivos para iniciar a conciliação.")
