# config.py
from decimal import Decimal

def get_default_pricing():
    """
    Retorna a estrutura de preços padrão da aplicação.
    Estes valores são usados como fallback se a configuração não for encontrada na base de dados.
    """
    return {
        "_id": "global_prices", # Identificador fixo para o documento na BD
        
        "PLANOS_PJ": {
            "12 Meses": {"GPRS / Gsm": 80.88, "Satélite": 193.80, "Identificador de Motorista / RFID": 19.25, "Leitor de Rede CAN / Telemetria": 75.25, "Videomonitoramento + DMS + ADAS": 409.11},
            "24 Meses": {"GPRS / Gsm": 53.92, "Satélite": 129.20, "Identificador de Motorista / RFID": 12.83, "Leitor de Rede CAN / Telemetria": 50.17, "Videomonitoramento + DMS + ADAS": 272.74},
            "36 Meses": {"GPRS / Gsm": 44.93, "Satélite": 107.67, "Identificador de Motorista / RFID": 10.69, "Leitor de Rede CAN / Telemetria": 41.81, "Videomonitoramento + DMS + ADAS": 227.28}
        },
        "PRODUTOS_PJ_DESCRICAO": {
            "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G.",
            "Satélite": "Equipamento de rastreamento via satélite para cobertura total.",
            "Identificador de Motorista / RFID": "Identificação automática de motoristas via RFID.",
            "Leitor de Rede CAN / Telemetria": "Leitura de dados avançados de telemetria via rede CAN do veículo.",
            "Videomonitoramento + DMS + ADAS": "Sistema de videomonitoramento com câmeras, alertas de fadiga (DMS) e assistência ao motorista (ADAS)."
        },
        "PRECOS_PF": {
            "GPRS / Gsm": 970.56,
            "Satelital": 2325.60
        },
        "TAXAS_PARCELAMENTO_PF": {
            "2": 0.05, "3": 0.065, "4": 0.08, "5": 0.09, "6": 0.10, 
            "7": 0.11, "8": 0.12, "9": 0.13, "10": 0.15, "11": 0.16, "12": 0.18
        },
        "PRECO_CUSTO_LICITACAO": {
            "Rastreador GPRS/GSM 2G": 300.00,
            "Rastreador GPRS/GSM 4G": 400.00,
            "Rastreador Satelital": 900.00,
            "Telemetria/CAN": 600.00,
            "RFID - ID Motorista": 153.00,
        },
        "AMORTIZACAO_HARDWARE_MESES": 12
    }
