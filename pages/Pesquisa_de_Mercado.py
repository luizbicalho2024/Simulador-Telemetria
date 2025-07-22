# pages/Pesquisa_de_Mercado.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

# --- 2. FUNÇÃO PARA CARREGAR DADOS DIRETAMENTE DOS FICHEIROS CSV ---
@st.cache_data
def load_data_from_files():
    """Carrega todos os dados dos ficheiros CSV para garantir a fidelidade."""
    try:
        df_funci_regionais = pd.read_csv("funcionalidades e preco.xlsx - funci. regionais.csv")
        df_funci_nacionais = pd.read_csv("funcionalidades e preco.xlsx - funci. nacionais.csv")
        df_preco_regionais = pd.read_csv("funcionalidades e preco.xlsx - preco regionais.csv")
        df_preco_nacionais = pd.read_csv("funcionalidades e preco.xlsx - preco nacionais.csv")
        return df_funci_regionais, df_funci_nacionais, df_preco_regionais, df_preco_nacionais
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar os ficheiros de dados: {e}. Certifique-se de que os quatro ficheiros .csv estão na pasta raiz do projeto.")
        return None, None, None, None

# Carrega os dados
df_funci_regionais, df_funci_nacionais, df_preco_regionais, df_preco_nacionais = load_data_from_files()

if df_funci_regionais is None:
    st.stop() # Interrompe a execução se os dados não puderem ser carregados

# --- 3. INTERFACE DA PÁGINA ---
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
| **Locadoras de Veículos** | Risco e Descontrole do Ativo: Uso indevido, sinistros e a dificuldade de garantir a segurança do patrimônio. | Oferecer uma solução de proteção do ativo e segurança jurídica, que vai além do simples rastreamento. |
| **Transportadoras** | Altos Custos Operacionais e Riscos Trabalhistas: Consumo excessivo de combustível, manutenção imprevista e acidentes. | Entregar uma plataforma de eficiência operacional e compliance, com ROI claro através da redução de custos. |
""")
st.markdown("---")

st.subheader("Nossos Diferenciais Competitivos")
st.write("Para vencer no mercado, nosso discurso deve focar nos pilares que a concorrência não entrega de forma integrada:")
st.info("📊 **Gestão Financeira Integrada (ROI Claro):** Nossos dashboards transformam dados operacionais em indicadores financeiros, provando o retorno sobre o investimento.")
st.info("👮‍♂️ **Segurança Jurídica e Compliance:** Somos a única solução que integra a gestão da Lei do Motorista com o sensor de fadiga, mitigando passivos trabalhistas e acidentes.")
st.info("💡 **Inovação Acessível:** Oferecemos tecnologias de ponta (sensor de fadiga, vídeo) que são tipicamente premium, como parte do nosso pacote padrão.")
st.markdown("---")


# --- 4. EXIBIÇÃO DAS TABELAS COMPLETAS ---
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

st.markdown("---")


# --- 5. GRÁFICOS DE BUSINESS INTELLIGENCE (BI) ---
st.subheader("Visualização e Inteligência de Mercado (BI)")

# --- GRÁFICO 1: PONTUAÇÃO DE FUNCIONALIDADES ---
st.markdown("##### Pontuação Total de Funcionalidades")
st.write("Este gráfico classifica os concorrentes com base numa pontuação, onde cada funcionalidade essencial ('Sim') vale 1 ponto e 'Parcial' ou 'Opcional' vale 0.5.")

df_func_all = pd.concat([df_funci_nacionais, df_funci_regionais]).drop_duplicates(subset=['Empresa']).reset_index(drop=True)
score_map = {'✅ Sim': 1.0, '❔ Opcional': 0.5, '❔ Parcial': 0.5, '❌ Não': 0.0, '❔ Comercial': 0.0}
features_to_score = ['Telemetria (CAN)', 'Vídeo', 'Sensor de Fadiga', 'Controle de Jornada', 'Roteirizador', 'Suporte 24h', 'App de Gestão']

for feature in features_to_score:
    if feature in df_func_all.columns:
        df_func_all[feature] = df_func_all[feature].map(score_map).fillna(0)

df_func_all['Pontuação Total'] = df_func_all[features_to_score].sum(axis=1)
df_func_all_sorted = df_func_all.sort_values('Pontuação Total', ascending=True)

fig_score = go.Figure(go.Bar(
    y=df_func_all_sorted['Empresa'], x=df_func_all_sorted['Pontuação Total'],
    orientation='h', marker=dict(color=df_func_all_sorted['Pontuação Total'], colorscale='Greens')
))
fig_score.update_layout(
    title='Ranking de Concorrentes por Pontuação de Funcionalidades',
    xaxis_title='Pontuação Total (Soma das Funcionalidades)', yaxis_title=None, height=600
)
st.plotly_chart(fig_score, use_container_width=True)

# --- GRÁFICO 2: CUSTO-BENEFÍCIO ---
st.markdown("##### Análise de Custo-Benefício (GPRS)")
st.write("Este gráfico cruza o custo da mensalidade GPRS com a pontuação de funcionalidades.")

def clean_price(price_str):
    try:
        price = re.findall(r'\d+[\.,]\d+', str(price_str))[0]
        return float(price.replace(',', '.'))
    except (IndexError, TypeError):
        return None

df_prices_all = pd.concat([df_preco_nacionais, df_preco_regionais]).drop_duplicates(subset=['Empresa'])
df_prices_all['Mensalidade_GPRS_Num'] = df_prices_all['Mensalidade (GPRS)'].apply(clean_price)

df_bi = pd.merge(df_func_all, df_prices_all, on='Empresa', how='left')
df_bi.dropna(subset=['Mensalidade_GPRS_Num'], inplace=True)

df_bi['color'] = df_bi['Empresa'].apply(lambda x: '#A7C957' if 'VERDIO' in x else '#0582CA')
df_bi['size'] = df_bi['Pontuação Total'].apply(lambda y: y * 4 + 10)

fig_bubble_bi = go.Figure(data=[go.Scatter(
    x=df_bi['Mensalidade_GPRS_Num'], y=df_bi['Pontuação Total'],
    text=df_bi['Empresa'], mode='markers+text', textposition="top center",
    marker=dict(size=df_bi['size'], color=df_bi['color'])
)])
fig_bubble_bi.update_layout(
    title='Custo (Mensalidade GPRS) vs. Benefício (Pontuação de Funcionalidades)',
    xaxis_title="Preço da Mensalidade GPRS (R$)",
    yaxis_title="Pontuação Total de Funcionalidades",
    height=600, showlegend=False
)
st.plotly_chart(fig_bubble_bi, use_container_width=True)
