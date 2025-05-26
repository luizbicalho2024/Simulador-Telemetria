# user_management_db.py
import streamlit as st
from pymongo import MongoClient, errors as pymongo_errors
from streamlit_authenticator.utilities.hasher import Hasher # Importação correta
import certifi 

# --- Configurações do Banco de Dados ---
@st.cache_resource(show_spinner="Conectando ao Banco de Dados...")
def get_mongo_client():
    print("INFO_LOG (user_management_db.py): get_mongo_client() chamado.")
    if "MONGO_CONNECTION_STRING" not in st.secrets:
        st.error("CONFIGURAÇÃO CRÍTICA AUSENTE (user_management_db.py): 'MONGO_CONNECTION_STRING' não definida nos segredos.")
        print("CRITICAL_ERROR_LOG (user_management_db.py): MONGO_CONNECTION_STRING not found in Streamlit Cloud secrets.")
        return None
    
    CONNECTION_STRING = st.secrets["MONGO_CONNECTION_STRING"]
    
    try:
        print("INFO_LOG (user_management_db.py): Tentando conectar ao MongoDB com PyMongo...")
        client = MongoClient(
            CONNECTION_STRING,
            tlsCAFile=certifi.where(), 
            serverSelectionTimeoutMS=25000, 
            socketTimeoutMS=25000,          
            connectTimeoutMS=25000          
            # , tlsAllowInvalidCertificates=True # MANTENHA COMENTADO EM PRODUÇÃO
        )
        client.admin.command('ping') 
        print("INFO_LOG (user_management_db.py): Conexão com MongoDB Atlas bem-sucedida.")
        return client
    except pymongo_errors.ConfigurationError as ce:
        st.error(f"ERRO DE CONFIGURAÇÃO DO PYMONGO (user_management_db.py): {ce}")
        print(f"PYMONGO_CONFIG_ERROR_LOG (user_management_db.py): {ce}")
        return None
    except pymongo_errors.ServerSelectionTimeoutError as sste:
        st.error(f"TIMEOUT AO CONECTAR AO MONGODB (user_management_db.py): {sste}")
        print(f"MONGODB_TIMEOUT_ERROR_LOG (user_management_db.py): {sste}")
        return None
    except Exception as e:
        st.error(f"ERRO GERAL AO CONECTAR AO MONGODB (user_management_db.py): {e}")
        print(f"MONGODB_GENERAL_CONNECTION_ERROR_LOG (user_management_db.py): {e}, Type: {type(e)}")
        return None

@st.cache_resource
def get_users_collection():
    print("INFO_LOG (user_management_db.py): get_users_collection() chamado.")
    client = get_mongo_client()
    if client is None:
        print("WARN_LOG (user_management_db.py - get_users_collection): Cliente MongoDB é None.")
        return None
    try:
        db_name = st.secrets.get("MONGO_DB_NAME", "simulador_db") 
        collection_name = st.secrets.get("MONGO_USERS_COLLECTION", "users")
        
        db = client[db_name]
        users_collection = db[collection_name]
        print(f"INFO_LOG (user_management_db.py): Acessando DB: '{db_name}', Coleção: '{collection_name}'")
        return users_collection
    except Exception as e:
        st.error(f"ERRO ao obter coleção '{collection_name}' do DB '{db_name}' (user_management_db.py): {e}")
        print(f"GET_COLLECTION_ERROR_LOG (user_management_db.py): DB='{db_name}', Collection='{collection_name}', Error: {e}")
        return None

