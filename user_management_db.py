# user_management_db.py
import streamlit as st
from pymongo import MongoClient
import streamlit_authenticator as stauth # Para Hasher

# --- Configurações do Banco de Dados ---
@st.cache_resource
def get_mongo_client():
    """Retorna um cliente MongoDB conectado."""
    try:
        # Esta linha VAI FALHAR se o secrets.toml não estiver configurado corretamente
        # Mas o erro atual (ModuleNotFoundError) acontece ANTES disso.
        CONNECTION_STRING = st.secrets["MONGO_CONNECTION_STRING"]
        client = MongoClient(CONNECTION_STRING)
        client.admin.command('ping') # Testa a conexão
        print("Conectado ao MongoDB com sucesso! (user_management_db.py)")
        return client
    except KeyError:
        st.error("ERRO EM user_management_db.py: MONGO_CONNECTION_STRING não encontrada nos segredos.")
        return None
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB (user_management_db.py): {e}")
        return None

@st.cache_resource
def get_users_collection():
    """Retorna a coleção de usuários do MongoDB."""
    client = get_mongo_client()
    if client:
        db = client.simulador_db # Nome do seu banco de dados
        return db.users # Nome da sua coleção de usuários
    st.error("Cliente MongoDB não disponível para get_users_collection.")
    return None

# --- Funções CRUD de Usuários ---
# (Adicione aqui as funções fetch_all_users_for_auth, get_user_role, add_user, etc.
#  que foram fornecidas na resposta completa sobre user_management_db.py)

def add_user(username, name, email, plain_password, role):
    """Adiciona um novo usuário ao banco de dados."""
    users_collection = get_users_collection()
    if not users_collection:
        st.error("Não foi possível conectar à coleção de usuários para adicionar usuário.")
        return False

    if users_collection.find_one({"username": username}):
        st.warning(f"Usuário '{username}' já existe.")
        return False

    try:
        hashed_password = stauth.Hasher([plain_password]).generate()[0]
        users_collection.insert_one({
            "username": username,
            "name": name,
            "email": email,
            "hashed_password": hashed_password,
            "role": role
        })
        st.success(f"Usuário '{username}' cadastrado com sucesso! (user_management_db.py)")
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar usuário (user_management_db.py): {e}")
        return False

def fetch_all_users_for_auth():
    """Busca todos os usuários e formata para o streamlit-authenticator."""
    users_collection = get_users_collection()
    if not users_collection:
        # Se o erro for de MONGO_CONNECTION_STRING, a mensagem já terá sido dada por get_mongo_client
        # st.error("Coleção de usuários não disponível para fetch_all_users_for_auth.")
        return {"usernames": {}} # Retorna vazio para evitar mais erros

    users_from_db = list(users_collection.find({}))
    credentials = {"usernames": {}}
    for user in users_from_db:
        credentials["usernames"][user["username"]] = {
            "name": user["name"],
            "email": user.get("email", ""),
            "password": user["hashed_password"],
            "role": user["role"]
        }
    return credentials

def get_user_role(username):
    """Busca o papel (role) de um usuário específico."""
    users_collection = get_users_collection()
    if not users_collection:
        return None
    user_data = users_collection.find_one({"username": username})
    return user_data["role"] if user_data else None

# Adicione as outras funções (update_user_details, delete_user, etc.) aqui
# conforme a resposta anterior mais completa.