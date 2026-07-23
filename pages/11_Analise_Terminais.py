from __future__ import annotations

import io
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Análise de Terminais")
apply_branding()
require_auth()
render_sidebar()
render_hero("Análise de terminais", "Identifique equipamentos sem transmissão recente e gere uma comunicação pronta para o cliente.")


@st.cache_data(show_spinner=False)
def process_terminal_report(file_bytes: bytes, stale_days: int) -> tuple[str, pd.DataFrame]:
    source = io.BytesIO(file_bytes)
    client_frame = pd.read_excel(source, header=None, skiprows=8, nrows=1, engine="openpyxl")
    client_name = "Cliente não identificado"
    if not client_frame.empty and len(client_frame.columns) > 4:
        raw_name = client_frame.iloc[0, 4]
        if pd.notna(raw_name):
            client_name = str(raw_name).strip()

    source.seek(0)
    terminals = pd.read_excel(source, header=11, engine="openpyxl")
    terminals.rename(
        columns={
            "Última Transmissão": "Data Transmissão",
            "Rastreador Modelo": "Modelo",
        },
        inplace=True,
    )
    required = {"Terminal", "Placa", "Rastreador", "Modelo", "Data Transmissão"}
    missing = required - set(terminals.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {', '.join(sorted(missing))}.")

    terminals = terminals.dropna(subset=["Terminal"]).copy()
    terminals["Data Transmissão"] = pd.to_datetime(terminals["Data Transmissão"], errors="coerce", dayfirst=True)
    terminals = terminals.dropna(subset=["Data Transmissão"])
    limit = datetime.now() - timedelta(days=stale_days)
    terminals["Status"] = terminals["Data Transmissão"].apply(lambda value: "Atualizado" if value >= limit else "Desatualizado")
    terminals["Dias sem transmitir"] = (pd.Timestamp.now() - terminals["Data Transmissão"]).dt.days.clip(lower=0)
    return client_name, terminals


threshold_col, upload_col = st.columns([1, 3])
stale_days = threshold_col.number_input("Limite sem transmissão (dias)", min_value=1, max_value=180, value=10, step=1)
uploaded = upload_col.file_uploader("Relatório lista_de_terminais.xlsx", type=["xlsx"])

if uploaded:
    try:
        file_bytes = uploaded.getvalue()
        client_name, analysis = process_terminal_report(file_bytes, int(stale_days))
        updated = analysis[analysis["Status"] == "Atualizado"]
        stale = analysis[analysis["Status"] == "Desatualizado"].sort_values("Dias sem transmitir", ascending=False)

        st.markdown(f"### Cliente: {client_name}")
        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Terminais analisados", len(analysis))
        metric_2.metric("Atualizados", len(updated))
        metric_3.metric("Desatualizados", len(stale))

        tab_stale, tab_all, tab_message = st.tabs(["Desatualizados", "Todos os terminais", "Comunicação ao cliente"])
        with tab_stale:
            if stale.empty:
                st.success("Todos os terminais transmitiram dentro do período definido.")
            else:
                st.warning(f"{len(stale)} terminal(is) precisam de verificação.")
                st.dataframe(
                    stale[["Terminal", "Placa", "Rastreador", "Modelo", "Data Transmissão", "Dias sem transmitir"]],
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Data Transmissão": st.column_config.DatetimeColumn("Última transmissão", format="DD/MM/YYYY HH:mm:ss"),
                        "Dias sem transmitir": st.column_config.NumberColumn("Dias sem transmitir", format="%d"),
                    },
                )
        with tab_all:
            st.dataframe(
                analysis,
                width="stretch",
                hide_index=True,
                column_config={"Data Transmissão": st.column_config.DatetimeColumn("Última transmissão", format="DD/MM/YYYY HH:mm:ss")},
            )
        with tab_message:
            if stale.empty:
                st.info("Não há terminais desatualizados para comunicar.")
            else:
                vehicle_lines = "\n".join(
                    f"- Placa {row['Placa']} — última comunicação em {row['Data Transmissão'].strftime('%d/%m/%Y às %H:%M')}"
                    for _, row in stale.iterrows()
                )
                subject = "Verificação necessária no sistema de rastreamento"
                body = f"""Prezado(a) cliente,

Identificamos ausência de comunicação recente nos seguintes veículos:

{vehicle_lines}

A falta de transmissão impede o acompanhamento em tempo real. Caso os veículos estejam em operação, pedimos que seja agendada uma verificação técnica para diagnóstico e restabelecimento do serviço.

Canais de atendimento:
- WhatsApp: (69) 9 9322-9855
- Capitais: 4020-1724
- Outras localidades: 0800 025 8871
- Suporte: contato@rovemabank.com.br

Atenciosamente,
Equipe de Monitoramento"""
                st.text_input("Assunto", value=subject)
                st.text_area("Mensagem", value=body, height=360)

        signature = f"{uploaded.name}:{len(file_bytes)}:{stale_days}"
        if st.session_state.get("terminal_analysis_logged") != signature:
            db.add_log(
                st.session_state.get("username", "sistema"),
                "Analisou terminais",
                {"cliente": client_name, "total": len(analysis), "desatualizados": len(stale), "limite_dias": stale_days},
            )
            st.session_state.terminal_analysis_logged = signature
    except Exception as exc:
        st.error(f"Não foi possível processar o relatório: {exc}")
else:
    st.caption("Carregue o relatório para iniciar a análise.")