def fetch_all_users_for_auth():
    print("INFO_LOG (user_management_db.py): fetch_all_users_for_auth() chamado.")
    users_collection = get_users_collection()
    default_credentials = {"usernames": {}} 
    if users_collection is None:
        print("WARN_LOG (user_management_db.py - fetch_all_users): Coleção não disponível. Retornando credenciais vazias.")
        return default_credentials
    try:
        users_from_db = list(users_collection.find({}))
        if not users_from_db:
            print("INFO_LOG (user_management_db.py - fetch_all_users): Nenhum usuário no banco.")
    except Exception as e:
        st.error(f"ERRO ao buscar usuários do DB (fetch_all_users_for_auth): {e}")
        print(f"FETCH_USERS_DB_ERROR_LOG (user_management_db.py): {e}")
        return default_credentials
    credentials = {"usernames": {}}
    for user_doc in users_from_db:
        if not all(key in user_doc for key in ["username", "name", "hashed_password", "role"]):
            print(f"WARN_LOG (user_management_db.py - fetch_all_users): Usuário com dados incompletos (ID: {user_doc.get('_id', 'N/A')}).")
            continue
        credentials["usernames"][user_doc["username"]] = {
            "name": user_doc["name"],
            "email": user_doc.get("email", ""),
            "password": user_doc["hashed_password"], # Este é o hash armazenado
            "role": user_doc["role"]
        }
    print(f"INFO_LOG (user_management_db.py - fetch_all_users): {len(credentials['usernames'])} usuários carregados.")
    return credentials

def get_user_hashed_password(username: str):
    """Busca o hash da senha de um usuário específico."""
    users_collection = get_users_collection()
    if users_collection is None or not username:
        return None
    try:
        user_data = users_collection.find_one({"username": username}, {"hashed_password": 1})
        return user_data.get("hashed_password") if user_data else None
    except Exception as e:
        print(f"GET_HASHED_PASSWORD_ERROR_LOG (user_management_db.py): User='{username}', Error: {e}")
        return None

def update_user_password_manual(username: str, new_plain_password: str):
    """Atualiza a senha de um usuário (usado para alteração manual pelo usuário)."""
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (update_user_password_manual): Coleção de usuários indisponível.")
        return False
    if not new_plain_password:
        st.warning("Nova senha não pode ser vazia.")
        return False
    try:
        new_hashed_password = Hasher([new_plain_password]).generate()[0]
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        if result.modified_count > 0:
            print(f"INFO_LOG (user_management_db.py - update_user_password_manual): Senha para '{username}' atualizada manualmente.")
            return True
        elif result.matched_count > 0 : # Usuário encontrado mas senha não mudou (pode ser a mesma)
            print(f"INFO_LOG (user_management_db.py - update_user_password_manual): Senha para '{username}' não modificada (pode ser a mesma), mas usuário existe.")
            return True # Considera sucesso se a operação foi "concluída"
        else:
            st.warning(f"Usuário '{username}' não encontrado para atualização de senha manual.")
            return False
    except Exception as e:
        st.error(f"ERRO ao atualizar senha manualmente para '{username}': {e}")
        print(f"UPDATE_PASSWORD_MANUAL_ERROR_LOG (user_management_db.py): User='{username}', Error: {e}")
        return False


def get_user_role(username: str):
    # ... (código como antes) ...
    users_collection = get_users_collection()
    if users_collection is None or not username: return None
    try:
        user_data = users_collection.find_one({"username": username})
        role = user_data.get("role") if user_data else None
        # print(f"INFO_LOG (user_management_db.py - get_user_role): Role para '{username}': {role}") # Removido para reduzir logs repetitivos
        return role
    except Exception as e:
        print(f"GET_ROLE_ERROR_LOG (user_management_db.py): User='{username}', Error: {e}")
        return None


def add_user(username: str, name: str, email: str, plain_password: str, role: str):
    # ... (código como antes) ...
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (add_user): Coleção de usuários indisponível.")
        return False
    try:
        if users_collection.find_one({"username": username}):
            st.warning(f"Usuário '{username}' já existe.")
            return False
        hashed_password = Hasher([plain_password]).generate()[0]
        user_doc = {"username": username, "name": name, "email": email, "hashed_password": hashed_password, "role": role}
        users_collection.insert_one(user_doc)
        st.success(f"Usuário '{username}' cadastrado!")
        print(f"INFO_LOG (user_management_db.py - add_user): Usuário '{username}' adicionado.")
        return True
    except Exception as e:
        st.error(f"ERRO ao cadastrar usuário '{username}': {e}")
        print(f"ADD_USER_ERROR_LOG (user_management_db.py): User='{username}', Error: {e}")
        return False

