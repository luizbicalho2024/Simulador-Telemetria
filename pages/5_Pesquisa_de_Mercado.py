# pages/Pesquisa_de_Mercado.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Pesquisa de Mercado",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. DADOS CENTRALIZADOS (CÓPIA FIEL DOS SEUS FICHEIROS) ---
MARKET_DATA = {
    "precos_nacionais": [
        {'Empresa': 'VERDIO (Referência)', 'Instalação (GPRS)': 'Alguns casos - R$ 50,00', 'Mensalidade (GPRS)': 'A partir de R$ 40,00', 'Instalação (Satelital)': 'Alguns casos - R$ 50,00', 'Mensalidade (Satelital)': 'A partir de R$ 107,67'},
        {'Empresa': 'Sascar', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 79,90', 'Instalação (Satelital)': 'R$ 824,19', 'Mensalidade (Satelital)': 'R$ 193,80'},
        {'Empresa': 'Omnilink', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 89,90', 'Instalação (Satelital)': 'R$ 554,00', 'Mensalidade (Satelital)': 'R$ 193,80'},
        {'Empresa': 'Onixsat', 'Instalação (GPRS)': '–', 'Mensalidade (GPRS)': '–', 'Instalação (Satelital)': 'R$ 0,00', 'Mensalidade (Satelital)': 'R$ 120,00'},
        {'Empresa': 'Veltec', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 110,00', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'Positron', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 75,00', 'Instalação (Satelital)': 'R$ 256,27', 'Mensalidade (Satelital)': 'R$ 191,05'},
        {'Empresa': 'Autotrac', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 99,90', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'Maxtrack', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 59,90', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
    ],
    "precos_regionais": [
        {'Empresa': 'VERDIO (Referência)', 'Instalação (GPRS)': 'Alguns casos - R$ 50,00', 'Mensalidade (GPRS)': 'A partir de R$ 40,00', 'Instalação (Satelital)': 'Alguns casos - R$ 50,00', 'Mensalidade (Satelital)': 'A partir de R$ 107,67'},
        {'Empresa': 'Elite Rastro', 'Instalação (GPRS)': 'R$ 30,00', 'Mensalidade (GPRS)': 'R$ 50,00', 'Instalação (Satelital)': 'R$ 900,00', 'Mensalidade (Satelital)': 'R$ 180,00'},
        {'Empresa': 'NJ Rastreamento', 'Instalação (GPRS)': 'R$ 120,00', 'Mensalidade (GPRS)': 'R$ 75,00', 'Instalação (Satelital)': 'R$ 650,00', 'Mensalidade (Satelital)': 'R$ 170,00'},
        {'Empresa': 'TK Rastreadores', 'Instalação (GPRS)': 'R$ 80,00', 'Mensalidade (GPRS)': 'R$ 69,90', 'Instalação (Satelital)': 'R$ 980,00', 'Mensalidade (Satelital)': 'R$ 150,00'},
        {'Empresa': 'vtrackrastreamento', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 50,00', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'rastrek', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 60,00', 'Instalação (Satelital)': 'R$ 0,00', 'Mensalidade (Satelital)': 'R$ 130,00'},
        {'Empresa': 'Pro Lion', 'Instalação (GPRS)': 'R$ 99,90', 'Mensalidade (GPRS)': 'R$ 49,90 - R$ 69,90', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'Impacto Rast.', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 45,00', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
    ],
    "funcionalidades_nacionais": [
        {'Empresa': 'VERDIO (Rovema)', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '✅ Sim', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Sascar', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Omnilink', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Onixsat', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Veltec', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Positron', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❔ Opcional', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Autotrac', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Maxtrack', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
    ],
    "funcionalidades_regionais": [
        {'Empresa': 'VERDIO (Rovema)', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '✅ Sim', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Elite Rastro', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'NJ Rastreamento', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'TK Rastreadores', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Suporte 24h': '❔ Comercial', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Vtrack Rastreamento', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Rastrek', 'Telemetria (CAN)': '❔ Parcial', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Pro Lion', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Impacto Rast.', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
    ]
}

# --- 3. CONVERSÃO PARA DATAFRAMES ---
df_preco_nacionais = pd.DataFrame(MARKET_DATA["precos_nacionais"])
df_preco_regionais = pd.DataFrame(MARKET_DATA["precos_regionais"])
df_funci_nacionais = pd.DataFrame(MARKET_DATA["funcionalidades_nacionais"])
df_funci_regionais = pd.DataFrame(MARKET_DATA["funcionalidades_regionais"])

# --- 4. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>Pesquisa de Mercado e Concorrentes</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SEÇÃO MERCADO-ALVO E DIFERENCIAIS ---
st.subheader("Nosso Mercado-Alvo")
st.markdown("""
| Segmento | Dor Principal | Oportunidade para o Verdio |
|---|---|---|
| **Locadoras de Veículos** | Risco e Descontrole do Ativo: Uso indevido, sinistros e a dificuldade de garantir a segurança do patrimônio. | Oferecer uma solução de proteção do ativo e segurança jurídica. |
| **Transportadoras** | Altos Custos Operacionais e Riscos Trabalhistas: Consumo excessivo de combustível, acidentes. | Entregar uma plataforma de eficiência operacional e compliance, com ROI claro. |
""")
st.markdown("---")

st.subheader("Nossos Diferenciais Competitivos")
st.info("📊 **Gestão Financeira Integrada (ROI Claro):** Transformamos dados operacionais em indicadores financeiros.")
st.info("👮‍♂️ **Segurança Jurídica e Compliance:** Integramos a gestão da Lei do Motorista com o sensor de fadiga.")
st.info("💡 **Inovação Acessível:** Oferecemos tecnologias de ponta como parte do nosso pacote padrão.")
st.markdown("---")


# --- 5. EXIBIÇÃO DAS TABELAS ---
st.subheader("Análise de Preços")
with st.expander("Comparativo de Preços - Concorrentes Nacionais", expanded=True):
    st.dataframe(df_preco_nacionais, hide_index=True, use_container_width=True)

with st.expander("Comparativo de Preços - Concorrentes Regionais", expanded=True):
    st.dataframe(df_preco_regionais, hide_index=True, use_container_width=True)

st.markdown("---")

st.subheader("Análise de Funcionalidades")
with st.expander("Comparativo de Funcionalidades - Concorrentes Nacionais", expanded=True):
    st.dataframe(df_funci_nacionais, hide_index=True, use_container_width=True)

with st.expander("Comparativo de Funcionalidades - Concorrentes Regionais", expanded=True):
    st.dataframe(df_funci_regionais, hide_index=True, use_container_width=True)
