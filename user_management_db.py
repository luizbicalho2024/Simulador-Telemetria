from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, time
from typing import Any, Iterable

import pymongo
import streamlit as st
from bson import ObjectId
from passlib.context import CryptContext
from pymongo import ASCENDING, DESCENDING, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from app_core.settings import get_default_branding, normalize_branding
from config import get_default_pricing

log = logging.getLogger("SimuladorApp.database")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_NAME = "simulador_db"


def _secret(*names: str, default: Any = None) -> Any:
    for name in names:
        try:
            value = st.secrets.get(name)
        except Exception:
            value = None
        if value not in (None, ""):
            return value
    return default


@st.cache_resource(show_spinner="Conectando ao banco de dados...")
def get_mongo_client() -> pymongo.MongoClient | None:
    connection_string = _secret("MONGO_CONNECTION_STRING", "mongo_connection_string")
    if not connection_string:
        log.error("MONGO_CONNECTION_STRING não foi configurada.")
        return None

    try:
        client = pymongo.MongoClient(
            connection_string,
            serverSelectionTimeoutMS=8_000,
            connectTimeoutMS=8_000,
            socketTimeoutMS=20_000,
            maxPoolSize=20,
            minPoolSize=0,
            retryWrites=True,
            appname="simulador-telemetria",
        )
        client.admin.command("ping")
        return client
    except PyMongoError:
        log.exception("Falha ao conectar ao MongoDB.")
        return None


@st.cache_resource
def get_database() -> Database | None:
    client = get_mongo_client()
    if client is None:
        return None
    return client[DB_NAME]


@st.cache_resource
def get_collection(collection_name: str) -> Collection | None:
    database = get_database()
    return database[collection_name] if database is not None else None


@st.cache_resource
def initialize_database() -> bool:
    database = get_database()
    if database is None:
        return False

    try:
        database.users.create_index([("username", ASCENDING)], unique=True, name="uq_users_username")
        database.users.create_index([("email", ASCENDING)], sparse=True, name="ix_users_email")
        database.activity_logs.create_index([("timestamp", DESCENDING)], name="ix_logs_timestamp")
        database.activity_logs.create_index([("user", ASCENDING), ("timestamp", DESCENDING)], name="ix_logs_user_timestamp")
        database.proposals.create_index([("data_geracao", DESCENDING)], name="ix_proposals_date")
        database.proposals.create_index(
            [("empresa", ASCENDING), ("consultor", ASCENDING), ("tipo", ASCENDING), ("data_geracao", DESCENDING)],
            name="ix_proposals_lookup",
        )
        database.billing_history.create_index([("data_geracao", DESCENDING)], name="ix_billing_date")
        database.fipe_vehicles.create_index(
            [("codigoFipe", ASCENDING), ("anoModelo", ASCENDING), ("combustivel", ASCENDING)],
            unique=True,
            sparse=True,
            name="uq_fipe_vehicle",
        )
        database.system_settings.create_index([("_id", ASCENDING)], unique=True, name="uq_system_settings")
        return True
    except PyMongoError:
        log.exception("Falha ao criar índices do MongoDB.")
        return False


def get_users_collection() -> Collection | None:
    return get_collection("users")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def fetch_all_users_for_auth() -> dict[str, dict[str, dict[str, str]]]:
    users_collection = get_users_collection()
    credentials: dict[str, dict[str, dict[str, str]]] = {"usernames": {}}
    if users_collection is None:
        return credentials

    projection = {"_id": 0, "username": 1, "name": 1, "email": 1, "hashed_password": 1, "role": 1, "active": 1}
    for user in users_collection.find({"active": {"$ne": False}}, projection):
        username = str(user.get("username") or "").strip().lower()
        hashed_password = user.get("hashed_password")
        if username and hashed_password:
            credentials["usernames"][username] = {
                "name": str(user.get("name") or username),
                "email": str(user.get("email") or ""),
                "password": str(hashed_password),
                "role": str(user.get("role") or "user"),
            }
    return credentials


