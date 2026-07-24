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
    products = sorted({product for plan_products in plans.values() for product in plan_products})

    return {
        "_id": "global_prices",
        "PLANOS_PJ": plans,
        "CUSTOS_PJ": {
            plan: {product: 0.0 for product in plan_products}
            for plan, plan_products in plans.items()
        },
        # Instalação é uma cobrança única por veículo. O preço pode ser cobrado
        # ou isentado na proposta, porém o custo interno sempre reduz a margem.
        "INSTALACAO_PJ": {
            product: {"preco_venda": 0.0, "custo": 0.0}
            for product in products
        },
        # Custo interno único da implantação da proposta, independente da frota.
        # Esse valor torna a análise de equilíbrio por quantidade economicamente útil.
        "CUSTO_FIXO_IMPLANTACAO_PJ": 0.0,
        # Regra de negócio fixa: condições personalizadas nunca podem ficar abaixo de 30%.
        "MARGEM_MINIMA_PERSONALIZADA_PJ": 30.0,
        "CENARIOS_QUANTIDADE_PJ": [1, 5, 10, 25, 50, 100, 200],
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


def _normalize_quantity_scenarios(value: Any) -> list[int]:
    if not isinstance(value, (list, tuple, set)):
        return [1, 5, 10, 25, 50, 100, 200]
    normalized: list[int] = []
    for item in value:
        try:
            parsed = max(1, min(int(item), 100_000))
        except (TypeError, ValueError):
            continue
        if parsed not in normalized:
            normalized.append(parsed)
    return sorted(normalized) or [1, 5, 10, 25, 50, 100, 200]


def normalize_pricing_config(data: dict[str, Any] | None) -> dict[str, Any]:
    """Normaliza preços antigos e migra custos, instalação e regras PJ."""
    defaults = get_default_pricing()
    provided = deepcopy(data or {})
    result = deepcopy(defaults)

    for key, value in provided.items():
        if key not in {
            "PLANOS_PJ",
            "CUSTOS_PJ",
            "INSTALACAO_PJ",
            "PRODUTOS_PJ_DESCRICAO",
        }:
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

    all_products = sorted(
        {product for products in result["PLANOS_PJ"].values() for product in products}
    )
    raw_installation = provided.get("INSTALACAO_PJ")
    raw_installation = raw_installation if isinstance(raw_installation, dict) else {}
    normalized_installation: dict[str, dict[str, float]] = {}
    for product in all_products:
        raw_item = raw_installation.get(product)
        raw_item = raw_item if isinstance(raw_item, dict) else {}
        normalized_installation[product] = {
            "preco_venda": _as_non_negative_float(raw_item.get("preco_venda", 0.0)),
            "custo": _as_non_negative_float(raw_item.get("custo", 0.0)),
        }
    result["INSTALACAO_PJ"] = normalized_installation

    result["CUSTO_FIXO_IMPLANTACAO_PJ"] = _as_non_negative_float(
        result.get("CUSTO_FIXO_IMPLANTACAO_PJ", 0.0)
    )
    # O piso é propositalmente travado em 30%, mesmo que um documento antigo
    # ou uma alteração manual no MongoDB tente gravar valor inferior.
    result["MARGEM_MINIMA_PERSONALIZADA_PJ"] = max(
        30.0,
        min(
            99.0,
            _as_non_negative_float(
                result.get("MARGEM_MINIMA_PERSONALIZADA_PJ", 30.0),
                30.0,
            ),
        ),
    )
    result["CENARIOS_QUANTIDADE_PJ"] = _normalize_quantity_scenarios(
        result.get("CENARIOS_QUANTIDADE_PJ")
    )

    result["_id"] = "global_prices"
    result["AMORTIZACAO_HARDWARE_MESES"] = max(
        1,
        int(_as_non_negative_float(result.get("AMORTIZACAO_HARDWARE_MESES", 12), 12)),
    )
    return result
