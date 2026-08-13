from __future__ import annotations

import logging
import math
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore

log = logging.getLogger("SimuladorApp.financeiro")
FIREBASE_APP_NAME = "simulador-financeiro-readonly"
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


def _strip_accents(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", str(value or ""))
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


def _secret_section(name: str) -> dict[str, Any] | None:
    """
    Lê uma seção dos Secrets sem interromper a aplicação caso
    ela não exista.
    """
    try:
        return dict(st.secrets[name])
    except Exception:
        return None


def _normalize_service_account(
    section: dict[str, Any],
) -> dict[str, Any]:
    """
    Normaliza a conta de serviço do Firebase.

    Também corrige private_key armazenada com \n literal.
    """
    normalized = dict(section or {})

    private_key = normalized.get("private_key")

    if private_key is not None:
        key_text = str(private_key).strip()

        if "\\n" in key_text and "\n" not in key_text:
            key_text = key_text.replace("\\n", "\n")

        normalized["private_key"] = key_text

    return normalized


def _finance_secret_with_source() -> tuple[dict[str, Any], str]:
    """
    Procura a conta Firebase em diferentes formatos.

    Ordem:
    1. [financeiro_service_account]
    2. [service_account]

    O segundo formato é exatamente o já utilizado pelo
    projeto financeiro-verdio.
    """

    candidates = [
        (
            "financeiro_service_account",
            _secret_section("financeiro_service_account"),
        ),
        (
            "service_account",
            _secret_section("service_account"),
        ),
    ]

    incomplete = []

    for source, raw_section in candidates:

        if not raw_section:
            continue

        section = _normalize_service_account(raw_section)

        required_fields = (
            "project_id",
            "client_email",
            "private_key",
        )

        missing = [
            field
            for field in required_fields
            if not str(section.get(field) or "").strip()
        ]

        if missing:
            incomplete.append(
                f"{source}: faltando {', '.join(missing)}"
            )

            continue

        return section, source

    if incomplete:
        raise RuntimeError(
            "Foi encontrada uma conta Firebase, mas ela está "
            "incompleta. "
            + "; ".join(incomplete)
        )

    raise RuntimeError(
        "Nenhuma conta de serviço Firebase foi encontrada. "
        "O Simulador aceita [financeiro_service_account] "
        "ou [service_account]."
    )


def _finance_secret() -> dict[str, Any]:
    secret, _ = _finance_secret_with_source()

    return secret


def _safe_firebase_error(exc: BaseException) -> str:
    """
    Retorna diagnóstico sem permitir exposição da private_key.
    """
    message = str(exc or "").strip()

    if not message:
        message = exc.__class__.__name__

    if "BEGIN PRIVATE KEY" in message:
        return (
            "A chave privada Firebase não pôde ser interpretada. "
            "Verifique o campo private_key no Streamlit Secrets."
        )

    message = re.sub(
        r"-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----.*?"
        r"-----END(?: [A-Z]+)* PRIVATE KEY-----",
        "[CHAVE PRIVADA OMITIDA]",
        message,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return message[:1200]
@st.cache_resource(show_spinner="Conectando ao histórico financeiro...")
def get_finance_db():
    """
    Inicializa uma instância Firebase independente para leitura
    dos dados financeiros.
    """

    try:

        try:
            app = firebase_admin.get_app(
                FIREBASE_APP_NAME
            )

        except ValueError:

            service_account, secret_source = (
                _finance_secret_with_source()
            )

            log.info(
                "Inicializando Firebase financeiro usando Secret %s "
                "no projeto %s.",
                secret_source,
                service_account.get("project_id"),
            )

            credential = credentials.Certificate(
                service_account
            )

            app = firebase_admin.initialize_app(
                credential,
                name=FIREBASE_APP_NAME,
            )

        return firestore.client(app=app)

    except Exception as exc:

        safe_message = _safe_firebase_error(exc)

        log.exception(
            "Não foi possível inicializar o Firestore financeiro."
        )

        raise RuntimeError(
            "Não foi possível conectar ao Firestore do Financeiro. "
            f"{exc.__class__.__name__}: {safe_message}"
        ) from exc
def _stream_collection(collection_name: str, limit: int) -> list[dict[str, Any]]:
    client = get_finance_db()
    safe_limit = max(1, min(int(limit), 50000))
    result: list[dict[str, Any]] = []
    for document in client.collection(collection_name).limit(safe_limit).stream():
        data = document.to_dict() or {}
        data["_id"] = document.id
        result.append(data)
    return result


@st.cache_data(ttl=180, show_spinner=False)
def get_month_closures(limit: int = 240) -> list[dict[str, Any]]:
    try:
        return _stream_collection("billing_month_closures", limit)
    except Exception:
        log.exception("Falha ao buscar fechamentos mensais.")
        return []


@st.cache_data(ttl=180, show_spinner=False)
def get_monthly_metrics(limit: int = 30000) -> list[dict[str, Any]]:
    try:
        metrics = _stream_collection("billing_monthly_metrics", limit)
    except Exception:
        log.exception("Falha ao buscar métricas analíticas; tentando histórico legado.")
        metrics = []

    # Fallback/compatibilidade: aproveita billing_history antigo quando a projeção nova ainda
    # não tiver sido reconstruída. A projeção nova sempre prevalece para o mesmo cliente/mês.
    try:
        history = _stream_collection("billing_history", limit)
    except Exception:
        history = []

    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for item in metrics:
        period_key = _safe_text(item.get("period_key")) or period_key_from_label(item.get("periodo_relatorio", ""))
        cliente = _safe_text(item.get("cliente"))
        if not period_key or not cliente:
            continue
        normalized = dict(item)
        normalized["period_key"] = period_key
        normalized.setdefault("data_quality", "detalhado")
        normalized["source"] = "analytics"
        by_key[(period_key, cliente)] = normalized

    for record in history:
        period_key = _safe_text(record.get("period_key")) or period_key_from_label(record.get("periodo_relatorio", ""))
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
            "source": "billing_history",
        }

    return list(by_key.values())


@st.cache_data(ttl=180, show_spinner=False)
def get_terminal_snapshots(period_key: str, limit: int = 30000) -> list[dict[str, Any]]:
    if not period_key:
        return []
    try:
        client = get_finance_db()
        query = client.collection("billing_terminal_snapshots").where("period_key", "==", period_key).limit(
            max(1, min(int(limit), 50000))
        )
        result = []
        for document in query.stream():
            data = document.to_dict() or {}
            data["_id"] = document.id
            result.append(data)

        # Reprocessamentos do mesmo cliente/mês podem deixar snapshots de revisões anteriores.
        # Mantemos apenas o run atualmente apontado por billing_monthly_metrics.
        latest_runs = {
            _safe_text(item.get("cliente")): _safe_text(item.get("source_run_id"))
            for item in get_monthly_metrics()
            if _safe_text(item.get("period_key")) == period_key and _safe_text(item.get("source_run_id"))
        }
        if latest_runs:
            result = [
                item
                for item in result
                if not latest_runs.get(_safe_text(item.get("cliente")))
                or _safe_text(item.get("run_id")) == latest_runs.get(_safe_text(item.get("cliente")))
            ]
        return result
    except Exception:
        log.exception("Falha ao buscar snapshots de terminais do período %s.", period_key)
        return []


def clear_finance_cache() -> None:
    get_month_closures.clear()
    get_monthly_metrics.clear()
    get_terminal_snapshots.clear()


def connection_diagnostics() -> dict[str, Any]:
    """
    Diagnóstico seguro da integração financeira.
    """

    project_id = ""
    secret_source = "não identificado"

    try:

        secret, secret_source = (
            _finance_secret_with_source()
        )

        project_id = str(
            secret.get("project_id") or ""
        )

        client = get_finance_db()

        # Consulta mínima para validar:
        # - credencial;
        # - projeto;
        # - Firestore;
        # - permissão de leitura.
        next(
            iter(
                client.collection("billing_history")
                .limit(1)
                .stream()
            ),
            None,
        )

        return {
            "ok": True,
            "project_id": project_id,
            "secret_source": secret_source,
            "checked_at": datetime.now(timezone.utc),
        }

    except Exception as exc:

        return {
            "ok": False,
            "project_id": project_id,
            "secret_source": secret_source,
            "error_type": exc.__class__.__name__,
            "error": _safe_firebase_error(exc),
            "checked_at": datetime.now(timezone.utc),
        }
