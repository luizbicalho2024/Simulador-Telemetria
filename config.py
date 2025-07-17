# config.py
from decimal import Decimal

# --- CONSTANTES GERAIS ---
AMORTIZACAO_HARDWARE_MESES = Decimal("12")

# --- SIMULADOR PESSOA JURÍDICA (PJ) ---
PLANOS_PJ = {
    "12 Meses": {"GPRS / Gsm": Decimal("80.88"), "Satélite": Decimal("193.80"), "Identificador de Motorista / RFID": Decimal("19.25"), "Leitor de Rede CAN / Telemetria": Decimal("75.25"), "Videomonitoramento + DMS + ADAS": Decimal("409.11")},
    "24 Meses": {"GPRS / Gsm": Decimal("53.92"), "Satélite": Decimal("129.20"), "Identificador de Motorista / RFID": Decimal("12.83"), "Leitor de Rede CAN / Telemetria": Decimal("50.17"), "Videomonitoramento + DMS + ADAS": Decimal("272.74")},
    "36 Meses": {"GPRS / Gsm": Decimal("44.93"), "Satélite": Decimal("107.67"), "Identificador de Motorista / RFID": Decimal("10.69"), "Leitor de Rede CAN / Telemetria": Decimal("41.81"), "Videomonitoramento + DMS + ADAS": Decimal("227.28")}
}
PRODUTOS_PJ_DESCRICAO = {
    "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G.",
    "Satélite": "Equipamento de rastreamento via satélite para cobertura total.",
    "Identificador de Motorista / RFID": "Identificação automática de motoristas via RFID.",
    "Leitor de Rede CAN / Telemetria": "Leitura de dados avançados de telemetria via rede CAN do veículo.",
    "Videomonitoramento + DMS + ADAS": "Sistema de videomonitoramento com câmeras, alertas de fadiga (DMS) e assistência ao motorista (ADAS)."
}

# --- SIMULADOR PESSOA FÍSICA (PF) ---
PRECOS_PF = {
    "GPRS / Gsm": Decimal("970.56"),
    "Satelital": Decimal("2325.60")
}
TAXAS_PARCELAMENTO_PF = {
    2: Decimal("0.05"), 3: Decimal("0.065"), 4: Decimal("0.08"), 5: Decimal("0.09"),
    6: Decimal("0.10"), 7: Decimal("0.11"), 8: Decimal("0.12"), 9: Decimal("0.13"),
    10: Decimal("0.15"), 11: Decimal("0.16"), 12: Decimal("0.18")
}

# --- SIMULADOR LICITAÇÃO ---
PRECO_CUSTO_LICITACAO = {
    "Rastreador GPRS/GSM 2G": Decimal("300"),
    "Rastreador GPRS/GSM 4G": Decimal("400"),
    "Rastreador Satelital": Decimal("900"),
    "Telemetria/CAN": Decimal("600"),
    "RFID - ID Motorista": Decimal("153"),
}
