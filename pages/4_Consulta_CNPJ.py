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
@st.cache_data(ttl=86400) # Cache de 1 dia para marcas
def get_fipe_marcas(tipo_veiculo):
    """Busca as marcas de veículos da API FIPE."""
    if not tipo_veiculo:
        return []
    url = f"https://brasilapi.com.br/api/fipe/marcas/v1/{tipo_veiculo}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        return []
    return []

@st.cache_data(ttl=3600) # Cache de 1 hora para modelos
def get_fipe_modelos(tipo_veiculo, codigo_marca):
    """Busca os modelos de uma marca específica."""
    if not codigo_marca:
        return []
    url = f"https://brasilapi.com.br/api/fipe/veiculos/v1/{tipo_veiculo}/{codigo_marca}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # A API pode retornar 'modelos' ou 'anos', verificamos ambos
            data = response.json()
            return data.get('modelos', data.get('anos', []))
    except requests.exceptions.RequestException:
        return []
    return []

@st.cache_data(ttl=3600) # Cache de 1 hora para preços
def get_fipe_preco(codigo_fipe):
    """Busca o preço de um veículo pelo código FIPE."""
    if not codigo_fipe:
        return None
    url = f"https://brasilapi.com.br/api/fipe/preco/v1/{codigo_fipe}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        return None
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
    cnpj_input = st.text_input("Digite o CNPJ (apenas números ou formatado):", key="cnpj_input")

    if st.button("Consultar CNPJ", use_container_width=True, type="primary"):
        if cnpj_input:
            with st.spinner("A consultar..."):
                dados_cnpj, erro = consultar_cnpj(cnpj_input)
            
            if erro:
                st.error(f"**Falha na consulta:** {erro}")
            elif dados_cnpj:
                st.success("**Consulta realizada com sucesso!**")
                st.header(dados_cnpj.get("razao_social", "N/A"))
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Nome Fantasia", dados_cnpj.get("nome_fantasia") or "N/A")
                col2.metric("Situação Cadastral", dados_cnpj.get("descricao_situacao_cadastral", "N/A"))
                col3.metric("Data de Abertura", dados_cnpj.get("data_inicio_atividade", "N/A"))
        else:
            st.warning("Por favor, digite um CNPJ para consultar.")

st.markdown("---")

# --- 6. NOVA SECÇÃO DE CONSULTA FIPE ---
with st.expander("🚗 Consulta Tabela FIPE", expanded=True):
    st.subheader("Consulte o valor de um veículo na Tabela FIPE")
    
    col_tipo, col_marca, col_modelo = st.columns(3)

    with col_tipo:
        tipo_veiculo = st.selectbox(
            "1. Tipo de Veículo",
            options=["carros", "motos", "caminhoes"],
            format_func=lambda x: x.capitalize(),
            key="fipe_tipo",
            index=None,
            placeholder="Selecione..."
        )
    
    if tipo_veiculo:
        marcas = get_fipe_marcas(tipo_veiculo)
        if marcas:
            # ***** CORREÇÃO PRINCIPAL AQUI *****
            # A API retorna a chave 'valor', não 'codigo'
            marcas_dict = {marca['nome']: marca['valor'] for marca in marcas}
            with col_marca:
                marca_selecionada = st.selectbox(
                    "2. Marca do Veículo",
                    options=list(marcas_dict.keys()),
                    key="fipe_marca",
                    index=None,
                    placeholder="Selecione..."
                )
            
            if marca_selecionada:
                codigo_marca = marcas_dict.get(marca_selecionada)
                modelos = get_fipe_modelos(tipo_veiculo, codigo_marca)

                if modelos:
                    modelos_dict = {modelo['nome']: modelo['codigo'] for modelo in modelos}
                    with col_modelo:
                        modelo_selecionado = st.selectbox(
                            "3. Modelo do Veículo",
                            options=list(modelos_dict.keys()),
                            key="fipe_modelo",
                            index=None,
                            placeholder="Selecione..."
                        )
                    
                    if st.button("Consultar Preço FIPE", use_container_width=True):
                        if modelo_selecionado:
                            codigo_fipe = modelos_dict.get(modelo_selecionado)
                            with st.spinner("A buscar o preço..."):
                                preco_info = get_fipe_preco(codigo_fipe)
                            
                            if preco_info and len(preco_info) > 0:
                                veiculo = preco_info[0]
                                st.subheader(f"{veiculo.get('marca')} {veiculo.get('modelo')}")
                                
                                p_col1, p_col2, p_col3 = st.columns(3)
                                p_col1.metric("Valor FIPE", veiculo.get('valor'))
                                p_col2.metric("Ano Modelo", veiculo.get('anoModelo'))
                                p_col3.metric("Combustível", veiculo.get('combustivel'))
                                
                                st.caption(f"Mês de Referência: {veiculo.get('mesReferencia').strip()} | Código FIPE: {veiculo.get('codigoFipe')}")
                            else:
                                st.error("Não foi possível obter o preço para o modelo selecionado.")
                        else:
                            st.warning("Por favor, selecione um modelo para consultar.")
