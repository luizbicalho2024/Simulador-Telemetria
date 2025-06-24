import streamlit as st
import requests
import base64
import json

# --- Constantes da API Unipix ---
BASE_URL = "https://api-sms-cliente.unipix.com.br/v2/api"

# --- Funções de Interação com a API Unipix ---

def get_unipix_auth_header():
    """Cria o header de autenticação Basic Auth a partir dos secrets."""
    user = st.secrets["UNIPIX_USER"]
    password = st.secrets["UNIPIX_PASSWORD"]
    
    # Codifica o usuário e senha em Base64 para o Basic Auth
    credentials = f"{user}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    return headers

@st.cache_data(ttl=3600) # Cache por 1 hora para não buscar o centro de custo toda hora
def fetch_centro_custo_info():
    """
    Busca as informações de Centro de Custo e Produto da API Unipix.
    ATENÇÃO: A URL exata ('/centro-custo') é uma suposição baseada na documentação.
    Pode ser necessário ajustá-la.
    """
    url = f"{BASE_URL}/centro-custo" # Verifique se este é o endpoint correto na doc
    headers = get_unipix_auth_header()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança um erro para respostas HTTP 4xx/5xx
        
        data = response.json()
        # Vamos pegar o primeiro centro de custo e produto encontrado na lista
        if data and len(data) > 0 and 'produtos' in data[0] and len(data[0]['produtos']) > 0:
            centro_custo_id = data[0]['id']
            produto_id = data[0]['produtos'][0]['id']
            return True, centro_custo_id, produto_id
        else:
            return False, "Nenhum centro de custo ou produto encontrado.", None
            
    except requests.exceptions.RequestException as e:
        return False, f"Erro ao buscar centro de custo: {e}", None
    except (KeyError, IndexError):
        return False, "Resposta da API de centro de custo não está no formato esperado.", None

def enviar_sms_via_unipix(destinatario, mensagem, centro_custo_id, produto_id):
    """
    Envia a mensagem de texto usando a API da Unipix.
    A documentação não mostra o endpoint de envio, vamos assumir um endpoint comum como '/sms/enviar'
    """
    # IMPORTANTE: Confirme o endpoint correto para o envio de SMS avulso na documentação
    url = f"{BASE_URL}/sms/enviar" 
    headers = get_unipix_auth_header()
    
    # O corpo da requisição (payload) precisa ser construído como um JSON
    # A estrutura abaixo é uma suposição baseada em APIs similares. VERIFIQUE A DOCUMENTAÇÃO!
    payload = {
        "centroCustoId": centro_custo_id,
        "produtoId": produto_id,
        "mensagem": mensagem,
        "numeros": [
            f"55{destinatario}" # API geralmente espera o número com código do país (55)
        ]
        # Outros parâmetros podem ser necessários, como "identificador", "flashSms", etc.
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        # A API pode retornar um ID de campanha ou de envio
        response_data = response.json()
        return True, response_data

    except requests.exceptions.RequestException as e:
        error_details = f"Erro na requisição: {e}"
        if e.response is not None:
            error_details += f" | Resposta da API: {e.response.text}"
        return False, error_details


# --- Função de Comando (Inalterada) ---
def montar_comando_apn(tracker_id, apn, user, password):
    """
    Função para montar o comando de configuração de APN.
    ATENÇÃO: Este é um EXEMPLO. Verifique a sintaxe CORRETA no manual do seu rastreador Suntech!
    """
    command = f"ST300CMD;{tracker_id};01;1;APN={apn};USR={user};PWD={password};"
    return command


# --- Interface da Aplicação com Streamlit (Lógica Principal Atualizada) ---

st.set_page_config(page_title="Configurador Remoto Suntech (Unipix)", layout="centered")

st.title("🚀 Configurador Remoto para Rastreadores Suntech")
st.markdown("Interface para envio de comandos via **Unipix SMS**.")

with st.form("config_form"):
    st.header("Dados do Rastreador e do Chip")
    tracker_id = st.text_input("ID do Rastreador", placeholder="Ex: 035123456789012")
    phone_number = st.text_input("Número do Chip (SIM Card)", placeholder="Apenas números, com DDD. Ex: 11987654321")
    
    st.header("Configuração da APN")
    apn_name = st.text_input("Nome da APN", placeholder="Ex: internet.vivo.br")
    apn_user = st.text_input("Usuário da APN (se houver)", placeholder="Ex: vivo")
    apn_password = st.text_input("Senha da APN (se houver)", type="password", placeholder="Ex: vivo")

    submitted = st.form_submit_button("Enviar Comando de Configuração")

if submitted:
    if not all([tracker_id, phone_number, apn_name]):
        st.warning("Por favor, preencha todos os campos obrigatórios: ID, Número do Chip e Nome da APN.")
    else:
        with st.spinner("Verificando credenciais e centro de custo na Unipix..."):
            # 1. Buscar as informações do centro de custo
            sucesso_cc, cc_id, p_id = fetch_centro_custo_info()

        if not sucesso_cc:
            st.error(f"Não foi possível obter os dados da Unipix: {cc_id}")
        else:
            st.success(f"Centro de Custo ({cc_id}) e Produto ({p_id}) encontrados!")
            
            with st.spinner("Montando e enviando o comando SMS..."):
                # 2. Montar o comando Suntech
                comando_final = montar_comando_apn(tracker_id, apn_name, apn_user, apn_password)
                st.code(f"Comando a ser enviado:\n{comando_final}", language="text")

                # 3. Enviar o SMS via Unipix
                sucesso_envio, resposta_envio = enviar_sms_via_unipix(phone_number, comando_final, cc_id, p_id)

                if sucesso_envio:
                    st.success("Comando enviado com sucesso pela Unipix!")
                    st.json(resposta_envio) # Mostra a resposta completa da API
                    st.balloons()
                else:
                    st.error("Falha ao enviar o SMS pela Unipix.")
                    st.error(f"Detalhe do erro: {resposta_envio}")

st.sidebar.info(
    "Verifique se seu usuário e senha da Unipix estão corretamente configurados nos 'Secrets' da aplicação."
)