def add_user(username: str, name: str, email: str, password: str, role: str) -> bool:
    users_collection = get_users_collection()
    if users_collection is None:
        return False

    username = username.strip().lower()
    email = email.strip().lower()
    name = name.strip()
    role = role if role in {"admin", "user"} else "user"
    if not username or not name or not email or len(password) < 8:
        return False

    try:
        users_collection.insert_one(
            {
                "username": username,
                "name": name,
                "email": email,
                "hashed_password": get_password_hash(password),
                "role": role,
                "active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        )
        return True
    except DuplicateKeyError:
        return False
    except PyMongoError:
        log.exception("Falha ao cadastrar usuário.")
        return False


def get_user_role(username: str) -> str | None:
    users_collection = get_users_collection()
    if users_collection is None:
        return None
    user = users_collection.find_one({"username": username.strip().lower()}, {"role": 1, "active": 1})
    if not user or user.get("active") is False:
        return None
    return str(user.get("role") or "user")


def update_user_password(username: str, new_password: str) -> bool:
    users_collection = get_users_collection()
    if users_collection is None or len(new_password) < 8:
        return False
    result = users_collection.update_one(
        {"username": username.strip().lower()},
        {"$set": {"hashed_password": get_password_hash(new_password), "updated_at": datetime.now()}},
    )
    return result.matched_count > 0


def reset_user_password_by_admin(username: str, new_password: str) -> bool:
    return update_user_password(username, new_password)


def update_user_details(username: str, name: str, email: str, role: str, active: bool = True) -> bool:
    users_collection = get_users_collection()
    if users_collection is None:
        return False
    role = role if role in {"admin", "user"} else "user"
    result = users_collection.update_one(
        {"username": username.strip().lower()},
        {
            "$set": {
                "name": name.strip(),
                "email": email.strip().lower(),
                "role": role,
                "active": bool(active),
                "updated_at": datetime.now(),
            }
        },
    )
    return result.matched_count > 0


def delete_user(username: str) -> bool:
    users_collection = get_users_collection()
    if users_collection is None:
        return False

    normalized = username.strip().lower()
    user = users_collection.find_one({"username": normalized}, {"role": 1})
    if not user:
        return False
    if user.get("role") == "admin" and users_collection.count_documents({"role": "admin", "active": {"$ne": False}}) <= 1:
        return False
    return users_collection.delete_one({"username": normalized}).deleted_count > 0


def get_all_users_for_admin_display() -> list[dict[str, Any]]:
    users_collection = get_users_collection()
    if users_collection is None:
        return []
    projection = {"_id": 0, "hashed_password": 0}
    return list(users_collection.find({}, projection).sort("name", ASCENDING))


@st.cache_data(ttl=300, show_spinner=False)
def get_pricing_config() -> dict[str, Any]:
    collection = get_collection("pricing_config")
    if collection is not None:
        config = collection.find_one({"_id": "global_prices"})
        if config:
            return config
    return get_default_pricing()


def update_pricing_config(new_config: dict[str, Any]) -> bool:
    collection = get_collection("pricing_config")
    if collection is None:
        return False
    clean_config = dict(new_config)
    clean_config.pop("_id", None)
    try:
        collection.update_one(
            {"_id": "global_prices"},
            {"$set": clean_config, "$currentDate": {"updated_at": True}},
            upsert=True,
        )
        get_pricing_config.clear()
        return True
    except PyMongoError:
        log.exception("Falha ao atualizar preços.")
        return False


def get_system_settings() -> dict[str, Any]:
    collection = get_collection("system_settings")
    if collection is not None:
        settings = collection.find_one({"_id": "global_branding"})
        if settings:
            return normalize_branding(settings)
    return get_default_branding()


def update_system_settings(settings: dict[str, Any]) -> bool:
    collection = get_collection("system_settings")
    if collection is None:
        return False
    normalized = normalize_branding(settings)
    normalized.pop("_id", None)
    try:
        collection.update_one(
            {"_id": "global_branding"},
            {"$set": normalized, "$currentDate": {"updated_at": True}},
            upsert=True,
        )
        return True
    except PyMongoError:
        log.exception("Falha ao atualizar identidade visual.")
        return False


def _update_logo(
    raw_bytes: bytes,
    mime: str,
    filename: str,
    *,
    sidebar: bool,
) -> bool:
    if not raw_bytes:
        return False

    settings = normalize_branding(get_system_settings())
    prefix = "sidebar_logo" if sidebar else "logo"
    settings.update(
        {
            f"{prefix}_base64": base64.b64encode(raw_bytes).decode("ascii"),
            f"{prefix}_mime": str(mime or "image/png"),
            f"{prefix}_filename": str(filename or "logo.png")[:255],
        }
    )
    return update_system_settings(settings)


def update_system_logo(raw_bytes: bytes, mime: str, filename: str) -> bool:
    """Atualiza a logo principal usada no login e no conteúdo do sistema."""
    return _update_logo(raw_bytes, mime, filename, sidebar=False)


def update_sidebar_logo(raw_bytes: bytes, mime: str, filename: str) -> bool:
    """Atualiza exclusivamente a logo exibida na barra lateral."""
    return _update_logo(raw_bytes, mime, filename, sidebar=True)


def _reset_logo(*, sidebar: bool) -> bool:
    settings = normalize_branding(get_system_settings())
    prefix = "sidebar_logo" if sidebar else "logo"
    settings.update(
        {
            f"{prefix}_base64": None,
            f"{prefix}_mime": None,
            f"{prefix}_filename": None,
        }
    )
    return update_system_settings(settings)


def reset_system_logo() -> bool:
    return _reset_logo(sidebar=False)


def reset_sidebar_logo() -> bool:
    return _reset_logo(sidebar=True)


def add_log(user: str, action: str, details: Any = None) -> bool:
    collection = get_collection("activity_logs")
    if collection is None:
        return False
    try:
        collection.insert_one(
            {
                "timestamp": datetime.now(),
                "user": str(user or "sistema"),
                "action": str(action),
                "details": details if details is not None else {},
            }
        )
        return True
    except PyMongoError:
        log.exception("Falha ao registrar log.")
        return False


def get_all_logs(limit: int = 2_000) -> list[dict[str, Any]]:
    collection = get_collection("activity_logs")
    if collection is None:
        return []
    safe_limit = max(1, min(int(limit), 10_000))
    return list(collection.find({}).sort("timestamp", DESCENDING).limit(safe_limit))


def upsert_proposal(proposal_data: dict[str, Any]) -> bool:
    collection = get_collection("proposals")
    if collection is None:
        return False
    try:
        now = datetime.now()
        day_start = datetime.combine(now.date(), time.min)
        day_end = datetime.combine(now.date(), time.max)
        query = {
            "empresa": str(proposal_data.get("empresa") or "").strip(),
            "consultor": str(proposal_data.get("consultor") or "").strip(),
            "tipo": str(proposal_data.get("tipo") or "").strip(),
            "data_geracao": {"$gte": day_start, "$lte": day_end},
        }
        collection.update_one(
            query,
            {
                "$set": {
                    "valor_total": float(proposal_data.get("valor_total") or 0),
                    "data_geracao": now,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "empresa": query["empresa"],
                    "consultor": query["consultor"],
                    "tipo": query["tipo"],
                    "created_at": now,
                },
            },
            upsert=True,
        )
        return True
    except (PyMongoError, TypeError, ValueError):
        log.exception("Falha ao salvar proposta.")
        return False


# Compatibilidade com versões anteriores do projeto.
def log_proposal(proposal_data: dict[str, Any]) -> bool:
    return upsert_proposal(proposal_data)


def get_all_proposals(limit: int = 5_000) -> list[dict[str, Any]]:
    collection = get_collection("proposals")
    if collection is None:
        return []
    safe_limit = max(1, min(int(limit), 20_000))
    return list(collection.find({}).sort("data_geracao", DESCENDING).limit(safe_limit))


def get_recent_proposals(limit: int = 10) -> list[dict[str, Any]]:
    return get_all_proposals(limit=limit)


def delete_proposal(proposal_id: str) -> bool:
    collection = get_collection("proposals")
    if collection is None:
        return False
    try:
        return collection.delete_one({"_id": ObjectId(proposal_id)}).deleted_count > 0
    except (PyMongoError, ValueError):
        log.exception("Falha ao excluir proposta.")
        return False


def get_dashboard_summary() -> dict[str, Any]:
    collection = get_collection("proposals")
    users = get_users_collection()
    if collection is None:
        return {"total_proposals": 0, "total_value": 0.0, "active_users": 0, "last_proposal": None}

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_proposals": {"$sum": 1},
                "total_value": {"$sum": "$valor_total"},
                "last_proposal": {"$max": "$data_geracao"},
            }
        }
    ]
    aggregated = list(collection.aggregate(pipeline))
    summary = aggregated[0] if aggregated else {}
    return {
        "total_proposals": int(summary.get("total_proposals", 0)),
        "total_value": float(summary.get("total_value", 0.0)),
        "active_users": users.count_documents({"active": {"$ne": False}}) if users is not None else 0,
        "last_proposal": summary.get("last_proposal"),
    }


