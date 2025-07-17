# tests/test_calculations.py
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# Simula as constantes para o teste
AMORTIZACAO_HARDWARE_MESES = Decimal("12")

def test_arredondamento_licitacao():
    """
    Testa a regra de arredondamento para o cálculo do preço de venda na licitação.
    Custo do equipamento: 400
    Custo mensal (arredondado para baixo): 400 / 12 = 33.33
    Preço de venda (com 30% de margem): 33.33 * 1.3 = 43.329, deve ser arredondado para 43.33
    """
    custo_equipamento = Decimal("400")
    margem = Decimal("0.30")
    
    # 1. Cálculo do custo mensal (com ROUND_DOWN)
    custo_mensal = (custo_equipamento / AMORTIZACAO_HARDWARE_MESES).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )
    assert custo_mensal == Decimal("33.33")
    
    # 2. Cálculo do preço de venda (com ROUND_HALF_UP)
    preco_venda = (custo_mensal * (1 + margem)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    
    # 3. Verificação (Assert)
    # O teste passa se o resultado for o esperado.
    assert preco_venda == Decimal("43.33")
