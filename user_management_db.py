# user_management_db.py
import streamlit as st
from pymongo import MongoClient, errors as pymongo_errors
from streamlit_authenticator.utilities.hasher import Hasher # CORREÇÃO: Importação direta do Hasher
import certifi # Para tlsCAFile

# --- Configurações do Banco de Dados ---
@st.cache_resource(show_spinner="Conectando ao Banco de Dados...")
def get_mongo_client():
    """Retorna um cliente MongoDB conectado ou None em caso de falha."""
    if "MONGO_CONNECTION_STRING" not in st.secrets:
        st.error("CRÍTICO (user_management_db.py): 'MONGO_CONNECTION_STRING' não encontrada em .streamlit/secrets.toml.")
        return None
    
    CONNECTION_STRING = st.secrets["MONGO_CONNECTION_STRING"]
    
    try:
        client = MongoClient(
            CONNECTION_STRING,
            tlsCAFile=certifi.where(), # Tenta usar certificados do pacote certifi
            serverSelectionTimeoutMS=20000, # Timeout para seleção do servidor em ms
            socketTimeoutMS=20000,          # Timeout para operações de socket
            connectTimeoutMS=20000          # Timeout para estabelecer a conexão inicial
            # --- OPÇÃO DE TESTE PARA PROBLEMAS DE SSL (INSEGURO!) ---
            # Descomente a linha abaixo APENAS para teste se suspeitar de problemas de validação de certificado.
            # Lembre-se de comentar novamente depois. NÃO USE EM PRODUÇÃO.
            # , tlsAllowInvalidCertificates=True
        )
        client.admin.command('ping') # Testa a conexão para confirmar
        print("INFO (user_management_db.py): Conexão com MongoDB bem-sucedida.")
        return client
    except pymongo_errors.ConfigurationError as ce:
        st.error(f"ERRO DE CONFIGURAÇÃO DO PYMONGO (user_management_db.py): {ce}")
        st.error("Verifique a formatação da sua MONGO_CONNECTION_STRING.")
        return None
    except pymongo_errors.ServerSelectionTimeoutError as sste:
        st.error(f"TIMEOUT AO CONECTAR AO MONGODB (user_management_db.py): {sste}")
        st.error("Possíveis causas: IP não liberado no MongoDB Atlas, firewall/antivírus bloqueando, problemas de rede/DNS, ou o serviço MongoDB pode estar offline/sobrecarregado.")
        return None
    except Exception as e:
        st.error(f"ERRO GERAL AO CONECTAR AO MONGODB (user_management_db.py): {e}")
        st.error(f"Tipo do erro: {type(e)}")
        return None

@st.cache_resource
def get_users_collection():
    """Retorna a coleção de usuários do MongoDB ou None em caso de falha."""
    client = get_mongo_client()
    if client is None:
        # Erro já deve ter sido logado por get_mongo_client()
        return None
    try:
        # Permite configurar nome do DB e coleção via secrets.toml, com defaults
        db_name = st.secrets.get("MONGO_DB_NAME", "simulador_db") 
        collection_name = st.secrets.get("MONGO_USERS_COLLECTION", "users")
        
        db = client[db_name]
        return db[collection_name]
    except Exception as e:
        st.error(f"ERRO ao obter coleção de usuários (user_management_db.py): {e}")
        return None

# --- Funções CRUD de Usuários ---

def fetch_all_users_for_auth():
    """Busca todos os usuários e formata para o streamlit-authenticator."""
    users_collection = get_users_collection()
    default_credentials = {"usernames": {}} 

    if users_collection is None:
        print("WARN (user_management_db.py - fetch_all_users): Coleção de usuários não disponível.")
        return default_credentials

    try:
        users_from_db = list(users_collection.find({}))
        if not users_from_db:
            print("INFO (user_management_db.py - fetch_all_users): Nenhum usuário encontrado no banco de dados.")
    except Exception as e:
        st.error(f"ERRO ao buscar usuários do DB (fetch_all_users_for_auth): {e}")
        return default_credentials
        
    credentials = {"usernames": {}}
    for user in users_from_db:
        if not all(key in user for key in ["username", "name", "hashed_password", "role"]):
            st.warning(f"WARN (user_management_db.py): Usuário com dados incompletos encontrado (ID: {user.get('_id', 'N/A')}). Ignorando.")
            continue
        credentials["usernames"][user["username"]] = {
            "name": user["name"],
            "email": user.get("email", ""),
            "password": user["hashed_password"],
            "role": user["role"]
        }
    return credentials

