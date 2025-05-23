# user_management_db.py
import streamlit as st
from pymongo import MongoClient, errors as pymongo_errors
import streamlit_authenticator as stauth
import certifi # Para tlsCAFile

# --- Configurações do Banco de Dados ---
@st.cache_resource(show_spinner="Conectando ao Banco de Dados...")
def get_mongo_client():
    """Retorna um cliente MongoDB conectado."""
    try:
        if "MONGO_CONNECTION_STRING" not in st.secrets:
            st.error("CRÍTICO: MONGO_CONNECTION_STRING não encontrada nos segredos. Verifique o arquivo .streamlit/secrets.toml")
            return None
        CONNECTION_STRING = st.secrets["MONGO_CONNECTION_STRING"]
        
        client = MongoClient(
            CONNECTION_STRING,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000
        )
        client.admin.command('ping')
        print("INFO: Conectado ao MongoDB com sucesso! (user_management_db.py)")
        return client
    except pymongo_errors.ConfigurationError as ce:
        st.error(f"Erro de Configuração do PyMongo (user_management_db.py): {ce}")
        st.error("Verifique a sua MONGO_CONNECTION_STRING.")
        return None
    except pymongo_errors.ServerSelectionTimeoutError as sste:
        st.error(f"Timeout ao tentar conectar ao MongoDB (user_management_db.py): {sste}")
        st.error("Possíveis causas: IP não liberado no MongoDB Atlas, firewall bloqueando, problemas de rede, ou o serviço MongoDB pode estar offline.")
        return None
    except Exception as e:
        st.error(f"Erro geral ao conectar ao MongoDB (user_management_db.py): {e}")
        st.error(f"Tipo do erro: {type(e)}")
        st.error("Verifique a MONGO_CONNECTION_STRING, acesso à rede no Atlas, e logs para mais detalhes.")
        return None

@st.cache_resource
def get_users_collection():
    """Retorna a coleção de usuários do MongoDB."""
    client = get_mongo_client()
    if client is None: # CORRIGIDO AQUI TAMBÉM POR PRECAUÇÃO
        return None 
    db_name_str = st.secrets.get("MONGO_DB_NAME", "simulador_db")
    collection_name_str = st.secrets.get("MONGO_USERS_COLLECTION", "users")
    db = client[db_name_str]
    return db[collection_name_str]

# --- Funções CRUD de Usuários ---

def fetch_all_users_for_auth():
    """Busca todos os usuários e formata para o streamlit-authenticator."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        # get_users_collection ou get_mongo_client já deve ter mostrado um erro
        return {"usernames": {}}

    try:
        users_from_db = list(users_collection.find({}))
    except Exception as e:
        st.error(f"Erro ao buscar usuários do banco de dados: {e}")
        return {"usernames": {}}
        
    credentials = {"usernames": {}}
    for user in users_from_db:
        if "username" not in user or "name" not in user or "hashed_password" not in user or "role" not in user:
            st.warning(f"Usuário com dados incompletos encontrado no DB: {user.get('_id')}. Ignorando.")
            continue
        credentials["usernames"][user["username"]] = {
            "name": user["name"],
            "email": user.get("email", ""),
            "password": user["hashed_password"],
            "role": user["role"]
        }
    return credentials

def get_user_role(username: str):
    """Busca o papel (role) de um usuário específico."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None or not username:
        return None
    try:
        user_data = users_collection.find_one({"username": username})
        return user_data["role"] if user_data and "role" in user_data else None
    except Exception as e:
        st.error(f"Erro ao buscar papel do usuário '{username}': {e}")
        return None


def add_user(username: str, name: str, email: str, plain_password: str, role: str):
    """Adiciona um novo usuário ao banco de dados."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        st.error("Não foi possível acessar a coleção de usuários para adicionar.")
        return False

    try:
        if users_collection.find_one({"username": username}): # find_one retorna None se não achar, o que é ok para if
            st.warning(f"Usuário '{username}' já existe.")
            return False

        hashed_password = stauth.Hasher([plain_password]).generate()[0]
        user_doc = {
            "username": username,
            "name": name,
            "email": email,
            "hashed_password": hashed_password,
            "role": role
        }
        users_collection.insert_one(user_doc)
        st.success(f"Usuário '{username}' cadastrado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar usuário '{username}': {e}")
        return False

def update_user_details(username: str, name: str, email: str, role: str):
    """Atualiza os detalhes de um usuário (nome, email, role)."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        st.error("Não foi possível acessar a coleção de usuários para atualizar.")
        return False
    try:
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"name": name, "email": email, "role": role}}
        )
        if result.modified_count > 0:
            st.success(f"Detalhes do usuário '{username}' atualizados.")
            return True
        else:
            st.info(f"Nenhuma alteração detectada para o usuário '{username}' ou usuário não encontrado.")
            return False # Mudado para False para consistência se não houve modificação
    except Exception as e:
        st.error(f"Erro ao atualizar usuário '{username}': {e}")
        return False

def delete_user(username: str):
    """Exclui um usuário do banco de dados."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        st.error("Não foi possível acessar a coleção de usuários para excluir.")
        return False
    try:
        current_user_is_admin = st.session_state.get("role") == "admin"
        current_username = st.session_state.get("username")

        if current_user_is_admin and current_username == username:
            admin_users_count = users_collection.count_documents({"role": "admin"})
            if admin_users_count <= 1:
                st.error("Não é possível excluir o único administrador.")
                return False

        result = users_collection.delete_one({"username": username})
        if result.deleted_count > 0:
            st.success(f"Usuário '{username}' excluído.")
            return True
        else:
            st.warning(f"Usuário '{username}' não encontrado para exclusão.")
            return False
    except Exception as e:
        st.error(f"Erro ao excluir usuário '{username}': {e}")
        return False

def update_user_password_by_admin(username: str, plain_password: str):
    """Admin redefine a senha de um usuário."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        st.error("Não foi possível acessar a coleção de usuários para redefinir senha.")
        return False
    try:
        hashed_password = stauth.Hasher([plain_password]).generate()[0]
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": hashed_password}}
        )
        if result.modified_count > 0:
            st.success(f"Senha do usuário '{username}' redefinida com sucesso.")
            return True
        else:
            st.warning(f"Senha do usuário '{username}' não alterada (usuário não encontrado ou senha igual).")
            return False
    except Exception as e:
        st.error(f"Erro ao redefinir senha do usuário '{username}': {e}")
        return False

def update_user_password_self(username: str, new_hashed_password: str):
    """Usuário altera a própria senha (recebe hash já processado pelo authenticator)."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        st.error("Não foi possível acessar a coleção de usuários para alterar sua senha.")
        return False
    try:
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        # Mesmo que a senha seja igual (modified_count == 0), a operação em si foi um "sucesso"
        return True 
    except Exception as e:
        st.error(f"Erro ao salvar sua nova senha no banco: {e}")
        return False

def get_all_users_for_admin_display():
    """Retorna uma lista de dicts de usuários para exibição no painel admin."""
    users_collection = get_users_collection()
    # CORREÇÃO APLICADA ABAIXO:
    if users_collection is None:
        return []
    try:
        users_from_db = list(users_collection.find({}, {"_id": 0, "hashed_password": 0}))
        return users_from_db
    except Exception as e:
        st.error(f"Erro ao buscar lista de usuários para admin: {e}")
        return []