def update_user_details(username: str, new_name: str, new_email: str, new_role: str):
    # ... (código como antes) ...
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (update_user_details): Coleção de usuários indisponível.")
        print("ERROR_LOG (user_management_db.py - update_user_details): Collection is None.")
        return False
    
    update_fields = {}
    if new_name is not None: update_fields["name"] = new_name 
    if new_email is not None: update_fields["email"] = new_email 
    if new_role is not None: update_fields["role"] = new_role

    if not update_fields: 
        st.info(f"Nenhum dado novo fornecido para o usuário '{username}'.")
        return True 

    try:
        print(f"INFO_LOG (user_management_db.py - update_user_details): Atualizando '{username}' com: {update_fields}")
        result = users_collection.update_one(
            {"username": username}, 
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            st.warning(f"Usuário '{username}' não encontrado para atualização.")
            print(f"WARN_LOG (user_management_db.py - update_user_details): Usuário '{username}' não encontrado (matched_count=0).")
            return False
        if result.modified_count > 0:
            st.success(f"Detalhes do usuário '{username}' atualizados.")
            print(f"INFO_LOG (user_management_db.py - update_user_details): Usuário '{username}' atualizado (modified_count > 0).")
            return True
        else: 
            st.info(f"Nenhuma alteração efetiva nos dados do usuário '{username}'.")
            print(f"INFO_LOG (user_management_db.py - update_user_details): Usuário '{username}' encontrado, mas modified_count é 0.")
            return True 
            
    except Exception as e:
        st.error(f"ERRO ao atualizar detalhes do usuário '{username}': {e}")
        print(f"ERROR_LOG (user_management_db.py - update_user_details): User='{username}', Error: {e}")
        return False

def delete_user(username: str):
    # ... (código como antes) ...
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
    # ... (código como antes, já usa Hasher) ...
    users_collection = get_users_collection()
    if users_collection is None:
        st.error("FALHA (update_user_password_by_admin): Coleção de usuários indisponível.")
        print("ERROR_LOG (user_management_db.py - update_user_password_by_admin): Collection is None.")
        return False
    if not plain_password: 
        st.warning("A nova senha não pode ser vazia.")
        return False
    try:
        hashed_password = Hasher([plain_password]).generate()[0]
        print(f"INFO_LOG (user_management_db.py - update_user_password_by_admin): Tentando redefinir senha para '{username}'.")
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"hashed_password": hashed_password}}
        )
        
        if result.matched_count == 0:
            st.warning(f"Usuário '{username}' não encontrado para redefinição de senha.")
            print(f"WARN_LOG (user_management_db.py - update_user_password_by_admin): Usuário '{username}' não encontrado.")
            return False
        if result.modified_count > 0:
            st.success(f"Senha do usuário '{username}' redefinida com sucesso.")
            print(f"INFO_LOG (user_management_db.py - update_user_password_by_admin): Senha para '{username}' atualizada.")
            return True
        else:
            st.info(f"Senha do usuário '{username}' não foi alterada (a nova senha pode ser igual à anterior).")
            print(f"INFO_LOG (user_management_db.py - update_user_password_by_admin): Senha para '{username}' não modificada (modified_count=0), mas usuário existe.")
            return True 
            
    except Exception as e:
        st.error(f"ERRO ao redefinir senha do usuário '{username}': {e}")
        print(f"ERROR_LOG (user_management_db.py - update_user_password_by_admin): User='{username}', Error: {e}")
        return False

# Removida a função update_user_password_self, pois a lógica manual a substituirá
# Se você ainda usar o authenticator.change_password() e ele funcionar,
# você precisaria de uma função para persistir o hash que ele gera,
# mas como estamos contornando o change_password() da biblioteca, esta não é mais necessária.

def get_all_users_for_admin_display():
    # ... (código como antes) ...
    users_collection = get_users_collection()
    if users_collection is None:
        return []
    try:
        return list(users_collection.find({}, {"_id": 0, "hashed_password": 0}))
    except Exception as e:
        st.error(f"ERRO ao buscar lista de usuários para admin: {e}")
        return []