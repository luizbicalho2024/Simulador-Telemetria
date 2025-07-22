# pages/Pesquisa_de_Mercado.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO DA PÁGINA E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Pesquisa de Mercado",
    page_icon="imgs/v-c.png"
)

# Bloco de verificação de autenticação padrão
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. DADOS (Extraídos do PDF) ---
# Dados para o gráfico de comparação de funcionalidades
comparison_data = {
    'labels': ['VERDIO', 'Sascar', 'Omnilink', 'Onixsat', 'Autotrac', 'Veltec', 'Maxtrack', 'Getrak'],
    'datasets': [
        {'label': 'Telemetria (CAN)', 'data': [1, 1, 1, 1, 0, 1, 1, 0], 'color': '#006494'},
        {'label': 'Vídeo Monitoramento', 'data': [1, 1, 1, 0, 0, 1, 0, 0], 'color': '#0582CA'},
        {'label': 'Sensor de Fadiga', 'data': [1, 0, 0, 0, 0, 0, 0, 0], 'color': '#A7C957'},
        {'label': 'Controle de Jornada', 'data': [1, 1, 1, 1, 0, 1, 0, 0], 'color': '#00A6FB'},
        {'label': 'Roteirizador', 'data': [1, 1, 1, 0, 1, 1, 1, 0], 'color': '#6A994E'},
    ]
}

# Dados para o gráfico de custo-benefício (bubble chart)
price_performance_data = {
    'labels': ['Getrak', 'VERDIO', 'Maxtrack', 'Sascar', 'Omnilink', 'Autotrac', 'Veltec', 'Onixsat'],
    'data': [
        {'x': 34.90, 'y': 0, 'r': 10}, {'x': 40.00, 'y': 5, 'r': 25}, {'x': 59.90, 'y': 2, 'r': 15},
        {'x': 79.90, 'y': 4, 'r': 20}, {'x': 89.90, 'y': 4, 'r': 20}, {'x': 99.90, 'y': 1, 'r': 12},
        {'x': 110.00, 'y': 4, 'r': 20}, {'x': 120.00, 'y': 2, 'r': 15},
    ],
    'verdiocolor': '#A7C957',
    'competitorcolor': '#0582CA'
}

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>Análise Competitiva de Mercado</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em;'>Inteligência para Frotas</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SEÇÃO INTRODUTÓRIA E ROI ---
st.subheader("O Desafio da Frota Moderna")
st.write("Gerenciar uma frota hoje é um ato de equilíbrio entre reduzir custos operacionais e mitigar riscos críticos. Falhas na gestão resultam em perdas financeiras e vulnerabilidades que podem comprometer toda a operação.")
st.metric(label="Retorno sobre o Investimento (ROI) com Gestão Eficiente", value="200%")
st.caption("Cálculo baseado na eliminação de custos invisíveis versus o investimento na plataforma Verdio.")
st.markdown("---")

# --- SEÇÃO SOLUÇÃO VERDIO ---
st.subheader("Verdio: A Solução Integrada")
st.write("Verdio transforma dados brutos em decisões inteligentes, conectando a tecnologia embarcada no veículo à gestão estratégica do negócio, focando em segurança, conformidade e, principalmente, rentabilidade.")
col1, col2, col3 = st.columns(3)
with col1:
    st.info("🛰️ **Tecnologia Embarcada:** Hardware de ponta, incluindo rastreador, vídeo e sensor de fadiga.")
with col2:
    st.info("📊 **Plataforma de Gestão:** Dashboards claros, relatórios financeiros e controle de jornada.")
with col3:
    st.success("🏆 **Decisão e Resultado:** ROI comprovado, mais segurança e total conformidade legal.")
st.markdown("---")

# --- SEÇÃO CENÁRIO COMPETITIVO ---
st.subheader("Cenário Competitivo")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("##### Players Nacionais e Mundiais")
    st.markdown("""
    - Sascar (Michelin)
    - Omnilink
    - Ituran
    - Positron
    - Autotrac
    - Onixsat
    - Veltec
    """)
