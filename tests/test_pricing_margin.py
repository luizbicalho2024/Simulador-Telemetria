from decimal import Decimal

import pytest

from app_core.pricing import (
    gross_margin_percent,
    gross_margin_value,
    sale_price_from_margin,
)
from config import normalize_pricing_config


def test_gross_margin_value_and_percent() -> None:
    assert gross_margin_value("100", "60") == Decimal("40.00")
    assert gross_margin_percent("100", "60") == Decimal("40.00")


def test_price_from_target_margin() -> None:
    assert sale_price_from_margin("60", "40") == Decimal("100.00")


def test_price_from_margin_rejects_one_hundred_percent() -> None:
    with pytest.raises(ValueError):
        sale_price_from_margin("60", "100")


def test_old_pricing_document_receives_cost_structure() -> None:
    old_document = {
        "_id": "global_prices",
        "PLANOS_PJ": {"12 Meses": {"Produto A": 80.0}},
        "PRODUTOS_PJ_DESCRICAO": {"Produto A": "Descrição"},
    }
    normalized = normalize_pricing_config(old_document)
    assert normalized["CUSTOS_PJ"]["12 Meses"]["Produto A"] == 0.0
    assert normalized["PLANOS_PJ"]["12 Meses"]["Produto A"] == 80.0
