# user_management_db.py
import streamlit as st
import pymongo
from passlib.context import CryptContext
from logger_config import log # Importa o logger

# --- 1. CONFIGURAÇÃO DE SEGURANÇA E CONEXÃO ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@st.cache_resource(show_spinner="A ligar à base de dados...")
def get_mongo_client():
    try:
        connection_string = st.secrets["MONGO_CONNECTION_STRING"]
        client = pymongo.MongoClient(connection_string)
        client.admin.command('ping')
        log.info("Conexão com MongoDB estabelecida com sucesso.")
        return client
    except Exception as e:
        log.critical(f"Erro de conexão com o MongoDB: {e}")
        return None

@st.cache_resource
def get_collection(collection_name: str):
    """Obtém uma coleção específica da base de dados."""
    client = get_mongo_client()
    if client is not None:
        db = client["simulador_db"]
        return db[collection_name]
    return None

def get_users_collection():
    """Função de conveniência para obter a coleção de utilizadores."""
    return get_collection("users")

# --- 2. FUNÇÕES DE GESTÃO DE SENHAS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- 3. FUNÇÕES DE GESTÃO DE UTILIZADORES (CRUD) ---
def fetch_all_users_for_auth():
    users_collection = get_users_collection()
    credentials = {"usernames": {}}
    if users_collection is not None:
        for user in users_collection.find({}, {"_id": 0}):
            username = user.get("username")
            if username:
                credentials["usernames"][username] = {
                    "name": user.get("name"), "email": user.get("email"),
                    "password": user.get("hashed_password"), "role": user.get("role")
                }
    return credentials

def add_user(username, name, email, password, role):
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("A base de dados não está disponível.")
        return False
    if users_collection.find_one({"username": username}):
        st.warning(f"O nome de utilizador '{username}' já existe.")
        return False
    
    users_collection.insert_one({
        "username": username, "name": name, "email": email,
        "hashed_password": get_password_hash(password), "role": role
    })
    log.info(f"Utilizador '{username}' criado com sucesso.")
    return True

# ... (outras funções como get_user_role, update_user_password, etc. continuam aqui, mas usando o logger) ...
# Para poupar espaço, não as vou repetir, mas a lógica é a mesma da versão anterior,
# apenas trocando print() por log.info(), log.warning(), etc.

# --- 4. NOVAS FUNÇÕES PARA DASHBOARD ---
def log_proposal(proposal_data: dict):
    """Guarda os metadados de uma proposta gerada."""
    proposals_collection = get_collection("proposals")
    if proposals_collection is not None:
        try:
            proposals_collection.insert_one(proposal_data)
            log.info(f"Proposta para '{proposal_data.get('empresa')}' registada com sucesso.")
            return True
        except Exception as e:
            log.error(f"Falha ao registar proposta: {e}")
            return False
    return False

def get_all_proposals():
    """Busca todas as propostas para o dashboard."""
    proposals_collection = get_collection("proposals")
    if proposals_collection is not None:
        return list(proposals_collection.find({}, {"_id": 0}))
    return []
