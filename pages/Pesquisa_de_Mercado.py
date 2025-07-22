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

# --- 2. FUNÇÕES PARA CARREGAR DADOS ---
@st.cache_data
def load_data():
    """Carrega todos os dados dos ficheiros CSV."""
    try:
        df_comparativo = pd.read_csv("pesqusisa de mercado rastreadores março 2025.xlsx - comparativo.csv")
        df_precos = pd.read_csv("pesqusisa de mercado rastreadores março 2025.xlsx - preços praticados .csv")
        df_empresas = pd.read_csv("pesqusisa de mercado rastreadores março 2025.xlsx - empresas.csv")
        df_alvos = pd.read_csv("Locadoras e Transportadoras.xlsx - Página1.csv")
        
        return df_comparativo, df_precos, df_empresas, df_alvos
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar os ficheiros de dados: {e}. Certifique-se de que os ficheiros .csv estão na pasta raiz do projeto.")
        return None, None, None, None

# Carrega os dados
df_comparativo, df_precos, df_empresas, df_alvos = load_data()

if df_comparativo is None:
    st.stop()

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
| **Locadoras de Veículos** | Risco e Descontrole do Ativo: Uso indevido, sinistros, multas e a dificuldade de garantir a segurança do patrimônio. | Oferecer uma solução de proteção do ativo e segurança jurídica, que vai além do simples rastreamento. |
| **Transportadoras** | Altos Custos Operacionais e Riscos Trabalhistas: Consumo excessivo de combustível, manutenção imprevista, acidentes por fadiga. | Entregar uma plataforma de eficiência operacional e compliance, com ROI claro através da redução de custos. |
""")
st.markdown("---")

# --- SEÇÃO DIFERENCIAIS ---
st.subheader("Nossos Diferenciais Competitivos")
st.write("Para vencer no mercado, nosso discurso deve focar nos pilares que a concorrência não entrega de forma integrada:")
st.info("📊 **Gestão Financeira Integrada (ROI Claro):** Nossos dashboards transformam dados operacionais (combustível, ociosidade) em indicadores financeiros, provando o retorno sobre o investimento.")
st.info("👮‍♂️ **Segurança Jurídica e Compliance:** Somos a única solução que integra a gestão da Lei do Motorista com o sensor de fadiga, mitigando passivos trabalhistas e acidentes.")
st.info("💡 **Inovação Acessível:** Oferecemos tecnologias de ponta (sensor de fadiga, vídeo) que são tipicamente premium, como parte do nosso pacote padrão.")
st.markdown("---")


# --- SEÇÃO GRÁFICO DE FUNCIONALIDADES ---
st.subheader("Verdio vs. Concorrência: A Vantagem Clara")
st.write("Analisando as funcionalidades-chave, o Verdio se destaca por oferecer um pacote completo e tecnologicamente avançado a um preço competitivo.")

# Prepara os dados do CSV para o gráfico
df_comparativo_chart = df_comparativo.head(8) # Pega os 8 principais concorrentes
features = ['Telemetria (CAN)', 'Vídeo Monitoramento', 'Sensor de Fadiga', 'Controle de Jornada', 'Roteirizador']
colors = ['#006494', '#0582CA', '#A7C957', '#00A6FB', '#6A994E']

fig_features = go.Figure()
for feature, color in zip(features, colors):
    # Converte 'Sim'/'Não' para 1/0
    x_data = df_comparativo_chart[feature].apply(lambda x: 1 if str(x).strip().lower() == 'sim' else 0)
    fig_features.add_trace(go.Bar(
        y=df_comparativo_chart['Empresa'],
        x=x_data,
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

# Prepara os dados do CSV para o gráfico
df_precos_chart = df_precos.head(8)
df_precos_chart['color'] = df_precos_chart['Empresa'].apply(lambda x: '#A7C957' if x == 'VERDIO' else '#0582CA')
df_precos_chart['size'] = df_precos_chart['Empresa'].apply(lambda x: 25 if x == 'VERDIO' else 15)

fig_bubble = go.Figure(data=[go.Scatter(
    x=df_precos_chart['Preço Mensal (a partir de)'],
    y=df_precos_chart['Nº de Funcionalidades Essenciais'],
    text=df_precos_chart['Empresa'],
    mode='markers+text',
    textposition="top center",
    marker=dict(
        size=df_precos_chart['size'],
        color=df_precos_chart['color'],
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
st.subheader("Nossos Alvos Regionais")
col_c, col_d = st.columns(2)
with col_c:
    st.info("🎯 **Alvos em Locadoras**")
    for locadora in df_alvos[df_alvos['Tipo'] == 'Locadora']['Empresa']:
        st.markdown(f"- {locadora}")
with col_d:
    st.info("🎯 **Alvos em Transportadoras**")
    for transportadora in df_alvos[df_alvos['Tipo'] == 'Transportadora']['Empresa']:
        st.markdown(f"- {transportadora}")