def log_faturamento(faturamento_data: dict[str, Any]) -> bool:
    collection = get_collection("billing_history")
    if collection is None:
        return False
    try:
        document = dict(faturamento_data)
        document["data_geracao"] = datetime.now()
        document["gerado_por"] = st.session_state.get("name", "N/A")
        collection.insert_one(document)
        add_log(
            st.session_state.get("username", "sistema"),
            "Exportou e salvou faturamento",
            {"cliente": document.get("cliente"), "valor": document.get("valor_total")},
        )
        return True
    except PyMongoError:
        log.exception("Falha ao salvar histórico de faturamento.")
        return False


def get_billing_history(limit: int = 5_000) -> list[dict[str, Any]]:
    collection = get_collection("billing_history")
    if collection is None:
        return []
    return list(collection.find({}).sort("data_geracao", DESCENDING).limit(max(1, min(limit, 20_000))))


def delete_billing_history(history_id: str) -> bool:
    collection = get_collection("billing_history")
    if collection is None:
        return False
    try:
        return collection.delete_one({"_id": ObjectId(history_id)}).deleted_count > 0
    except (PyMongoError, ValueError):
        log.exception("Falha ao excluir histórico de faturamento.")
        return False


def get_fipe_collection() -> Collection | None:
    return get_collection("fipe_vehicles")


