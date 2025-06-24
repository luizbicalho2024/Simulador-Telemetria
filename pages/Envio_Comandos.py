import streamlit as st
import requests
import base64
import json

# --- Constantes e Configurações ---
BASE_URL = "https://api-sms-cliente.unipix.com.br/v2/api"

# --- Funções de Interação com a API Unipix (Versão Melhorada) ---

def get_unipix_auth_header():
    """Cria o header de autenticação Basic Auth a partir dos secrets."""
    # Esta função está correta e não precisa de alterações.
    user = st.secrets["UNIPIX_USER"]
    password = st.secrets["UNIPIX_PASSWORD"]
    credentials = f"{user}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    return headers

@st.cache_data(ttl=3600)
def fetch_centro_custo_info():
    """
    Busca as informações de Centro de Custo e Produto da API Unipix.
    A URL '/centro-custo' é uma suposição e pode precisar de ajuste.
    """
    # SUPOSIÇÃO 1: A URL para buscar o centro de custo.
    url = f"{BASE_URL}/centro-custo" 
    headers = get_unipix_auth_header()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança um erro para respostas HTTP 4xx/5xx
        
        data = response.json()
        if data and len(data) > 0 and 'produtos' in data[0] and len(data[0]['produtos']) > 0:
            centro_custo_id = data[0]['id']
            produto_id = data[0]['produtos'][0]['id']
            return True, centro_custo_id, produto_id
        else:
            return False, "Resposta da API recebida, mas nenhum centro de custo ou produto foi encontrado.", None
            
    except requests.exceptions.RequestException as e:
        # Se a chamada falhar, agora vamos mostrar a resposta da API para depuração.
        error_details = f"Erro ao buscar centro de custo: {e}"
        if e.response is not None:
            error_details += f"\n\nResposta da API (Status {e.response.status_code}):\n{e.response.text}"
        return False, error_details, None

def enviar_sms_via_unipix(destinatario, mensagem, centro_custo_id, produto_id):
    """
    Envia a mensagem de texto usando a API da Unipix.
    A URL e o payload são suposições e podem precisar de ajustes.
    """
    # SUPOSIÇÃO 2: A URL para envio avulso.
    url = f"{BASE_URL}/sms/enviar" 
    headers = get_unipix_auth_header()
    
    # SUPOSIÇÃO 3: A estrutura do corpo (payload) JSON.
    payload = {
        "centroCustoId": centro_custo_id,
        "produtoId": produto_id,
        "mensagem": mensagem,
        "numeros": [f"55{destinatario}"] # Adiciona o código de país 55
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return True, response.json()

    except requests.exceptions.RequestException as e:
        # Tratamento de erro melhorado para a função de envio.
        error_details = f"Erro na requisição de envio: {e}"
        if e.response is not None:
            error_details += f"\n\nResposta da API (Status {e.response.status_code}):\n{e.response.text}"
        return False, error_details

# --- O resto do seu código (função de montar comando e interface Streamlit) ---
# Nenhuma alteração é necessária aqui. O código abaixo pode ser usado como está.

def montar_comando_apn(tracker_id, apn, user, password):
    command = f"ST300CMD;{tracker_id};01;1;APN={apn};USR={user};PWD={password};"
    return command

# ... (cole aqui a sua interface Streamlit com o formulário) ...
# O código da interface que você já tem está correto.
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
            sucesso_cc, cc_id_or_error, p_id = fetch_centro_custo_info()

        if not sucesso_cc:
            st.error("Falha ao obter os dados da Unipix.")
            st.code(cc_id_or_error, language="text") # Mostra o erro detalhado da API
        else:
            st.success(f"Centro de Custo ({cc_id_or_error}) e Produto ({p_id}) encontrados!")
            
            with st.spinner("Montando e enviando o comando SMS..."):
                comando_final = montar_comando_apn(tracker_id, apn_name, apn_user, apn_password)
                
                sucesso_envio, resposta_envio = enviar_sms_via_unipix(phone_number, comando_final, cc_id_or_error, p_id)

                if sucesso_envio:
                    st.success("Comando enviado com sucesso pela Unipix!")
                    st.json(resposta_envio)
                    st.balloons()
                else:
                    st.error("Falha ao enviar o SMS pela Unipix.")
                    st.code(resposta_envio, language="text") # Mostra o erro detalhado da API
