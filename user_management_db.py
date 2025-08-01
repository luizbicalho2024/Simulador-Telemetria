# user_management_db.py
import streamlit as st
import pymongo
from bson import ObjectId
from passlib.context import CryptContext
from datetime import datetime
from config import get_default_pricing

# --- 1. CONFIGURAÇÃO DE SEGURANÇA E CONEXÃO ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@st.cache_resource(show_spinner="A ligar à base de dados...")
def get_mongo_client():
    try:
        client = pymongo.MongoClient(st.secrets["MONGO_CONNECTION_STRING"])
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"CRITICAL: Erro de conexão com o MongoDB: {e}")
        return None

@st.cache_resource
def get_collection(collection_name: str):
    client = get_mongo_client()
    if client is not None:
        db = client["simulador_db"]
        return db[collection_name]
    return None

def get_users_collection():
    return get_collection("users")

# --- 2. FUNÇÕES DE GESTÃO DE SENHAS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)

# --- 3. FUNÇÕES DE GESTÃO DE UTILIZADORES ---
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
    if users_collection is None: return False
    if users_collection.find_one({"username": username}):
        st.warning(f"O nome de utilizador '{username}' já existe.")
        return False
    users_collection.insert_one({
        "username": username, "name": name, "email": email,
        "hashed_password": get_password_hash(password), "role": role
    })
    return True

def get_user_role(username):
    users_collection = get_users_collection()
    if users_collection is not None:
        user_data = users_collection.find_one({"username": username})
        return user_data.get("role") if user_data else None
    return None

def update_user_password(username, new_password):
    users_collection = get_users_collection()
    if users_collection is None: return False
    new_hashed_password = get_password_hash(new_password)
    result = users_collection.update_one({"username": username}, {"$set": {"hashed_password": new_hashed_password}})
    return result.modified_count > 0

def update_user_details(username, name, email, role):
    users_collection = get_users_collection()
    if users_collection is None: return False
    result = users_collection.update_one({"username": username}, {"$set": {"name": name, "email": email, "role": role}})
    return result.modified_count > 0

def delete_user(username):
    users_collection = get_users_collection()
    if users_collection is None: return False
    if get_user_role(username) == "admin" and users_collection.count_documents({"role": "admin"}) <= 1:
        st.error("Não é possível excluir o único administrador.")
        return False
    result = users_collection.delete_one({"username": username})
    return result.deleted_count > 0

def get_all_users_for_admin_display():
    users_collection = get_users_collection()
    if users_collection is not None:
        return list(users_collection.find({}, {"_id": 0, "hashed_password": 0}))
    return []

def reset_user_password_by_admin(username: str, new_password: str):
    """Permite que um admin redefina a senha de qualquer utilizador."""
    return update_user_password(username, new_password)

# --- 4. FUNÇÕES PARA GESTÃO DE PREÇOS ---
@st.cache_data(ttl=300)
def get_pricing_config():
    pricing_collection = get_collection("pricing_config")
    if pricing_collection is not None:
        config = pricing_collection.find_one({"_id": "global_prices"})
        if config:
            return config
    return get_default_pricing()

def update_pricing_config(new_config: dict):
    pricing_collection = get_collection("pricing_config")
    if pricing_collection is not None:
        try:
            new_config.pop('_id', None)
            pricing_collection.update_one(
                {"_id": "global_prices"}, {"$set": new_config}, upsert=True
            )
            st.cache_data.clear()
            return True
        except Exception as e:
            print(f"ERROR: Falha ao atualizar preços: {e}")
            return False
    return False

# --- 5. FUNÇÕES PARA DASHBOARD E LOGS ---
def add_log(user: str, action: str, details: str = ""):
    logs_collection = get_collection("activity_logs")
    if logs_collection is not None:
        try:
            log_entry = {
                "timestamp": datetime.now(), "user": user,
                "action": action, "details": details
            }
            logs_collection.insert_one(log_entry)
            return True
        except Exception as e:
            print(f"ERROR: Falha ao registar log: {e}")
            return False
    return False

def get_all_logs():
    logs_collection = get_collection("activity_logs")
    if logs_collection is not None:
        return list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1))
    return []

def log_proposal(proposal_data: dict):
    proposals_collection = get_collection("proposals")
    if proposals_collection is not None:
        try:
            proposal_data["data_geracao"] = datetime.now()
            proposals_collection.insert_one(proposal_data)
            return True
        except Exception as e:
            print(f"ERROR: Falha ao registar proposta: {e}")
            return False
    return False

def get_all_proposals():
    proposals_collection = get_collection("proposals")
    if proposals_collection is not None:
        return proposals_collection.find({}).sort("data_geracao", -1)
    return []

def delete_proposal(proposal_id: str):
    proposals_collection = get_collection("proposals")
    if proposals_collection is not None:
        try:
            result = proposals_collection.delete_one({"_id": ObjectId(proposal_id)})
            if result.deleted_count > 0:
                add_log(st.session_state["username"], "Excluiu Proposta", f"ID da proposta: {proposal_id}")
                st.toast("Proposta excluída com sucesso!", icon="🗑️")
            return result.deleted_count > 0
        except Exception as e:
            print(f"ERROR: Falha ao excluir proposta (ID: {proposal_id}): {e}")
            return False
    return False
