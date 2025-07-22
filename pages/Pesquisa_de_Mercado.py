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

# --- 2. DADOS CENTRALIZADOS (Extraídos do PDF e ficheiros de dados) ---
MARKET_DATA = {
    "comparativo_features": [
        {'Empresa': 'VERDIO', 'Telemetria (CAN)': 1, 'Vídeo Monitoramento': 1, 'Sensor de Fadiga': 1, 'Controle de Jornada': 1, 'Roteirizador': 1},
        {'Empresa': 'Sascar', 'Telemetria (CAN)': 1, 'Vídeo Monitoramento': 1, 'Sensor de Fadiga': 0, 'Controle de Jornada': 1, 'Roteirizador': 1},
        {'Empresa': 'Omnilink', 'Telemetria (CAN)': 1, 'Vídeo Monitoramento': 1, 'Sensor de Fadiga': 0, 'Controle de Jornada': 1, 'Roteirizador': 1},
        {'Empresa': 'Onixsat', 'Telemetria (CAN)': 1, 'Vídeo Monitoramento': 0, 'Sensor de Fadiga': 0, 'Controle de Jornada': 1, 'Roteirizador': 0},
        {'Empresa': 'Autotrac', 'Telemetria (CAN)': 0, 'Vídeo Monitoramento': 0, 'Sensor de Fadiga': 0, 'Controle de Jornada': 0, 'Roteirizador': 1},
        {'Empresa': 'Veltec', 'Telemetria (CAN)': 1, 'Vídeo Monitoramento': 1, 'Sensor de Fadiga': 0, 'Controle de Jornada': 1, 'Roteirizador': 1},
        {'Empresa': 'Maxtrack', 'Telemetria (CAN)': 1, 'Vídeo Monitoramento': 0, 'Sensor de Fadiga': 0, 'Controle de Jornada': 0, 'Roteirizador': 1},
        {'Empresa': 'Getrak', 'Telemetria (CAN)': 0, 'Vídeo Monitoramento': 0, 'Sensor de Fadiga': 0, 'Controle de Jornada': 0, 'Roteirizador': 0},
    ],
    "precos_performance": [
        {'Empresa': 'Getrak', 'Preço Mensal': 34.90, 'Funcionalidades': 0},
        {'Empresa': 'VERDIO', 'Preço Mensal': 40.00, 'Funcionalidades': 5},
        {'Empresa': 'Maxtrack', 'Preço Mensal': 59.90, 'Funcionalidades': 2},
        {'Empresa': 'Sascar', 'Preço Mensal': 79.90, 'Funcionalidades': 4},
        {'Empresa': 'Omnilink', 'Preço Mensal': 89.90, 'Funcionalidades': 4},
        {'Empresa': 'Autotrac', 'Preço Mensal': 99.90, 'Funcionalidades': 1},
        {'Empresa': 'Veltec', 'Preço Mensal': 110.00, 'Funcionalidades': 4},
        {'Empresa': 'Onixsat', 'Preço Mensal': 120.00, 'Funcionalidades': 2},
    ],
    "empresas_concorrentes": {
        "nacional_mundial": ["Sascar (Michelin)", "Omnilink", "Ituran", "Positron", "Autotrac", "Onixsat", "Veltec"],
        "regional_nicho": ["Getrak", "Maxtrack", "CEABS", "SystemSat", "GolSat", "Sighra", "3S"]
    },
    "alvos": {
        "locadoras": ["LOCALIZA HERTZ", "MOVIDA", "UNIDAS", "AS RENT A CAR", "FOCO ALUGUEL DE CARROS", "YES RENT A CAR", "VAMOS LOCADORA"],
        "transportadoras": ["JSL", "TRANSPORTE BERTOLINI", "ATUAL CARGAS", "BRASPRESS", "CARVALIMA", "COOPERCarga", "RODONAVES"]
    }
}

