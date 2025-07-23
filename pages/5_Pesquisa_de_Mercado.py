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

# --- 2. DADOS CENTRALIZADOS ---
MARKET_DATA = {
    "funcionalidades": [
        {'Empresa': 'VERDIO', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '✅ Sim', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Sascar', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Omnilink', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Onixsat', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Veltec', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Positron', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❔ Opcional', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Autotrac', 'Categoria': 'Nacional', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Maxtrack', 'Categoria': 'Nacional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Elite Rastro', 'Categoria': 'Regional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'NJ Rastreamento', 'Categoria': 'Regional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'TK Rastreadores', 'Categoria': 'Regional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '❔ Comercial', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'vtrackrastreamento', 'Categoria': 'Regional', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'rastrek', 'Categoria': 'Regional', 'Telemetria (CAN)': '❔ Parcial', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Pro Lion', 'Categoria': 'Regional', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Impacto Rast.', 'Categoria': 'Regional', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
    ],
    "precos": [
        {'Empresa': 'VERDIO', 'Mensalidade (GPRS)': 'R$ 44,93 - R$ 584,49'},
        {'Empresa': 'Sascar', 'Mensalidade (GPRS)': 'R$ 79,90'},
        {'Empresa': 'Omnilink', 'Mensalidade (GPRS)': 'R$ 89,90'},
        {'Empresa': 'Onixsat', 'Mensalidade (GPRS)': '–'},
        {'Empresa': 'Veltec', 'Mensalidade (GPRS)': 'R$ 110,00'},
        {'Empresa': 'Positron', 'Mensalidade (GPRS)': 'R$ 75,00'},
        {'Empresa': 'Autotrac', 'Mensalidade (GPRS)': 'R$ 99,90'},
        {'Empresa': 'Maxtrack', 'Mensalidade (GPRS)': 'R$ 59,90'},
        {'Empresa': 'Elite Rastro', 'Mensalidade (GPRS)': 'R$ 50,00'},
        {'Empresa': 'NJ Rastreamento', 'Mensalidade (GPRS)': 'R$ 75,00'},
        {'Empresa': 'TK Rastreadores', 'Mensalidade (GPRS)': 'R$ 69,90'},
        {'Empresa': 'vtrackrastreamento', 'Mensalidade (GPRS)': 'R$ 50,00'},
        {'Empresa': 'rastrek', 'Mensalidade (GPRS)': 'R$ 60,00'},
        {'Empresa': 'Pro Lion', 'Mensalidade (GPRS)': 'R$ 49,90 - R$ 69,90'},
        {'Empresa': 'Impacto Rast.', 'Mensalidade (GPRS)': 'R$ 45,00'},
    ]
}

# --- 3. PROCESSAMENTO DE DADOS ---
df_func_all = pd.DataFrame(MARKET_DATA["funcionalidades"])
df_prices_all = pd.DataFrame(MARKET_DATA["precos"])

score_map = {'✅ Sim': 1.0, '❔ Opcional': 0.5, '❔ Parcial': 0.5, '❌ Não': 0.0, '❔ Comercial': 0.0}
features_to_score = ['Telemetria (CAN)', 'Vídeo', 'Sensor de Fadiga', 'Controle de Jornada', 'Roteirizador', 'Com. Satelital', 'Suporte 24h', 'App de Gestão']
for feature in features_to_score:
    if feature in df_func_all.columns:
        df_func_all[feature + '_Score'] = df_func_all[feature].map(score_map).fillna(0)
df_func_all['Pontuação Total'] = df_func_all[[f + '_Score' for f in features_to_score]].sum(axis=1)

def clean_price(price_str):
    try:
        return float(re.findall(r'\d+[\.,]\d+', str(price_str))[0].replace(',', '.'))
    except (IndexError, TypeError):
        return None
df_prices_all['Mensalidade_GPRS_Num'] = df_prices_all['Mensalidade (GPRS)'].apply(clean_price)

df_bi = pd.merge(df_func_all, df_prices_all, on='Empresa', how='left')
df_bi.dropna(subset=['Mensalidade_GPRS_Num', 'Pontuação Total'], inplace=True)
df_bi['Custo_por_Ponto'] = df_bi['Mensalidade_GPRS_Num'] / df_bi['Pontuação Total']
df_bi['Custo_por_Ponto'].fillna(0, inplace=True) # Evita divisão por zero

# --- 4. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title("Filtros e Análises")

# --- Filtros Interativos ---
st.sidebar.subheader("Filtros do Dashboard")
categorias = st.sidebar.multiselect("Filtrar por Categoria:", options=df_bi['Categoria'].unique(), default=df_bi['Categoria'].unique())
max_price = int(df_bi['Mensalidade_GPRS_Num'].max()) + 1
price_range = st.sidebar.slider("Filtrar por Faixa de Preço (GPRS):", 0, max_price, (0, max_price))
max_score = int(df_bi['Pontuação Total'].max()) + 1
score_range = st.sidebar.slider("Filtrar por Pontuação de Funcionalidades:", 0, max_score, (0, max_score))

# --- Análise "What-If" ---
st.sidebar.subheader("Análise de Cenário (What-If)")
verdio_default_price = clean_price(df_prices_all[df_prices_all['Empresa'] == 'VERDIO']['Mensalidade (GPRS)'].iloc[0])
novo_preco_verdio = st.sidebar.number_input("Simular novo preço para o VERDIO:", value=verdio_default_price, step=5.0, format="%.2f")

# Aplica os filtros ao DataFrame principal
df_bi_filtered = df_bi[
    (df_bi['Categoria'].isin(categorias)) &
    (df_bi['Mensalidade_GPRS_Num'] >= price_range[0]) &
    (df_bi['Mensalidade_GPRS_Num'] <= price_range[1]) &
    (df_bi['Pontuação Total'] >= score_range[0]) &
    (df_bi['Pontuação Total'] <= score_range[1])
].copy()
# Atualiza o preço do VERDIO para a simulação
if not df_bi_filtered[df_bi_filtered['Empresa'] == 'VERDIO'].empty:
    df_bi_filtered.loc[df_bi_filtered['Empresa'] == 'VERDIO', 'Mensalidade_GPRS_Num'] = novo_preco_verdio


try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>Pesquisa de Mercado e Concorrentes</h1>", unsafe_allow_html=True)
st.markdown("---")
# ... (Secções Mercado Alvo e Diferenciais como antes) ...
st.markdown("---")

# --- 5. EXIBIÇÃO DAS TABELAS E MATRIZ DE CALOR ---
st.subheader("Análise de Funcionalidades")
df_func_heatmap = df_func_all.set_index('Empresa')[[f + '_Score' for f in features_to_score]]
st.dataframe(df_func_heatmap.style.background_gradient(cmap='RdYlGn', axis=1).format("{:.1f}"))
st.markdown("---")

# --- 6. GRÁFICOS DE BI (ATUALIZADOS COM FILTROS) ---
st.subheader("Visualização e Inteligência de Mercado (BI)")

if df_bi_filtered.empty:
    st.warning("Nenhum concorrente corresponde aos filtros selecionados.")
else:
    # --- GRÁFICO 1: CUSTO POR PONTO ---
    st.markdown("##### Análise de Custo por Ponto de Funcionalidade")
    df_custo_ponto = df_bi_filtered.copy()
    df_custo_ponto = df_custo_ponto[df_custo_ponto['Pontuação Total'] > 0] # Evita divisão por zero
    df_custo_ponto['Custo_por_Ponto'] = df_custo_ponto['Mensalidade_GPRS_Num'] / df_custo_ponto['Pontuação Total']
    df_custo_ponto.sort_values('Custo_por_Ponto', ascending=False, inplace=True)

    fig_cost_per_point = go.Figure(go.Bar(
        y=df_custo_ponto['Empresa'], x=df_custo_ponto['Custo_por_Ponto'],
        orientation='h', marker=dict(color=df_custo_ponto['Custo_por_Ponto'], colorscale='Reds_r')
    ))
    fig_cost_per_point.update_layout(title='Custo por Ponto de Funcionalidade (Menor é Melhor)', xaxis_title='R$ por Ponto de Funcionalidade', yaxis_title=None)
    st.plotly_chart(fig_cost_per_point, use_container_width=True)

    # --- GRÁFICO 2: CUSTO-BENEFÍCIO ---
    st.markdown("##### Análise de Custo-Benefício (GPRS)")
    unique_companies = df_bi_filtered['Empresa'].unique()
    color_palette = px.colors.qualitative.Plotly
    color_map = {company: color_palette[i % len(color_palette)] for i, company in enumerate(unique_companies)}
    if 'VERDIO' in color_map:
        color_map['VERDIO'] = '#2ca02c'

    df_bi_filtered['color'] = df_bi_filtered['Empresa'].map(color_map)
    df_bi_filtered['size'] = df_bi_filtered['Pontuação Total'].apply(lambda y: y * 4 + 15)

    fig_bubble_bi = go.Figure()
    for empresa in df_bi_filtered['Empresa'].unique():
        df_empresa = df_bi_filtered[df_bi_filtered['Empresa'] == empresa]
        fig_bubble_bi.add_trace(go.Scatter(
            x=df_empresa['Mensalidade_GPRS_Num'], y=df_empresa['Pontuação Total'],
            name=empresa, text=df_empresa['Empresa'], mode='markers',
            marker=dict(size=df_empresa['size'], color=df_empresa['color'].iloc[0], sizemode='diameter')
        ))
    fig_bubble_bi.update_layout(
        title='Custo (Mensalidade GPRS) vs. Benefício (Pontuação de Funcionalidades)',
        xaxis_title="Preço da Mensalidade GPRS (R$)",
        yaxis_title="Pontuação Total de Funcionalidades",
        height=600, legend_title_text='Concorrentes'
    )
    st.plotly_chart(fig_bubble_bi, use_container_width=True)