def save_fipe_data(vehicle_data_list: Iterable[dict[str, Any]]) -> bool:
    collection = get_fipe_collection()
    if collection is None:
        return False

    operations: list[UpdateOne] = []
    for source in vehicle_data_list:
        vehicle = dict(source)
        code = vehicle.get("codigoFipe") or vehicle.get("CodigoFipe")
        year = vehicle.get("anoModelo") or vehicle.get("AnoModelo")
        fuel = vehicle.get("combustivel") or vehicle.get("Combustivel") or ""
        if not code or year is None:
            continue
        vehicle.update(
            {
                "codigoFipe": code,
                "anoModelo": year,
                "combustivel": fuel,
                "modelo": vehicle.get("modelo") or vehicle.get("Modelo") or "",
                "marca": vehicle.get("marca") or vehicle.get("Marca") or "",
                "valor": vehicle.get("valor") or vehicle.get("Valor") or "",
                "mesReferencia": vehicle.get("mesReferencia") or vehicle.get("MesReferencia") or "",
                "updated_at": datetime.now(),
            }
        )
        operations.append(
            UpdateOne(
                {"codigoFipe": code, "anoModelo": year, "combustivel": fuel},
                {"$set": vehicle},
                upsert=True,
            )
        )

    if not operations:
        return False
    try:
        collection.bulk_write(operations, ordered=False)
        return True
    except PyMongoError:
        log.exception("Falha ao salvar dados FIPE.")
        return False


def search_vehicle_in_db(model_name: str, limit: int = 200) -> list[dict[str, Any]]:
    collection = get_fipe_collection()
    if collection is None:
        return []
    term = re.escape(model_name.strip())
    if not term:
        return []
    query = {"modelo": {"$regex": term, "$options": "i"}}
    return list(collection.find(query).sort("anoModelo", DESCENDING).limit(max(1, min(limit, 1_000))))
