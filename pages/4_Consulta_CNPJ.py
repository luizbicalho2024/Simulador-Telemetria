# pages/4_Consulta_CNPJ.py
import streamlit as st
import pandas as pd
import requests
import re
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Consultas Gerais",
    page_icon="🔍"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES AUXILIARES (CNPJ) ---
@st.cache_data(ttl=3600)
def consultar_cnpj(cnpj: str):
    """Consulta um CNPJ na BrasilAPI."""
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_limpo) != 14:
        return None, "O CNPJ deve ter 14 dígitos."
    
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            return None, "CNPJ não encontrado na base de dados da Receita Federal."
        else:
            return None, f"Erro na API. Código: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Erro de conexão: {e}"

# --- 3. FUNÇÕES AUXILIARES (FIPE) ---
BASE_FIPE_URL = "https://parallelum.com.br/fipe/api/v1"

@st.cache_data(ttl=86400) # Cache de 1 dia
def get_fipe_marcas(tipo_veiculo):
    """Busca as marcas de veículos da API FIPE."""
    if not tipo_veiculo: return []
    url = f"{BASE_FIPE_URL}/{tipo_veiculo}/marcas"
    try:
        response = requests.get(url)
        if response.status_code == 200: return response.json()
    except: return []
    return []

@st.cache_data(ttl=3600)
def get_fipe_modelos(tipo_veiculo, codigo_marca):
    """Busca os modelos de uma marca específica."""
    if not codigo_marca: return []
    url = f"{BASE_FIPE_URL}/{tipo_veiculo}/marcas/{codigo_marca}/modelos"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('modelos', [])
    except: return []
    return []

@st.cache_data(ttl=3600)
def get_fipe_anos(tipo_veiculo, codigo_marca, codigo_modelo):
    """Busca os anos de um modelo específico."""
    if not codigo_modelo: return []
    url = f"{BASE_FIPE_URL}/{tipo_veiculo}/marcas/{codigo_marca}/modelos/{codigo_modelo}/anos"
    try:
        response = requests.get(url)
        if response.status_code == 200: return response.json()
    except: return []
    return []

@st.cache_data(ttl=3600)
def get_fipe_preco(tipo_veiculo, codigo_marca, codigo_modelo, codigo_ano):
    """Busca o preço final do veículo."""
    if not codigo_ano: return None
    url = f"{BASE_FIPE_URL}/{tipo_veiculo}/marcas/{codigo_marca}/modelos/{codigo_modelo}/anos/{codigo_ano}"
    try:
        response = requests.get(url)
        if response.status_code == 200: return response.json()
    except: return None
    return None

# --- 4. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔍 Consultas Gerais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 5. SECÇÃO DE CONSULTA DE CNPJ ---
with st.expander("🏢 Consulta de CNPJ", expanded=True):
    # ... (código da consulta CNPJ como na última versão) ...

st.markdown("---")

# --- 6. SECÇÃO DE CONSULTA FIPE (REFATORADA) ---
with st.expander("🚗 Consulta Tabela FIPE", expanded=True):
    st.subheader("Encontre o valor de um veículo na Tabela FIPE")
    
    col1, col2, col3, col4 = st.columns(4)

    # Passo 1: Selecionar o tipo de veículo
    tipo_veiculo = col1.selectbox(
        "1. Tipo", ["carros", "motos", "caminhoes"],
        format_func=str.capitalize, index=None, placeholder="Selecione..."
    )

    # Passo 2: Selecionar a marca
    if tipo_veiculo:
        marcas = get_fipe_marcas(tipo_veiculo)
        marcas_dict = {marca['nome']: marca['codigo'] for marca in marcas}
        marca_nome = col2.selectbox(
            "2. Marca", list(marcas_dict.keys()),
            index=None, placeholder="Selecione..."
        )
        
        # Passo 3: Selecionar o modelo
        if marca_nome:
            codigo_marca = marcas_dict[marca_nome]
            modelos = get_fipe_modelos(tipo_veiculo, codigo_marca)
            modelos_dict = {modelo['nome']: modelo['codigo'] for modelo in modelos}
            modelo_nome = col3.selectbox(
                "3. Modelo", list(modelos_dict.keys()),
                index=None, placeholder="Selecione..."
            )

            # Passo 4: Selecionar o ano
            if modelo_nome:
                codigo_modelo = modelos_dict[modelo_nome]
                anos = get_fipe_anos(tipo_veiculo, codigo_marca, codigo_modelo)
                anos_dict = {ano['nome']: ano['codigo'] for ano in anos}
                ano_nome = col4.selectbox(
                    "4. Ano", list(anos_dict.keys()),
                    index=None, placeholder="Selecione..."
                )
                
                # Exibição do resultado
                if ano_nome:
                    codigo_ano = anos_dict[ano_nome]
                    with st.spinner("A buscar o preço..."):
                        veiculo_info = get_fipe_preco(tipo_veiculo, codigo_marca, codigo_modelo, codigo_ano)
                    
                    st.markdown("---")
                    if veiculo_info:
                        st.subheader(f"Resultado da Consulta FIPE:")
                        st.title(veiculo_info.get('Valor'))
                        
                        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                        r_col1.metric("Marca", veiculo_info.get('Marca'))
                        r_col2.metric("Modelo", veiculo_info.get('Modelo'))
                        r_col3.metric("Ano", str(veiculo_info.get('AnoModelo')))
                        r_col4.metric("Combustível", veiculo_info.get('Combustivel'))
                        
                        st.caption(f"Mês de Referência: {veiculo_info.get('MesReferencia')} | Código FIPE: {veiculo_info.get('CodigoFipe')}")
                    else:
                        st.error("Não foi possível obter o preço para o veículo selecionado.")
