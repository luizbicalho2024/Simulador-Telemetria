# pages/4_Consultas_Gerais.py (Substitua o conteúdo de pages/4_Consulta_CNPJ.py)
import streamlit as st
import pandas as pd
import requests
import re
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Consultas Gerais", page_icon="🔍")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES AUXILIARES ---

# Função de CNPJ (mantida)
@st.cache_data(ttl=3600)
def consultar_cnpj(cnpj: str):
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_limpo) != 14: return None, "O CNPJ deve ter 14 dígitos."
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200: return response.json(), None
        elif response.status_code == 404: return None, "CNPJ não encontrado."
        else: return None, f"Erro na API (Código: {response.status_code})."
    except requests.exceptions.RequestException as e: return None, f"Erro de conexão: {e}"

# --- FUNÇÕES UNIFICADAS E CORRIGIDAS DA API FIPE (USANDO APENAS PARALLELUM) ---
@st.cache_data(ttl=86400)
def get_fipe_marcas(tipo_veiculo):
    if not tipo_veiculo: return []
    url = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas"
    try:
        r = requests.get(url, timeout=10)
        # A API Parallelum retorna a chave 'codigo' como string.
        return r.json() if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def get_fipe_modelos_por_marca(tipo_veiculo, codigo_marca):
    if not codigo_marca: return []
    url = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas/{codigo_marca}/modelos"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get('modelos', []) if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def get_fipe_precos_por_modelo(tipo_veiculo, codigo_marca, codigo_modelo):
    if not codigo_modelo: return []
    url = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas/{codigo_marca}/modelos/{codigo_modelo}/anos"
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

# --- FUNÇÕES DE VISUALIZAÇÃO ---
def exibir_resultados_fipe(resultados):
    st.subheader("Resultados da Consulta")
    if not resultados:
        st.warning("Nenhum resultado encontrado."); return

    df = pd.DataFrame(resultados)
    df.rename(columns={
        'Valor': 'valor', 'Marca': 'marca', 'Modelo': 'modelo', 'AnoModelo': 'anoModelo',
        'Combustivel': 'combustivel', 'CodigoFipe': 'codigoFipe', 'MesReferencia': 'mesReferencia'
    }, inplace=True, errors='ignore')
    
    cols_to_show = ['marca', 'modelo', 'anoModelo', 'combustivel', 'valor', 'codigoFipe', 'mesReferencia']
    df_display = df[[col for col in cols_to_show if col in df.columns]]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

def exibir_dados_cnpj(data):
    st.subheader(f"🏢 {data.get('razao_social', 'N/A')}")
    st.caption(f"**Nome Fantasia:** {data.get('nome_fantasia') or 'Não informado'}")
    
    col1, col2 = st.columns(2)
    col1.metric("Situação Cadastral", data.get('descricao_situacao_cadastral', 'N/A'))
    col2.metric("Data de Abertura", data.get('data_inicio_atividade', 'N/A'))
    
    with st.expander("Endereço e Contato"):
        st.write(f"**Logradouro:** {data.get('logradouro', '')}, {data.get('numero', '')}")
        st.write(f"**Bairro:** {data.get('bairro', '')}")
        st.write(f"**Cidade/UF:** {data.get('municipio', '')} - {data.get('uf', '')}")
        st.write(f"**CEP:** {data.get('cep', '')}")
        st.write(f"**Telefone:** {data.get('ddd_telefone_1') or 'Não informado'}")

    with st.expander("Informações Adicionais"):
        st.write(f"**CNAE Principal:** {data.get('cnae_fiscal', '')} - {data.get('cnae_fiscal_descricao', '')}")
        st.write(f"**Natureza Jurídica:** {data.get('natureza_juridica', '')}")
        st.write(f"**Porte:** {data.get('descricao_porte', '')}")

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
try: st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔍 Consultas Gerais</h1>", unsafe_allow_html=True)

tab_fipe, tab_cnpj = st.tabs(["🚗 Consulta Tabela FIPE", "🏢 Consulta de CNPJ"])

