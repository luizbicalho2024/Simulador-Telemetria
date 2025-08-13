# pages/Consulta_CNPJ.py
import streamlit as st
import pandas as pd
import requests
import re

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Consulta de CNPJ",
    page_icon="🏢"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO AUXILIAR PARA A CONSULTA À API ---
@st.cache_data(ttl=3600) # Cache de 1 hora para evitar consultas repetidas
def consultar_cnpj(cnpj: str):
    """
    Consulta um CNPJ na BrasilAPI e retorna os dados em formato JSON.
    """
    # Remove qualquer formatação do CNPJ (pontos, barras, etc.)
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj_limpo) != 14:
        return None, "O CNPJ deve ter 14 dígitos."

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            return None, "CNPJ não encontrado na base de dados da Receita Federal."
        else:
            return None, f"Erro na API. Código: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Erro de conexão: {e}"

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🏢 Consulta de CNPJ</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. CAMPO DE INPUT E BOTÃO DE CONSULTA ---
st.subheader("Consultar CNPJ na Receita Federal")
cnpj_input = st.text_input("Digite o CNPJ (apenas números ou formatado):", key="cnpj_input")

if st.button("Consultar CNPJ", use_container_width=True, type="primary"):
    if cnpj_input:
        with st.spinner("A consultar..."):
            dados_cnpj, erro = consultar_cnpj(cnpj_input)
        
        st.markdown("---")
        
        if erro:
            st.error(f"**Falha na consulta:** {erro}")
        elif dados_cnpj:
            st.success("**Consulta realizada com sucesso!**")
            st.header(dados_cnpj.get("razao_social", "Razão Social não informada"))
            
            # --- SEÇÃO DE INFORMAÇÕES PRINCIPAIS ---
            st.subheader("Informações Principais")
            col1, col2, col3 = st.columns(3)
            col1.metric("Nome Fantasia", dados_cnpj.get("nome_fantasia") or "N/A")
            col2.metric("Situação Cadastral", dados_cnpj.get("descricao_situacao_cadastral", "N/A"))
            col3.metric("Data de Abertura", dados_cnpj.get("data_inicio_atividade", "N/A"))

            # --- SEÇÃO DE ENDEREÇO ---
            with st.expander("📍 Endereço"):
                endereco = f"{dados_cnpj.get('descricao_tipo_de_logradouro', '')} {dados_cnpj.get('logradouro', '')}, {dados_cnpj.get('numero', '')}"
                complemento = dados_cnpj.get('complemento', '')
                if complemento:
                    endereco += f" - {complemento}"
                
                st.write(f"**Endereço:** {endereco}")
                st.write(f"**Bairro:** {dados_cnpj.get('bairro', '')}")
                st.write(f"**Cidade/UF:** {dados_cnpj.get('municipio', '')} / {dados_cnpj.get('uf', '')}")
                st.write(f"**CEP:** {dados_cnpj.get('cep', '')}")

            # --- SEÇÃO DE CONTATO ---
            with st.expander("📞 Contato"):
                st.write(f"**Telefone:** {dados_cnpj.get('ddd_telefone_1', '')}")
                st.write(f"**E-mail:** {dados_cnpj.get('email') or 'Não informado'}")

            # --- SEÇÃO DE ATIVIDADES ---
            with st.expander("📋 Atividades (CNAE)"):
                st.write(f"**Atividade Principal:** {dados_cnpj.get('cnae_fiscal_descricao', '')}")
                if dados_cnpj.get("cnaes_secundarios"):
                    st.write("**Atividades Secundárias:**")
                    for cnae in dados_cnpj["cnaes_secundarios"]:
                        st.markdown(f"- {cnae['descricao']}")
            
            # --- SEÇÃO DE SÓCIOS (QSA) ---
            with st.expander("👥 Quadro de Sócios e Administradores (QSA)"):
                qsa = dados_cnpj.get("qsa")
                if qsa:
                    df_qsa = pd.DataFrame(qsa)
                    st.dataframe(
                        df_qsa[['nome_socio', 'qualificacao_socio', 'data_entrada_sociedade']],
                        column_config={
                            "nome_socio": "Nome do Sócio",
                            "qualificacao_socio": "Qualificação",
                            "data_entrada_sociedade": "Data de Entrada"
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Quadro de sócios não informado ou não disponível para esta natureza jurídica.")
    else:
        st.warning("Por favor, digite um CNPJ para consultar.")