def get_user_role(username: str):
    users_collection = get_users_collection()
    if users_collection is None or not username:
        return None
    try:
        user_data = users_collection.find_one({"username": username})
        return user_data.get("role") if user_data else None
    except Exception as e:
        st.error(f"ERRO ao buscar papel do usuário '{username}': {e}")
        return None

def add_user(username: str, name: str, email: str, plain_password: str, role: str):
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (add_user): Coleção de usuários indisponível. Verifique conexão com DB.")
        return False
    try:
        if users_collection.find_one({"username": username}):
            st.warning(f"Usuário '{username}' já existe.")
            return False

        # CORREÇÃO: Usando Hasher importado diretamente
        hashed_password = Hasher([plain_password]).generate()[0]
        user_doc = {
            "username": username, "name": name, "email": email,
            "hashed_password": hashed_password, "role": role
        }
        users_collection.insert_one(user_doc)
        st.success(f"Usuário '{username}' cadastrado com sucesso!")
        return True
    except Exception as e:
        st.error(f"ERRO ao cadastrar usuário '{username}': {e}")
        return False

def update_user_details(username: str, name: str, email: str, role: str):
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (update_user_details): Coleção de usuários indisponível.")
        return False
    try:
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"name": name, "email": email, "role": role}}
        )
        if result.modified_count > 0:
            st.success(f"Detalhes do usuário '{username}' atualizados.")
            return True
        elif users_collection.count_documents({"username": username}) > 0: # Verifica se o usuário existe
            st.info(f"Nenhuma alteração nos dados do usuário '{username}' (dados podem ser os mesmos).")
            return True 
        else:
            st.warning(f"Usuário '{username}' não encontrado para atualização.")
            return False
    except Exception as e:
        st.error(f"ERRO ao atualizar usuário '{username}': {e}")
        return False

def delete_user(username: str):
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (delete_user): Coleção de usuários indisponível.")
        return False
    try:
        is_current_user_admin = st.session_state.get("role") == "admin"
        current_logged_in_username = st.session_state.get("username")

        if is_current_user_admin and current_logged_in_username == username:
            if users_collection.count_documents({"role": "admin"}) <= 1:
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
        st.error(f"ERRO ao excluir usuário '{username}': {e}")
        return False

def update_user_password_by_admin(username: str, plain_password: str):
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (update_user_password_by_admin): Coleção de usuários indisponível.")
        return False
    try:
        # CORREÇÃO: Usando Hasher importado diretamente
        hashed_password = Hasher([plain_password]).generate()[0]
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": hashed_password}}
        )
        if result.modified_count > 0:
            st.success(f"Senha do usuário '{username}' redefinida com sucesso.")
            return True
        else: 
            st.warning(f"Senha do usuário '{username}' não alterada (usuário não encontrado ou senha igual à anterior).")
            return False
    except Exception as e:
        st.error(f"ERRO ao redefinir senha do usuário '{username}': {e}")
        return False

def update_user_password_self(username: str, new_hashed_password: str):
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (update_user_password_self): Coleção de usuários indisponível.")
        return False
    try:
        users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        return True 
    except Exception as e:
        st.error(f"ERRO ao salvar sua nova senha no banco: {e}")
        return False

def get_all_users_for_admin_display():
    users_collection = get_users_collection()
    if users_collection is None:
        return []
    try:
        return list(users_collection.find({}, {"_id": 0, "hashed_password": 0}))
    except Exception as e:
        st.error(f"ERRO ao buscar lista de usuários para admin: {e}")
        return []