# --- ABA DE CONSULTA FIPE (LÓGICA CORRIGIDA) ---
with tab_fipe:
    st.info("""
    **Como funciona:**
    1.  **Busca Rápida:** Pesquise em nossa base de dados local por qualquer parte do nome do modelo.
    2.  **Busca Guiada e Sincronização:** Se não encontrar, use a busca guiada. Ao selecionar um modelo, **todas as suas versões e anos serão salvos automaticamente** no banco de dados.
    """)

    st.subheader("1. Busca Rápida por Nome (no Banco de Dados Local)")
    modelo_busca_local = st.text_input("Digite o nome do modelo:", key="fipe_busca_local")
    if st.button("Buscar no Banco de Dados", use_container_width=True):
        if modelo_busca_local:
            with st.spinner("Buscando..."):
                resultados_db = umdb.search_vehicle_in_db(modelo_busca_local)
            if resultados_db:
                st.success(f"Encontrados {len(resultados_db)} registros em nosso banco!")
                exibir_resultados_fipe(resultados_db)
            else:
                st.warning("Nenhum registro encontrado no banco de dados local. Tente a busca guiada abaixo.")
        else:
            st.warning("Digite um modelo para buscar.")

    st.markdown("---")

    st.subheader("2. Busca Guiada e Sincronização Automática (via API FIPE)")
    col_tipo, col_marca, col_modelo = st.columns(3)

    tipo_veiculo = col_tipo.selectbox("Tipo de Veículo", ["carros", "motos", "caminhoes"], index=None, placeholder="Selecione...", key="fipe_tipo")

    if tipo_veiculo:
        marcas = get_fipe_marcas(tipo_veiculo)
        marcas_dict = {m['nome']: m['codigo'] for m in marcas}
        marca_selecionada = col_marca.selectbox("Marca", list(marcas_dict.keys()), index=None, placeholder="Selecione...", key="fipe_marca")

        if marca_selecionada:
            codigo_marca = marcas_dict.get(marca_selecionada)
            modelos = get_fipe_modelos_por_marca(tipo_veiculo, codigo_marca)
            modelos_dict = {m['nome']: m['codigo'] for m in modelos}
            modelo_selecionado_nome = col_modelo.selectbox("Modelo", list(modelos_dict.keys()), index=None, placeholder="Selecione...", key="fipe_modelo")

            if modelo_selecionado_nome and st.button("Consultar e Salvar Dados do Modelo", type="primary", use_container_width=True):
                codigo_modelo = modelos_dict.get(modelo_selecionado_nome)
                with st.spinner(f"Buscando todas as versões de '{modelo_selecionado_nome}'..."):
                    dados_completos_modelo = get_fipe_precos_por_modelo(tipo_veiculo, codigo_marca, codigo_modelo)
                    if dados_completos_modelo:
                        umdb.save_fipe_data(dados_completos_modelo)
                        umdb.add_log(st.session_state["username"], "Sincronizou Modelo FIPE", {"modelo": modelo_selecionado_nome, "registros": len(dados_completos_modelo)})
                        st.toast(f"{len(dados_completos_modelo)} registros salvos!", icon="💾")
                        st.success("Dados consultados e salvos com sucesso!")
                        exibir_resultados_fipe(dados_completos_modelo)
                    else:
                        st.error("Falha ao obter dados para este modelo na API.")

# --- ABA DE CONSULTA CNPJ (VISUALIZAÇÃO MELHORADA) ---
with tab_cnpj:
    cnpj_input = st.text_input("Digite o CNPJ:", key="cnpj_input")
    if st.button("Consultar CNPJ", use_container_width=True):
        if cnpj_input:
            with st.spinner("Consultando dados..."):
                dados_cnpj, erro = consultar_cnpj(cnpj_input)
            if erro:
                st.error(f"Falha na consulta: {erro}")
            elif dados_cnpj:
                st.success("Consulta realizada com sucesso!")
                exibir_dados_cnpj(dados_cnpj)
        else:
            st.warning("Digite um CNPJ para consultar.")
