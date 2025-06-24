import streamlit as st
import requests
import base64
import json

# --- Configurações Gerais ---
# URL base da API. Verifique se está correta.
BASE_URL = "https://api-sms-cliente.unipix.com.br/v2/api"

# --- Funções de Segurança e Autenticação ---

def check_password():
    """Verifica a senha de acesso da aplicação Streamlit."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        password = st.text_input("Digite a senha para acessar a ferramenta", type="password")
        if st.button("Entrar"):
            # A senha do app deve estar nos seus secrets
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("A senha está incorreta.")
        st.stop()

def get_unipix_auth_header():
    """Cria o cabeçalho de autenticação Basic Auth com as credenciais da Unipix."""
    try:
        user = st.secrets["UNIPIX_USER"]
        password = st.secrets["UNIPIX_PASSWORD"]
        credentials = f"{user}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        return headers
    except KeyError as e:
        st.error(f"Erro de configuração: A credencial '{e.args[0]}' não foi encontrada nos Secrets do Streamlit.")
        st.stop()

# --- Funções de Interação com a API Unipix ---

@st.cache_data(ttl=3600) # Cache por 1 hora para evitar chamadas repetidas
def fetch_centro_custo_info(_auth_headers):
    """Busca as informações de Centro de Custo e Produto da API Unipix."""
    # SUPOSIÇÃO 1: Verifique se a URL para buscar o centro de custo está correta.
    url = f"{BASE_URL}/centro-custo"
    
    try:
        response = requests.get(url, headers=_auth_headers)
        response.raise_for_status()  # Lança um erro para respostas HTTP 4xx/5xx
        data = response.json()
        
        if data and len(data) > 0 and 'produtos' in data[0] and len(data[0]['produtos']) > 0:
            centro_custo_id = data[0]['id']
            produto_id = data[0]['produtos'][0]['id']
            return True, centro_custo_id, produto_id
        else:
            return False, "Resposta da API recebida, mas nenhum centro de custo ou produto foi encontrado.", None
            
    except requests.exceptions.RequestException as e:
        error_details = f"Erro ao buscar centro de custo: {e}"
        if e.response is not None:
            error_details += f"\n\nResposta da API (Status {e.response.status_code}):\n{e.response.text}"
        return False, error_details, None

def enviar_sms_via_unipix(auth_headers, destinatario, mensagem, centro_custo_id, produto_id):
    """Envia a mensagem de texto usando a API da Unipix."""
    # SUPOSIÇÃO 2: Verifique se a URL para envio avulso está correta.
    url = f"{BASE_URL}/sms/enviar"
    
    # SUPOSIÇÃO 3: Verifique se a estrutura do corpo (payload) JSON está correta.
    payload = {
        "centroCustoId": centro_custo_id,
        "produtoId": produto_id,
        "mensagem": mensagem,
        "numeros": [f"55{destinatario}"]  # Adiciona o código de país 55
    }

    try:
        response = requests.post(url, headers=auth_headers, data=json.dumps(payload))
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        error_details = f"Erro na requisição de envio: {e}"
        if e.response is not None:
            error_details += f"\n\nResposta da API (Status {e.response.status_code}):\n{e.response.text}"
        return False, error_details

# --- Função de Negócio ---

def montar_comando_apn(tracker_id, apn, user, password):
    """Monta o comando de configuração de APN para o rastreador Suntech."""
    # ATENÇÃO: Verifique a sintaxe CORRETA no manual do seu modelo de rastreador!
    return f"ST300CMD;{tracker_id};01;1;APN={apn};USR={user};PWD={password};"

# --- Interface Principal da Aplicação ---

st.set_page_config(page_title="Configurador Remoto Suntech", layout="centered")
st.title("🚀 Configurador Remoto para Rastreadores Suntech")

# 1. Trava de Segurança
check_password()

# 2. Autenticação na API e busca de IDs
auth_headers = get_unipix_auth_header()
sucesso_cc, cc_id_or_error, p_id = fetch_centro_custo_info(auth_headers)

if not sucesso_cc:
    st.error("Falha ao obter os dados de configuração da Unipix.")
    st.code(cc_id_or_error, language="text")
    st.warning("Verifique suas credenciais da Unipix e a URL do centro de custo no código.")
else:
    st.success(f"Conectado à Unipix com sucesso. (Centro de Custo: {cc_id_or_error})")
    
    # 3. Formulário de Configuração (só aparece se a conexão com a Unipix funcionar)
    with st.form("config_form"):
        st.header("Dados do Rastreador e do Chip")
        tracker_id = st.text_input("ID do Rastreador", placeholder="Ex: 035123456789012")
        phone_number = st.text_input("Número do Chip (SIM Card)", placeholder="Apenas números, com DDD. Ex: 11987654321")
        
        st.header("Configuração da APN")
        apn_name = st.text_input("Nome da APN", placeholder="Ex: internet.vivo.br")
        apn_user = st.text_input("Usuário da APN (se houver)", placeholder="Ex: vivo")
        apn_password = st.text_input("Senha da APN (se houver)", type="password", placeholder="Ex: vivo")

        submitted = st.form_submit_button("✔️ Enviar Comando de Configuração")

    # 4. Lógica de Envio
    if submitted:
        if not all([tracker_id, phone_number, apn_name]):
            st.warning("Por favor, preencha todos os campos obrigatórios.")
        else:
            with st.spinner("Montando e enviando o comando SMS..."):
                comando_final = montar_comando_apn(tracker_id, apn_name, apn_user, apn_password)
                
                sucesso_envio, resposta_envio = enviar_sms_via_unipix(
                    auth_headers, phone_number, comando_final, cc_id_or_error, p_id
                )

                if sucesso_envio:
                    st.success("Comando enviado com sucesso pela Unipix!")
                    st.json(resposta_envio)
                    st.balloons()
                else:
                    st.error("Falha ao enviar o SMS pela Unipix.")
                    st.code(resposta_envio, language="text")
