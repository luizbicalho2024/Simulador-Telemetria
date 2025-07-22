# pages/Pesquisa_de_Mercado.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Pesquisa de Mercado",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. DADOS CENTRALIZADOS (Estrutura Completa) ---
MARKET_DATA = {
    "comparativo_features": [
        # Verdio
        {'Empresa': 'VERDIO', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Sim', 'Vídeo Monitoramento': 'Sim', 'Sensor de Fadiga': 'Sim', 'Controle de Jornada': 'Sim', 'Roteirizador': 'Sim'},
        # Nacionais
        {'Empresa': 'Sascar', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Sim', 'Vídeo Monitoramento': 'Sim', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Sim', 'Roteirizador': 'Sim'},
        {'Empresa': 'Omnilink', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Sim', 'Vídeo Monitoramento': 'Sim', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Sim', 'Roteirizador': 'Sim'},
        {'Empresa': 'Onixsat', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Sim', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Sim', 'Roteirizador': 'Não'},
        {'Empresa': 'Autotrac', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Sim'},
        {'Empresa': 'Veltec', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Sim', 'Vídeo Monitoramento': 'Sim', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Sim', 'Roteirizador': 'Sim'},
        {'Empresa': 'Ituran', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        {'Empresa': 'Positron', 'Categoria': 'Nacional/Mundial', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        # Regionais
        {'Empresa': 'Maxtrack', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Sim', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Sim'},
        {'Empresa': 'Getrak', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        {'Empresa': 'CEABS', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        {'Empresa': 'SystemSat', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        {'Empresa': 'GolSat', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        {'Empresa': 'Sighra', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
        {'Empresa': '3S', 'Categoria': 'Regional/Nicho', 'Telemetria (CAN)': 'Não', 'Vídeo Monitoramento': 'Não', 'Sensor de Fadiga': 'Não', 'Controle de Jornada': 'Não', 'Roteirizador': 'Não'},
    ],
    "precos_concorrentes": [
        {'Concorrente': 'VERDIO (Referência)', 'Categoria': 'Nacional/Mundial', 'Instalação (GPRS)': 'Alguns casos - R$ 50,00', 'Mensalidade (GPRS)': 'A partir de R$ 40,00', 'Instalação (Satelital)': 'Alguns casos - R$ 50,00', 'Mensalidade (Satelital)': 'A partir de R$ 107,67'},
        {'Concorrente': 'Sascar', 'Categoria': 'Nacional/Mundial', 'Instalação (GPRS)': 'R$ 300,00', 'Mensalidade (GPRS)': 'A partir de R$ 79,90', 'Instalação (Satelital)': 'R$ 1.200,00', 'Mensalidade (Satelital)': 'A partir de R$ 250,00'},
        {'Concorrente': 'Omnilink', 'Categoria': 'Nacional/Mundial', 'Instalação (GPRS)': 'R$ 350,00', 'Mensalidade (GPRS)': 'A partir de R$ 89,90', 'Instalação (Satelital)': 'R$ 1.500,00', 'Mensalidade (Satelital)': 'A partir de R$ 300,00'},
        {'Concorrente': 'Autotrac', 'Categoria': 'Nacional/Mundial', 'Instalação (GPRS)': 'R$ 400,00', 'Mensalidade (GPRS)': 'A partir de R$ 99,90', 'Instalação (Satelital)': '-', 'Mensalidade (Satelital)': '-'},
        {'Concorrente': 'Elite Rastro', 'Categoria': 'Regional/Nicho', 'Instalação (GPRS)': 'R$ 30,00', 'Mensalidade (GPRS)': 'R$ 50,00', 'Instalação (Satelital)': 'R$ 900,00', 'Mensalidade (Satelital)': 'R$ 180,00'},
        {'Concorrente': 'NJ Rastreamento', 'Categoria': 'Regional/Nicho', 'Instalação (GPRS)': 'R$ 120,00', 'Mensalidade (GPRS)': 'R$ 75,00', 'Instalação (Satelital)': 'R$ 650,00', 'Mensalidade (Satelital)': 'R$ 170,00'},
        {'Concorrente': 'TK Rastreadores', 'Categoria': 'Regional/Nicho', 'Instalação (GPRS)': 'R$ 80,00', 'Mensalidade (GPRS)': 'R$ 69,90', 'Instalação (Satelital)': 'R$ 980,00', 'Mensalidade (Satelital)': 'R$ 150,00'},
    ]
}

# Converte os dados para DataFrames do Pandas
df_features = pd.DataFrame(MARKET_DATA["comparativo_features"])
df_prices = pd.DataFrame(MARKET_DATA["precos_concorrentes"])

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>Pesquisa de Mercado e Concorrentes</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SEÇÃO MERCADO-ALVO ---
st.subheader("Nosso Mercado-Alvo")
st.markdown("""
| Segmento | Dor Principal | Oportunidade para o Verdio |
|---|---|---|
| **Locadoras de Veículos** | Risco e Descontrole do Ativo: Uso indevido, sinistros e a dificuldade de garantir a segurança do patrimônio. | Oferecer uma solução de proteção do ativo e segurança jurídica, que vai além do simples rastreamento. |
| **Transportadoras** | Altos Custos Operacionais e Riscos Trabalhistas: Consumo excessivo de combustível, manutenção imprevista e acidentes. | Entregar uma plataforma de eficiência operacional e compliance, com ROI claro através da redução de custos. |
""")
st.markdown("---")

# --- SEÇÃO DIFERENCIAIS ---
st.subheader("Nossos Diferenciais Competitivos")
st.write("Para vencer no mercado, nosso discurso deve focar nos pilares que a concorrência não entrega de forma integrada:")
st.info("📊 **Gestão Financeira Integrada (ROI Claro):** Nossos dashboards transformam dados operacionais em indicadores financeiros, provando o retorno sobre o investimento.")
st.info("👮‍♂️ **Segurança Jurídica e Compliance:** Somos a única solução que integra a gestão da Lei do Motorista com o sensor de fadiga, mitigando passivos trabalhistas e acidentes.")
st.info("💡 **Inovação Acessível:** Oferecemos tecnologias de ponta (sensor de fadiga, vídeo) que são tipicamente premium, como parte do nosso pacote padrão.")
st.markdown("---")


# --- SEÇÃO COMPARATIVO DE PREÇOS ---
st.subheader("Comparativo de Preços")
st.markdown("##### Concorrentes Nacionais")
df_prices_nacional = df_prices[df_prices['Categoria'] == 'Nacional/Mundial'].drop(columns=['Categoria'])
st.dataframe(df_prices_nacional, hide_index=True, use_container_width=True)

st.markdown("##### Concorrentes Regionais")
df_prices_regional = df_prices[df_prices['Categoria'] == 'Regional/Nicho'].drop(columns=['Categoria'])
st.dataframe(df_prices_regional, hide_index=True, use_container_width=True)
st.markdown("---")

# --- SEÇÃO COMPARATIVO DE FUNCIONALIDADES ---
st.subheader("Comparativo de Funcionalidades")
st.markdown("##### Concorrentes Nacionais")
df_features_nacional = df_features[df_features['Categoria'] == 'Nacional/Mundial'].drop(columns=['Categoria'])
st.dataframe(df_features_nacional, hide_index=True, use_container_width=True)

st.markdown("##### Concorrentes Regionais")
df_features_regional = df_features[df_features['Categoria'] == 'Regional/Nicho'].drop(columns=['Categoria'])
st.dataframe(df_features_regional, hide_index=True, use_container_width=True)
st.markdown("---")
