# user_management_db.py
import streamlit as st
import pymongo
from passlib.context import CryptContext

# --- 1. CONFIGURAÇÃO DE SEGURANÇA E CONEXÃO ---

# Cria um contexto de criptografia usando bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@st.cache_resource(show_spinner="A ligar à base de dados...")
def get_mongo_client():
    """Estabelece e armazena em cache a conexão com o MongoDB."""
    try:
        connection_string = st.secrets["MONGO_CONNECTION_STRING"]
        client = pymongo.MongoClient(connection_string)
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"CRITICAL: Erro de conexão com o MongoDB: {e}")
        return None

@st.cache_resource
def get_users_collection():
    """Obtém a coleção de 'users' da base de dados."""
    client = get_mongo_client()
    # CORREÇÃO: Usa 'is not None' para verificar o cliente
    if client is not None:
        db = client["simulador_db"]
        return db["users"]
    return None


# --- 2. FUNÇÕES DE GESTÃO DE SENHAS ---

def verify_password(plain_password, hashed_password):
    """Verifica se uma senha em texto simples corresponde a um hash guardado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Gera um hash seguro para uma nova senha."""
    return pwd_context.hash(password)


# --- 3. FUNÇÕES DE GESTÃO DE UTILIZADORES (CRUD) ---

def fetch_all_users_for_auth():
    """Busca todos os utilizadores e formata-os para o streamlit-authenticator."""
    users_collection = get_users_collection()
    credentials = {"usernames": {}}
    
    # ***** A CORREÇÃO PRINCIPAL ESTÁ AQUI *****
    # Em vez de 'if users_collection:', usamos 'if users_collection is not None:'
    if users_collection is not None:
        for user in users_collection.find({}, {"_id": 0}):
            username = user.get("username")
            if username:
                credentials["usernames"][username] = {
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "password": user.get("hashed_password"),
                    "role": user.get("role")
                }
    return credentials

def add_user(username, name, email, password, role):
    """Adiciona um novo utilizador à base de dados."""
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("A base de dados não está disponível.")
        return False
        
    if users_collection.find_one({"username": username}):
        st.warning(f"O nome de utilizador '{username}' já existe.")
        return False
    
    users_collection.insert_one({
        "username": username,
        "name": name,
        "email": email,
        "hashed_password": get_password_hash(password),
        "role": role
    })
    return True

def get_user_role(username):
    """Busca o papel (role) de um utilizador específico."""
    users_collection = get_users_collection()
    if users_collection is not None:
        user_data = users_collection.find_one({"username": username})
        return user_data.get("role") if user_data else None
    return None

def update_user_password(username, new_password):
    """Atualiza a senha de um utilizador com um novo hash."""
    users_collection = get_users_collection()
    if users_collection is None: return False
    
    new_hashed_password = get_password_hash(new_password)
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    return result.modified_count > 0

def update_user_details(username, name, email, role):
    """Atualiza os detalhes (nome, email, papel) de um utilizador."""
    users_collection = get_users_collection()
    if users_collection is None: return False
    
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"name": name, "email": email, "role": role}}
    )
    return result.modified_count > 0

def delete_user(username):
    """Remove um utilizador da base de dados."""
    users_collection = get_users_collection()
    if users_collection is None: return False
    
    if get_user_role(username) == "admin":
        if users_collection.count_documents({"role": "admin"}) <= 1:
            st.error("Não é possível excluir o único administrador do sistema.")
            return False
            
    result = users_collection.delete_one({"username": username})
    return result.deleted_count > 0

def get_all_users_for_admin_display():
    """Retorna uma lista de todos os utilizadores (sem a senha) para exibição segura."""
    users_collection = get_users_collection()
    if users_collection is not None:
        return list(users_collection.find({}, {"_id": 0, "hashed_password": 0}))
    return []
