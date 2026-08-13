from __future__ import annotations

import logging
import math
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import streamlit as st
from pymongo import MongoClient

log = logging.getLogger("SimuladorApp.financeiro.mongo")
DEFAULT_FINANCE_DB = "financeiro_verdio"

MONTHS_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}
MONTH_LABELS = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}


def _secret_value(*names: str, default: str = "") -> str:
    for name in names:
        try:
            value = st.secrets[name]
        except Exception:
            value = None
        if value is None:
            value = os.getenv(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _strip_accents(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", str(value or ""))
        if not unicodedata.combining(ch)
    )


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none"} else text


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return float(default)
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        number = float(value)
        return float(default) if math.isnan(number) or math.isinf(number) else number
    text = _safe_text(value).replace("R$", "").replace(" ", "")
    if not text:
        return float(default)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        number = float(text)
        return float(default) if math.isnan(number) or math.isinf(number) else number
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(_safe_float(value, float(default))))
    except (TypeError, ValueError):
        return int(default)


def period_key_from_label(label: str) -> str:
    text = _strip_accents(_safe_text(label)).lower()
    match = re.search(r"\b([a-z]+)\s+de\s+(\d{4})\b", text)
    if match:
        month = MONTHS_PT.get(match.group(1))
        if month:
            return f"{int(match.group(2)):04d}-{month:02d}"
    numeric = re.search(r"\b(\d{4})[-/](\d{1,2})\b", text)
    if numeric:
        year = int(numeric.group(1))
        month = int(numeric.group(2))
        if 1 <= month <= 12:
            return f"{year:04d}-{month:02d}"
    return ""


def period_display(period_key: str) -> str:
    try:
        year, month = [int(part) for part in period_key.split("-", 1)]
        return f"{MONTH_LABELS.get(month, str(month))}/{year}"
    except Exception:
        return period_key


def previous_period(period_key: str) -> str:
    try:
        year, month = [int(part) for part in period_key.split("-", 1)]
    except Exception:
        return ""
    month -= 1
    if month == 0:
        year -= 1
        month = 12
    return f"{year:04d}-{month:02d}"


def _mongo_uri() -> str:
    uri = _secret_value(
        "FINANCEIRO_MONGO_CONNECTION_STRING",
        "MONGO_CONNECTION_STRING",
        "mongo_connection_string",
    )
    if not uri:
        raise RuntimeError(
            "MongoDB financeiro não configurado. O Simulador precisa de "
            "MONGO_CONNECTION_STRING ou FINANCEIRO_MONGO_CONNECTION_STRING."
        )
    return uri


def _finance_db_name() -> str:
    return _secret_value("FINANCEIRO_MONGO_DB", default=DEFAULT_FINANCE_DB)


@st.cache_resource(show_spinner="Conectando ao MongoDB financeiro...")
def get_finance_client() -> MongoClient:
    client = MongoClient(
        _mongo_uri(),
        serverSelectionTimeoutMS=10_000,
        connectTimeoutMS=10_000,
        socketTimeoutMS=20_000,
        retryWrites=True,
        tz_aware=True,
        appname="simulador-financeiro-readonly",
    )
    client.admin.command("ping")
    return client


@st.cache_resource(show_spinner=False)
def get_finance_db():
    return get_finance_client()[_finance_db_name()]


def _public(document: dict[str, Any]) -> dict[str, Any]:
    data = dict(document or {})
    if "_id" in data:
        data["_id"] = str(data["_id"])
    for key in list(data):
        if str(key).startswith("__mongo_"):
            data.pop(key, None)
    return data


def _stream_collection(
    collection_name: str,
    limit: int,
    *,
    query: dict[str, Any] | None = None,
    sort: list[tuple[str, int]] | None = None,
) -> list[dict[str, Any]]:
    db = get_finance_db()
    safe_limit = max(1, min(int(limit), 50_000))
    cursor = db[collection_name].find(query or {})
    if sort:
        cursor = cursor.sort(sort)
    cursor = cursor.limit(safe_limit)
    return [_public(document) for document in cursor]


@st.cache_data(ttl=180, show_spinner=False)
def get_month_closures(limit: int = 240) -> list[dict[str, Any]]:
    try:
        return _stream_collection("billing_month_closures", limit)
    except Exception:
        log.exception("Falha ao buscar fechamentos mensais no MongoDB.")
        return []


