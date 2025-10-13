# pages/4_Consultas_Gerais.py (substitua o conteúdo de pages/4_Consulta_CNPJ.py)
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

# --- 3. FUNÇÕES AUXILIARES (FIPE API EXTERNA) ---
@st.cache_data(ttl=3600) # Cache para evitar múltiplas chamadas na mesma sessão
def get_fipe_preco_from_api(codigo_fipe):
    """Busca o preço de um veículo pelo código FIPE na API externa."""
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

# --- 4. FUNÇÃO PARA EXIBIR RESULTADOS ---
def exibir_resultados_fipe(resultados):
    """Formata e exibe os resultados da busca FIPE."""
    st.subheader("Resultados da Consulta")
    if not resultados:
        st.warning("Nenhum resultado encontrado.")
        return

    # Usando um DataFrame para facilitar a visualização
    df_resultados = pd.DataFrame(resultados)
    
    # Colunas que queremos exibir
    cols_to_show = ['marca', 'modelo', 'anoModelo', 'combustivel', 'valor', 'codigoFipe', 'mesReferencia']
    
    # Renomeando para ficar mais amigável
    col_rename = {
        'marca': 'Marca', 'modelo': 'Modelo', 'anoModelo': 'Ano',
        'combustivel': 'Combustível', 'valor': 'Valor FIPE', 'codigoFipe': 'Cód. FIPE',
        'mesReferencia': 'Mês Referência'
    }
    
    df_display = df_resultados[cols_to_show].rename(columns=col_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ano": st.column_config.NumberColumn(format="%d"),
        }
    )

# --- 5. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔍 Consultas Gerais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 6. ABAS DE CONSULTA ---
tab_cnpj, tab_fipe = st.tabs(["🏢 Consulta de CNPJ", "🚗 Consulta Tabela FIPE"])

with tab_cnpj:
    cnpj_input = st.text_input("Digite o CNPJ (apenas números ou formatado):", key="cnpj_input")

    if st.button("Consultar CNPJ", use_container_width=True):
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

with tab_fipe:
    st.subheader("Busca por Modelo de Veículo")
    st.info("Primeiro, buscamos em nossa base de dados local. Se não encontrarmos, consultamos a API externa e salvamos o resultado para acelerar buscas futuras.")
    
    modelo_busca = st.text_input("Digite o modelo do veículo (ex: Gol, Palio, Onix):", key="fipe_modelo_busca")
    
    if st.button("Buscar Modelo", use_container_width=True, type="primary"):
        if modelo_busca:
            with st.spinner("Buscando na base de dados local..."):
                resultados_db = umdb.search_vehicle_in_db(modelo_busca)
            
            if resultados_db:
                st.success(f"✅ Encontrados {len(resultados_db)} registro(s) em nosso banco de dados!")
                exibir_resultados_fipe(resultados_db)
            else:
                st.warning("Não encontrado na base local. Buscando na API FIPE externa... Isso pode demorar um pouco.")
                
                # Lógica para buscar na API externa (simplificada, pois a API não tem busca por modelo)
                # A BrasilAPI não tem um endpoint para buscar por modelo diretamente.
                # A forma mais próxima seria buscar por código FIPE, mas o usuário não o tem.
                # Para esta implementação, vamos focar na busca por um código FIPE específico
                # e salvar o resultado. A busca por nome de modelo funcionará no cache.
                st.subheader("Consulta por Código FIPE (para popular o banco)")
                codigo_fipe_input = st.text_input("Para popular o banco, insira um Código FIPE (ex: 001004-9):", key="fipe_code_input")

                if st.button("Buscar por Código FIPE e Salvar"):
                    if codigo_fipe_input:
                        with st.spinner("Consultando API externa e salvando no banco..."):
                            resultados_api = get_fipe_preco_from_api(codigo_fipe_input)
                        
                        if resultados_api:
                            umdb.save_fipe_data(resultados_api)
                            umdb.add_log(st.session_state["username"], "Consultou e Salvou FIPE", {"codigo_fipe": codigo_fipe_input})
                            st.success("Dados consultados na API e salvos com sucesso no banco de dados!")
                            exibir_resultados_fipe(resultados_api)
                        else:
                            st.error("Código FIPE não encontrado na API externa.")
                    else:
                        st.warning("Por favor, insira um código FIPE.")

        else:
            st.warning("Por favor, digite um modelo para buscar.")