df_comparativo = pd.DataFrame(MARKET_DATA["comparativo_features"])
df_precos = pd.DataFrame(MARKET_DATA["precos_performance"])

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
st.info("📊 **Gestão Financeira Integrada (ROI Claro):** Nossos dashboards transformam dados operacionais (combustível, ociosidade) em indicadores financeiros, provando o retorno sobre o investimento.")
st.info("👮‍♂️ **Segurança Jurídica e Compliance:** Somos a única solução que integra a gestão da Lei do Motorista com o sensor de fadiga, mitigando passivos trabalhistas e acidentes.")
st.info("💡 **Inovação Acessível:** Oferecemos tecnologias de ponta (sensor de fadiga, vídeo) que são tipicamente premium, como parte do nosso pacote padrão.")
st.markdown("---")


# --- SEÇÃO CENÁRIO COMPETITIVO ---
st.subheader("Cenário Competitivo")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("##### Players Nacionais e Mundiais")
    for empresa in MARKET_DATA["empresas_concorrentes"]["nacional_mundial"]:
        st.markdown(f"- {empresa}")
with col_b:
    st.markdown("##### Players Regionais e de Nicho")
    for empresa in MARKET_DATA["empresas_concorrentes"]["regional_nicho"]:
        st.markdown(f"- {empresa}")
st.markdown("---")

# --- SEÇÃO GRÁFICO DE COMPARAÇÃO DE FUNCIONALIDADES ---
st.subheader("Verdio vs. Concorrência: A Vantagem Clara")
fig_features = go.Figure()
features = ['Telemetria (CAN)', 'Vídeo Monitoramento', 'Sensor de Fadiga', 'Controle de Jornada', 'Roteirizador']
colors = ['#006494', '#0582CA', '#A7C957', '#00A6FB', '#6A994E']

for feature, color in zip(features, colors):
    fig_features.add_trace(go.Bar(
        y=df_comparativo['Empresa'], x=df_comparativo[feature], name=feature,
        orientation='h', marker=dict(color=color)
    ))
fig_features.update_layout(
    title='Comparativo de Funcionalidades por Empresa', barmode='stack',
    yaxis={'categoryorder':'total ascending'}, yaxis_title=None,
    xaxis_title="Funcionalidades Oferecidas (1 = Sim, 0 = Não)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500, margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig_features, use_container_width=True)
st.markdown("---")

# --- SEÇÃO GRÁFICO DE CUSTO-BENEFÍCIO ---
st.subheader("Custo-Benefício no Mercado")
df_precos['color'] = df_precos['Empresa'].apply(lambda x: '#A7C957' if x == 'VERDIO' else '#0582CA')
df_precos['size'] = df_precos['Funcionalidades'].apply(lambda y: y * 5 + 10)

fig_bubble = go.Figure(data=[go.Scatter(
    x=df_precos['Preço Mensal'], y=df_precos['Funcionalidades'],
    text=df_precos['Empresa'], mode='markers+text', textposition="top center",
    marker=dict(size=df_precos['size'], color=df_precos['color'])
)])
fig_bubble.update_layout(
    title='Preço Mensal vs. Quantidade de Funcionalidades Essenciais',
    xaxis_title="Preço Mensal (A partir de R$)",
    yaxis_title="Nº de Funcionalidades Essenciais",
    height=500, margin=dict(l=20, r=20, t=50, b=20), showlegend=False
)
st.plotly_chart(fig_bubble, use_container_width=True)
st.markdown("---")

# --- SEÇÃO CLIENTES-ALVO ---
st.subheader("Nossos Alvos Regionais")
col_c, col_d = st.columns(2)
with col_c:
    st.info("🎯 **Alvos em Locadoras**")
    for locadora in MARKET_DATA["alvos"]["locadoras"]:
        st.markdown(f"- {locadora}")
with col_d:
    st.info("🎯 **Alvos em Transportadoras**")
    for transportadora in MARKET_DATA["alvos"]["transportadoras"]:
        st.markdown(f"- {transportadora}")