@st.cache_data(ttl=180, show_spinner=False)
def get_monthly_metrics(limit: int = 30_000) -> list[dict[str, Any]]:
    try:
        metrics = _stream_collection("billing_monthly_metrics", limit)
    except Exception:
        log.exception("Falha ao buscar métricas analíticas no MongoDB.")
        metrics = []

    # Compatibilidade: enquanto o primeiro lote ainda não criou as projeções,
    # aproveita billing_history. Após os novos uploads, analytics prevalece.
    try:
        history = _stream_collection("billing_history", limit)
    except Exception:
        history = []

    by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for item in metrics:
        period_key = _safe_text(item.get("period_key")) or period_key_from_label(
            item.get("periodo_relatorio", "")
        )
        cliente = _safe_text(item.get("cliente"))
        if not period_key or not cliente:
            continue
        normalized = dict(item)
        normalized["period_key"] = period_key
        normalized.setdefault("data_quality", "detalhado")
        normalized["source"] = "analytics_mongo"
        by_key[(period_key, cliente)] = normalized

    for record in history:
        period_key = _safe_text(record.get("period_key")) or period_key_from_label(
            record.get("periodo_relatorio", "")
        )
        cliente = _safe_text(record.get("cliente"))
        key = (period_key, cliente)
        if not period_key or not cliente or key in by_key:
            continue

        details = record.get("itens_detalhados")
        details = details if isinstance(details, list) else []
        activations = deactivations = suspensions = active_end = 0
        for detail in details:
            category = _strip_accents(_safe_text(detail.get("Categoria"))).lower()
            activated = "ativado no mes" in category or "ativado e desativado" in category
            deactivated = category == "desativado" or "ativado e desativado" in category
            suspended = category == "suspenso" or _safe_int(
                detail.get("Suspenso Dias Mes") or detail.get("Suspenso Dias Mês")
            ) > 0
            activations += int(activated)
            deactivations += int(deactivated)
            suspensions += int(suspended)
            active_end += int(not deactivated)

        if not details:
            active_end = (
                _safe_int(record.get("terminais_cheio"))
                + _safe_int(record.get("terminais_proporcional"))
                + _safe_int(record.get("terminais_suspensos"))
            )

        by_key[key] = {
            "period_key": period_key,
            "periodo_relatorio": record.get("periodo_relatorio") or period_display(period_key),
            "cliente": cliente,
            "receita": _safe_float(record.get("valor_total")),
            "veiculos_faturados": len(details) if details else max(active_end, 0),
            "veiculos_ativos_fim_mes": max(active_end, 0),
            "ativacoes": activations,
            "desativacoes": deactivations,
            "suspensoes": suspensions,
            "terminais_cheio": _safe_int(record.get("terminais_cheio")),
            "terminais_proporcional": _safe_int(record.get("terminais_proporcional")),
            "terminais_suspensos": _safe_int(record.get("terminais_suspensos")),
            "data_quality": "historico_detalhado" if details else "resumo_legado",
            "source": "billing_history_mongo",
        }

    return list(by_key.values())


@st.cache_data(ttl=180, show_spinner=False)
def get_terminal_snapshots(period_key: str, limit: int = 30_000) -> list[dict[str, Any]]:
    if not period_key:
        return []
    try:
        result = _stream_collection(
            "billing_terminal_snapshots",
            limit,
            query={"period_key": period_key},
        )

        latest_runs = {
            _safe_text(item.get("cliente")): _safe_text(item.get("source_run_id"))
            for item in get_monthly_metrics()
            if _safe_text(item.get("period_key")) == period_key
            and _safe_text(item.get("source_run_id"))
        }
        if latest_runs:
            result = [
                item
                for item in result
                if not latest_runs.get(_safe_text(item.get("cliente")))
                or _safe_text(item.get("run_id"))
                == latest_runs.get(_safe_text(item.get("cliente")))
            ]
        return result
    except Exception:
        log.exception("Falha ao buscar snapshots MongoDB do período %s.", period_key)
        return []


def clear_finance_cache() -> None:
    get_month_closures.clear()
    get_monthly_metrics.clear()
    get_terminal_snapshots.clear()


def connection_diagnostics() -> dict[str, Any]:
    try:
        client = get_finance_client()
        client.admin.command("ping")
        db = get_finance_db()
        return {
            "ok": True,
            "database": db.name,
            "billing_history": db["billing_history"].estimated_document_count(),
            "billing_monthly_metrics": db["billing_monthly_metrics"].estimated_document_count(),
            "checked_at": datetime.now(timezone.utc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "database": _finance_db_name(),
            "error_type": exc.__class__.__name__,
            "error": str(exc)[:1200],
            "checked_at": datetime.now(timezone.utc),
        }
