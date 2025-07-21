# pages/Analise_Concorrentes.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Análise de Concorrentes",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES PARA CARREGAR DADOS ---
@st.cache_data
def load_data():
    """Carrega todos os dados dos ficheiros CSV."""
    try:
        # Carrega os dados para os gráficos
        df_comparativo = pd.read_csv("pesqusisa de mercado rastreadores março 2025.xlsx - comparativo.csv")
        df_precos = pd.read_csv("pesqusisa de mercado rastreadores março 2025.xlsx - preços praticados .csv")
        
        # Carrega os dados para as listas de empresas
        df_empresas = pd.read_csv("pesqusisa de mercado rastreadores março 2025.xlsx - empresas.csv")
        df_alvos = pd.read_csv("Locadoras e Transportadoras.xlsx - Página1.csv")
        
        return df_comparativo, df_precos, df_empresas, df_alvos
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar os ficheiros de dados: {e}. Certifique-se de que os ficheiros .csv estão na pasta raiz do projeto.")
        return None, None, None, None

# Carrega os dados
df_comparativo, df_precos, df_empresas, df_alvos = load_data()

if df_comparativo is None:
    st.stop() # Interrompe a execução se os dados não puderem ser carregados

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
    for empresa in df_empresas[df_empresas['Categoria'] == 'Nacional/Mundial']['Empresa']:
        st.markdown(f"- {empresa}")
with col_b:
    st.markdown("##### Players Regionais e de Nicho")
    for empresa in df_empresas[df_empresas['Categoria'] == 'Regional/Nicho']['Empresa']:
        st.markdown(f"- {empresa}")
st.markdown("---")

# --- SEÇÃO GRÁFICO DE FUNCIONALIDADES ---
st.subheader("Verdio vs. Concorrência: A Vantagem Clara")
st.write("Analisando as funcionalidades-chave, o Verdio se destaca por oferecer um pacote completo e tecnologicamente avançado a um preço competitivo. O nosso principal diferencial, o Sensor de Fadiga, é um recurso de segurança que a maioria dos concorrentes não oferece ou cobra um valor premium.")

fig_features = go.Figure()
features = ['Telemetria (CAN)', 'Vídeo Monitoramento', 'Sensor de Fadiga', 'Controle de Jornada', 'Roteirizador']
colors = ['#006494', '#0582CA', '#A7C957', '#00A6FB', '#6A994E']

for feature, color in zip(features, colors):
    fig_features.add_trace(go.Bar(
        y=df_comparativo['Empresa'],
        x=df_comparativo[feature],
        name=feature,
        orientation='h',
        marker=dict(color=color)
    ))

fig_features.update_layout(
    title='Comparativo de Funcionalidades por Empresa', barmode='stack',
    yaxis={'categoryorder':'total ascending'}, yaxis_title="Empresa",
    xaxis_title="Funcionalidades Oferecidas (1 = Sim, 0 = Não)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500, margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig_features, use_container_width=True)
st.markdown("---")

# --- SEÇÃO GRÁFICO DE CUSTO-BENEFÍCIO ---
st.subheader("Custo-Benefício no Mercado")
st.write("Ao cruzar o preço inicial com a quantidade de funcionalidades essenciais, o Verdio se posiciona no 'quadrante de alto valor', entregando a mais completa suíte de recursos pelo preço mais competitivo.")

df_precos['color'] = df_precos['Empresa'].apply(lambda x: '#A7C957' if x == 'VERDIO' else '#0582CA')
df_precos['size'] = df_precos['Empresa'].apply(lambda x: 25 if x == 'VERDIO' else 15)

fig_bubble = go.Figure(data=[go.Scatter(
    x=df_precos['Preço Mensal (a partir de)'],
    y=df_precos['Nº de Funcionalidades Essenciais'],
    text=df_precos['Empresa'],
    mode='markers+text',
    textposition="top center",
    marker=dict(
        size=df_precos['size'],
        color=df_precos['color'],
        sizemode='diameter'
    )
)])
fig_bubble.update_layout(
    title='Preço Mensal vs. Quantidade de Funcionalidades Essenciais',
    xaxis_title="Preço Mensal (A partir de R$)",
    yaxis_title="Nº de Funcionalidades Essenciais",
    height=500, margin=dict(l=20, r=20, t=50, b=20),
    showlegend=False
)
st.plotly_chart(fig_bubble, use_container_width=True)
st.markdown("---")

# --- SEÇÃO CLIENTES-ALVO ---
st.subheader("Nossos Alvos: A Oportunidade de Mercado")
col_c, col_d = st.columns(2)
with col_c:
    st.info("🎯 **Alvos em Locadoras**")
    for locadora in df_alvos[df_alvos['Tipo'] == 'Locadora']['Empresa']:
        st.markdown(f"- {locadora}")
with col_d:
    st.info("🎯 **Alvos em Transportadoras**")
    for transportadora in df_alvos[df_alvos['Tipo'] == 'Transportadora']['Empresa']:
        st.markdown(f"- {transportadora}")
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
