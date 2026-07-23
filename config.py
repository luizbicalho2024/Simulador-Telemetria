from __future__ import annotations

from copy import deepcopy
from typing import Any


def get_default_pricing() -> dict[str, Any]:
    """Retorna a configuração comercial usada antes da primeira gravação no MongoDB."""
    plans = {
        "12 Meses": {
            "GPRS / Gsm": 80.88,
            "Satélite": 193.80,
            "Identificador de Motorista / RFID": 19.25,
            "Leitor de Rede CAN / Telemetria": 75.25,
            "Videomonitoramento + DMS + ADAS": 409.11,
        },
        "24 Meses": {
            "GPRS / Gsm": 53.92,
            "Satélite": 129.20,
            "Identificador de Motorista / RFID": 12.83,
            "Leitor de Rede CAN / Telemetria": 50.17,
            "Videomonitoramento + DMS + ADAS": 272.74,
        },
        "36 Meses": {
            "GPRS / Gsm": 44.93,
            "Satélite": 107.67,
            "Identificador de Motorista / RFID": 10.69,
            "Leitor de Rede CAN / Telemetria": 41.81,
            "Videomonitoramento + DMS + ADAS": 227.28,
        },
    }

    return {
        "_id": "global_prices",
        "PLANOS_PJ": plans,
        # Custos mensais unitários por produto e prazo. Permanecem em zero até o
        # administrador cadastrar os custos reais da operação.
        "CUSTOS_PJ": {
            plan: {product: 0.0 for product in products}
            for plan, products in plans.items()
        },
        "PRODUTOS_PJ_DESCRICAO": {
            "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G.",
            "Satélite": "Equipamento de rastreamento via satélite para cobertura total.",
            "Identificador de Motorista / RFID": "Identificação automática de motoristas via RFID.",
            "Leitor de Rede CAN / Telemetria": "Leitura de dados avançados de telemetria via rede CAN do veículo.",
            "Videomonitoramento + DMS + ADAS": "Videomonitoramento com câmeras, alertas de fadiga e assistência ao motorista.",
        },
        "PRECOS_PF": {
            "GPRS / Gsm": 970.56,
            "Satelital": 2325.60,
        },
        "TAXAS_PARCELAMENTO_PF": {
            "2": 0.05,
            "3": 0.065,
            "4": 0.08,
            "5": 0.09,
            "6": 0.10,
            "7": 0.11,
            "8": 0.12,
            "9": 0.13,
            "10": 0.15,
            "11": 0.16,
            "12": 0.18,
        },
        "PRECO_CUSTO_LICITACAO": {
            "Rastreador GPRS/GSM 2G": 300.00,
            "Rastreador GPRS/GSM 4G": 400.00,
            "Rastreador Satelital": 900.00,
            "Telemetria/CAN": 600.00,
            "RFID - ID Motorista": 153.00,
        },
        "AMORTIZACAO_HARDWARE_MESES": 12,
    }


def _as_non_negative_float(value: Any, fallback: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return fallback
    return max(0.0, parsed)


def normalize_pricing_config(data: dict[str, Any] | None) -> dict[str, Any]:
    """Normaliza preços antigos e cria a estrutura de custos PJ sem KeyError.

    Produtos e planos já cadastrados no MongoDB são preservados. Quando um custo
    ainda não existe, ele é inicializado em zero para que o administrador possa
    informar o valor real antes de usar a análise de margem.
    """
    defaults = get_default_pricing()
    provided = deepcopy(data or {})
    result = deepcopy(defaults)

    for key, value in provided.items():
        if key not in {"PLANOS_PJ", "CUSTOS_PJ", "PRODUTOS_PJ_DESCRICAO"}:
            result[key] = deepcopy(value)

    raw_plans = provided.get("PLANOS_PJ")
    if isinstance(raw_plans, dict) and raw_plans:
        result["PLANOS_PJ"] = {}
        for plan, products in raw_plans.items():
            if not isinstance(products, dict):
                continue
            normalized_products: dict[str, float] = {}
            for product, price in products.items():
                name = str(product or "").strip()
                if name:
                    normalized_products[name] = _as_non_negative_float(price)
            if normalized_products:
                result["PLANOS_PJ"][str(plan)] = normalized_products

    descriptions = deepcopy(defaults["PRODUTOS_PJ_DESCRICAO"])
    raw_descriptions = provided.get("PRODUTOS_PJ_DESCRICAO")
    if isinstance(raw_descriptions, dict):
        for product, description in raw_descriptions.items():
            name = str(product or "").strip()
            if name:
                descriptions[name] = str(description or name).strip()
    for products in result["PLANOS_PJ"].values():
        for product in products:
            descriptions.setdefault(product, product)
    result["PRODUTOS_PJ_DESCRICAO"] = descriptions

    raw_costs = provided.get("CUSTOS_PJ")
    raw_costs = raw_costs if isinstance(raw_costs, dict) else {}
    normalized_costs: dict[str, dict[str, float]] = {}
    for plan, products in result["PLANOS_PJ"].items():
        plan_costs = raw_costs.get(plan)
        plan_costs = plan_costs if isinstance(plan_costs, dict) else {}
        normalized_costs[plan] = {
            product: _as_non_negative_float(plan_costs.get(product, 0.0))
            for product in products
        }
    result["CUSTOS_PJ"] = normalized_costs

    result["_id"] = "global_prices"
    result["AMORTIZACAO_HARDWARE_MESES"] = max(
        1,
        int(_as_non_negative_float(result.get("AMORTIZACAO_HARDWARE_MESES", 12), 12)),
    )
    return result