with col_b:
    st.markdown("##### Players Regionais e de Nicho")
    st.markdown("""
    - Getrak
    - Maxtrack
    - CEABS
    - SystemSat
    - GolSat
    - Sighra
    - 3S
    """)
st.markdown("---")

# --- SEÇÃO GRÁFICO DE FUNCIONALIDADES ---
st.subheader("Verdio vs. Concorrência: A Vantagem Clara")
st.write("Analisando as funcionalidades-chave, o Verdio se destaca por oferecer um pacote completo e tecnologicamente avançado a um preço competitivo. O nosso principal diferencial, o Sensor de Fadiga, é um recurso de segurança que a maioria dos concorrentes não oferece ou cobra um valor premium.")

fig_features = go.Figure()
for dataset in comparison_data['datasets']:
    fig_features.add_trace(go.Bar(
        y=comparison_data['labels'], x=dataset['data'], name=dataset['label'],
        orientation='h', marker=dict(color=dataset['color'])
    ))
fig_features.update_layout(
    title='Comparativo de Funcionalidades por Empresa', barmode='stack',
    yaxis={'categoryorder':'total ascending'}, yaxis_title="Empresa",
    xaxis_title="Funcionalidades Oferecidas (Pontuação)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500, margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig_features, use_container_width=True)
st.markdown("---")

# --- SEÇÃO GRÁFICO DE CUSTO-BENEFÍCIO ---
st.subheader("Custo-Benefício no Mercado")
st.write("Ao cruzar o preço inicial com a quantidade de funcionalidades essenciais, o Verdio se posiciona no 'quadrante de alto valor', entregando a mais completa suíte de recursos pelo preço mais competitivo.")

bubble_colors = [price_performance_data['verdiocolor'] if label == 'VERDIO' else price_performance_data['competitorcolor'] for label in price_performance_data['labels']]
fig_bubble = go.Figure(data=[go.Scatter(
    x=[d['x'] for d in price_performance_data['data']],
    y=[d['y'] for d in price_performance_data['data']],
    text=price_performance_data['labels'], mode='markers+text',
    textposition="top center",
    marker=dict(
        size=[d['r'] for d in price_performance_data['data']], color=bubble_colors,
        sizemode='diameter', showscale=False
    )
)])
fig_bubble.update_layout(
    title='Preço Mensal vs. Quantidade de Funcionalidades Essenciais',
    xaxis_title="Preço Mensal (A partir de R$)",
    yaxis_title="Nº de Funcionalidades Essenciais",
    height=500, margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig_bubble, use_container_width=True)
st.markdown("---")

# --- SEÇÃO CLIENTES-ALVO ---
st.subheader("Nossos Alvos: A Oportunidade de Mercado")
col_c, col_d = st.columns(2)
with col_c:
    st.info("🎯 **Alvos em Locadoras:** LOCALIZA HERTZ, MOVIDA, UNIDAS, AS RENT A CAR, FOCO, YES RENT A CAR, VAMOS LOCADORA.")
with col_d:
    st.info("🎯 **Alvos em Transportadoras:** JSL, TRANSPORTE BERTOLINI, ATUAL CARGAS, BRASPRESS, CARVALIMA, COOPERCarga, RODONAVES.")
st.markdown("---")

# --- SEÇÃO IMPLANTAÇÃO ---
st.subheader("Implantação Ágil: Do Contrato ao Valor")
st.write("Nossa promessa é clara: frotas de até 200 veículos implantadas em 30 dias, sem paralisar a operação do cliente. O nosso processo é consultivo e pensado para gerar resultados rápidos.")
st.markdown("""
- **1. Diagnóstico:** Análise da frota e sistemas atuais.
- **2. Proposta Sob Medida:** Plano customizado para o seu negócio.
- **3. Implantação:** Instalação do hardware sem parar a frota.
- **4. Treinamento:** Capacitação das equipas operacionais.
""")
