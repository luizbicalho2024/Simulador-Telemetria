from __future__ import annotations

import re
from typing import Any

import pandas as pd
import requests
import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Consultas Gerais")
apply_branding()
require_auth()
render_sidebar()
render_hero("Consultas gerais", "Consulte CNPJ e valores da Tabela FIPE com cache e armazenamento local no MongoDB.")

HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "Simulador-Telemetria/2.0"})


@st.cache_data(ttl=3_600, show_spinner=False)
def query_cnpj(cnpj: str) -> tuple[dict[str, Any] | None, str | None]:
    normalized = re.sub(r"\D", "", cnpj)
    if len(normalized) != 14:
        return None, "O CNPJ deve possuir 14 dígitos."
    try:
        response = HTTP.get(f"https://brasilapi.com.br/api/cnpj/v1/{normalized}", timeout=15)
        if response.status_code == 200:
            return response.json(), None
        if response.status_code == 404:
            return None, "CNPJ não encontrado."
        return None, f"A consulta retornou o código HTTP {response.status_code}."
    except requests.RequestException as exc:
        return None, f"Falha de comunicação com a BrasilAPI: {exc}"


@st.cache_data(ttl=86_400, show_spinner=False)
def fipe_brands(vehicle_type: str) -> list[dict]:
    try:
        response = HTTP.get(f"https://parallelum.com.br/fipe/api/v1/{vehicle_type}/marcas", timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


@st.cache_data(ttl=21_600, show_spinner=False)
def fipe_models(vehicle_type: str, brand_code: str) -> list[dict]:
    try:
        response = HTTP.get(
            f"https://parallelum.com.br/fipe/api/v1/{vehicle_type}/marcas/{brand_code}/modelos",
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("modelos", [])
    except requests.RequestException:
        return []


@st.cache_data(ttl=21_600, show_spinner=False)
def fipe_years(vehicle_type: str, brand_code: str, model_code: str) -> list[dict]:
    try:
        response = HTTP.get(
            f"https://parallelum.com.br/fipe/api/v1/{vehicle_type}/marcas/{brand_code}/modelos/{model_code}/anos",
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


@st.cache_data(ttl=21_600, show_spinner=False)
def fipe_price(vehicle_type: str, brand_code: str, model_code: str, year_code: str) -> dict | None:
    try:
        response = HTTP.get(
            f"https://parallelum.com.br/fipe/api/v1/{vehicle_type}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}",
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def display_fipe(records: list[dict]) -> None:
    if not records:
        st.info("Nenhum registro encontrado.")
        return
    frame = pd.DataFrame(records)
    aliases = {
        "Valor": "valor",
        "Marca": "marca",
        "Modelo": "modelo",
        "AnoModelo": "anoModelo",
        "Combustivel": "combustivel",
        "CodigoFipe": "codigoFipe",
        "MesReferencia": "mesReferencia",
    }
    frame.rename(columns=aliases, inplace=True)
    columns = [column for column in ["marca", "modelo", "anoModelo", "combustivel", "valor", "codigoFipe", "mesReferencia"] if column in frame.columns]
    st.dataframe(frame[columns], width="stretch", hide_index=True)


tab_fipe, tab_cnpj = st.tabs(["Tabela FIPE", "CNPJ"])

with tab_fipe:
    st.markdown("#### Pesquisa local")
    local_col, local_action = st.columns([4, 1])
    term = local_col.text_input("Modelo", placeholder="Ex.: Hilux, Corolla, CG 160")
    search_local = local_action.button("Pesquisar", width="stretch")
    if search_local:
        if len(term.strip()) < 2:
            st.warning("Informe pelo menos dois caracteres.")
        else:
            results = db.search_vehicle_in_db(term)
            st.caption(f"{len(results)} registro(s) encontrado(s) no banco local.")
            display_fipe(results)

    st.markdown("---")
    st.markdown("#### Consulta guiada e sincronização")
    type_col, brand_col, model_col = st.columns(3)
    vehicle_type = type_col.selectbox(
        "Tipo de veículo",
        ["carros", "motos", "caminhoes"],
        format_func=lambda value: {"carros": "Carros", "motos": "Motos", "caminhoes": "Caminhões"}[value],
        index=None,
        placeholder="Selecione",
    )

    selected_brand_code = None
    selected_model_code = None
    selected_model_name = None
    if vehicle_type:
        brands = fipe_brands(vehicle_type)
        brand_map = {brand["nome"]: str(brand["codigo"]) for brand in brands}
        selected_brand = brand_col.selectbox("Marca", list(brand_map), index=None, placeholder="Selecione")
        if selected_brand:
            selected_brand_code = brand_map[selected_brand]
            models = fipe_models(vehicle_type, selected_brand_code)
            model_map = {model["nome"]: str(model["codigo"]) for model in models}
            selected_model_name = model_col.selectbox("Modelo", list(model_map), index=None, placeholder="Selecione")
            if selected_model_name:
                selected_model_code = model_map[selected_model_name]

    if selected_model_code and st.button("Consultar todas as versões e salvar", type="primary", width="stretch"):
        years = fipe_years(vehicle_type, selected_brand_code, selected_model_code)
        if not years:
            st.error("A API não retornou versões para o modelo selecionado.")
        else:
            progress = st.progress(0, text="Consultando versões da FIPE...")
            records: list[dict] = []
            for index, year in enumerate(years, start=1):
                record = fipe_price(vehicle_type, selected_brand_code, selected_model_code, str(year["codigo"]))
                if record:
                    records.append(record)
                progress.progress(index / len(years), text=f"Consultando versão {index} de {len(years)}")
            progress.empty()
            if records and db.save_fipe_data(records):
                db.add_log(
                    st.session_state.get("username", "sistema"),
                    "Sincronizou modelo FIPE",
                    {"modelo": selected_model_name, "registros": len(records)},
                )
                st.success(f"{len(records)} versão(ões) consultada(s) e armazenada(s).")
                display_fipe(records)
            elif records:
                st.error("Os dados foram consultados, mas não puderam ser salvos no MongoDB.")
            else:
                st.error("Nenhuma versão retornou preço válido.")

with tab_cnpj:
    st.markdown("#### Consulta cadastral")
    cnpj_col, cnpj_action = st.columns([4, 1])
    cnpj = cnpj_col.text_input("CNPJ", placeholder="00.000.000/0000-00")
    query_button = cnpj_action.button("Consultar", width="stretch")

    if query_button:
        data, error = query_cnpj(cnpj)
        if error:
            st.error(error)
        elif data:
            st.markdown(f"### {data.get('razao_social', 'Razão social não informada')}")
            st.caption(data.get("nome_fantasia") or "Nome fantasia não informado")
            metric_1, metric_2, metric_3 = st.columns(3)
            metric_1.metric("Situação", data.get("descricao_situacao_cadastral", "N/A"))
            metric_2.metric("Abertura", data.get("data_inicio_atividade", "N/A"))
            metric_3.metric("Porte", data.get("descricao_porte", "N/A"))

            address_col, activity_col = st.columns(2)
            with address_col:
                st.markdown("#### Endereço e contato")
                st.write(f"{data.get('logradouro', '')}, {data.get('numero', '')}")
                st.write(f"{data.get('bairro', '')} — {data.get('municipio', '')}/{data.get('uf', '')}")
                st.write(f"CEP: {data.get('cep', '')}")
                st.write(f"Telefone: {data.get('ddd_telefone_1') or 'Não informado'}")
            with activity_col:
                st.markdown("#### Atividade empresarial")
                st.write(f"CNAE principal: {data.get('cnae_fiscal', '')}")
                st.write(data.get("cnae_fiscal_descricao", ""))
                st.write(f"Natureza jurídica: {data.get('natureza_juridica', '')}")
