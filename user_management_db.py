# user_management_db.py
import streamlit as st
from pymongo import MongoClient
import streamlit_authenticator as stauth # Para Hasher

# --- Configurações do Banco de Dados ---
@st.cache_resource # Cache para evitar reconexões constantes
def get_mongo_client():
    """Retorna um cliente MongoDB conectado."""
    try:
        CONNECTION_STRING = st.secrets["MONGO_CONNECTION_STRING"]
        client = MongoClient(CONNECTION_STRING)
        # Test connection
        client.admin.command('ping')
        print("Conectado ao MongoDB com sucesso!")
        return client
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB: {e}")
        return None

@st.cache_resource
def get_users_collection():
    """Retorna a coleção de usuários do MongoDB."""
    client = get_mongo_client()
    if client:
        db = client.simulador_db # Nome do seu banco de dados
        return db.users # Nome da sua coleção de usuários
    return None

# --- Funções CRUD de Usuários ---

def fetch_all_users_for_auth():
    """Busca todos os usuários e formata para o streamlit-authenticator."""
    users_collection = get_users_collection()
    if not users_collection:
        return {"usernames": {}}

    users_from_db = list(users_collection.find({}))
    credentials = {"usernames": {}}
    for user in users_from_db:
        credentials["usernames"][user["username"]] = {
            "name": user["name"],
            "email": user.get("email", ""), # Email é opcional
            "password": user["hashed_password"], # Senha já deve estar hasheada
            "role": user["role"] # Adicionamos o role aqui
        }
    return credentials

def get_user_role(username):
    """Busca o papel (role) de um usuário específico."""
    users_collection = get_users_collection()
    if not users_collection:
        return None
    user_data = users_collection.find_one({"username": username})
    return user_data["role"] if user_data else None


def add_user(username, name, email, plain_password, role):
    """Adiciona um novo usuário ao banco de dados."""
    users_collection = get_users_collection()
    if not users_collection:
        st.error("Não foi possível conectar à coleção de usuários.")
        return False

    if users_collection.find_one({"username": username}):
        st.warning(f"Usuário '{username}' já existe.")
        return False

    hashed_password = stauth.Hasher([plain_password]).generate()[0]
    try:
        users_collection.insert_one({
            "username": username,
            "name": name,
            "email": email,
            "hashed_password": hashed_password,
            "role": role
        })
        st.success(f"Usuário '{username}' cadastrado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar usuário: {e}")
        return False

def update_user_details(username, name, email, role):
    """Atualiza os detalhes de um usuário (nome, email, role)."""
    users_collection = get_users_collection()
    if not users_collection:
        st.error("Não foi possível conectar à coleção de usuários.")
        return False
    try:
        users_collection.update_one(
            {"username": username},
            {"$set": {"name": name, "email": email, "role": role}}
        )
        st.success(f"Detalhes do usuário '{username}' atualizados.")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar usuário: {e}")
        return False

def delete_user(username):
    """Exclui um usuário do banco de dados."""
    users_collection = get_users_collection()
    if not users_collection:
        st.error("Não foi possível conectar à coleção de usuários.")
        return False
    try:
        # Segurança: Não permitir excluir o último admin se for o próprio
        if st.session_state.get("role") == "admin" and st.session_state.get("username") == username:
            admin_users_count = users_collection.count_documents({"role": "admin"})
            if admin_users_count <= 1:
                st.error("Não é possível excluir o único administrador.")
                return False

        users_collection.delete_one({"username": username})
        st.success(f"Usuário '{username}' excluído.")
        return True
    except Exception as e:
        st.error(f"Erro ao excluir usuário: {e}")
        return False

def update_user_password_by_admin(username, plain_password):
    """Admin redefine a senha de um usuário."""
    users_collection = get_users_collection()
    if not users_collection:
        st.error("Não foi possível conectar à coleção de usuários.")
        return False
    hashed_password = stauth.Hasher([plain_password]).generate()[0]
    try:
        users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": hashed_password}}
        )
        st.success(f"Senha do usuário '{username}' redefinida.")
        return True
    except Exception as e:
        st.error(f"Erro ao redefinir senha: {e}")
        return False

def update_user_password_self(username, new_hashed_password):
    """Usuário altera a própria senha (recebe hash já processado pelo authenticator)."""
    users_collection = get_users_collection()
    if not users_collection:
        st.error("Não foi possível conectar à coleção de usuários.")
        return False
    try:
        users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        # st.success("Sua senha foi alterada com sucesso!") # Mensagem dada pelo authenticator
        return True
    except Exception as e:
        st.error(f"Erro ao salvar nova senha no banco: {e}")
        return False

def get_all_usernames_and_roles():
    """Retorna uma lista de tuplas (username, role) para exibição no painel admin."""
    users_collection = get_users_collection()
    if not users_collection:
        return []
    users_from_db = list(users_collection.find({}, {"username": 1, "role": 1, "name":1, "email":1, "_id": 0}))
    return users_from_db