# pages/Pesquisa_de_Mercado.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Pesquisa de Mercado",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. DADOS CENTRALIZADOS (COM COORDENADAS PARA O MAPA) ---
MARKET_DATA = {
    "precos_nacionais": [
        {'Empresa': 'VERDIO (Referência)', 'Instalação (GPRS)': 'Tratativa Comercial', 'Mensalidade (GPRS)': 'R$ 44,93 - R$ 584,49', 'Instalação (Satelital)': 'Tratativa Comercial', 'Mensalidade (Satelital)': 'R$ 107,67 - R$ 193,80'},
        {'Empresa': 'Sascar', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 79,90', 'Instalação (Satelital)': 'R$ 824,19', 'Mensalidade (Satelital)': 'R$ 193,80'},
        {'Empresa': 'Omnilink', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 89,90', 'Instalação (Satelital)': 'R$ 554,00', 'Mensalidade (Satelital)': 'R$ 193,80'},
        {'Empresa': 'Onixsat', 'Instalação (GPRS)': '–', 'Mensalidade (GPRS)': '–', 'Instalação (Satelital)': 'R$ 0,00', 'Mensalidade (Satelital)': 'R$ 120,00'},
        {'Empresa': 'Veltec', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 110,00', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'Positron', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 75,00', 'Instalação (Satelital)': 'R$ 256,27', 'Mensalidade (Satelital)': 'R$ 191,05'},
        {'Empresa': 'Autotrac', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 99,90', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'Maxtrack', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 59,90', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
    ],
    "precos_regionais": [
        {'Empresa': 'VERDIO (Referência)', 'Instalação (GPRS)': 'Tratativa Comercial', 'Mensalidade (GPRS)': 'R$ 44,93 - R$ 584,49', 'Instalação (Satelital)': 'Tratativa Comercial', 'Mensalidade (Satelital)': 'R$ 107,67 - R$ 193,80'},
        {'Empresa': 'Elite Rastro', 'Instalação (GPRS)': 'R$ 30,00', 'Mensalidade (GPRS)': 'R$ 50,00', 'Instalação (Satelital)': 'R$ 900,00', 'Mensalidade (Satelital)': 'R$ 180,00'},
        {'Empresa': 'NJ Rastreamento', 'Instalação (GPRS)': 'R$ 120,00', 'Mensalidade (GPRS)': 'R$ 75,00', 'Instalação (Satelital)': 'R$ 650,00', 'Mensalidade (Satelital)': 'R$ 170,00'},
        {'Empresa': 'TK Rastreadores', 'Instalação (GPRS)': 'R$ 80,00', 'Mensalidade (GPRS)': 'R$ 69,90', 'Instalação (Satelital)': 'R$ 980,00', 'Mensalidade (Satelital)': 'R$ 150,00'},
        {'Empresa': 'vtrackrastreamento', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 50,00', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'rastrek', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 60,00', 'Instalação (Satelital)': 'R$ 0,00', 'Mensalidade (Satelital)': 'R$ 130,00'},
        {'Empresa': 'Pro Lion', 'Instalação (GPRS)': 'R$ 99,90', 'Mensalidade (GPRS)': 'R$ 49,90 - R$ 69,90', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
        {'Empresa': 'Impacto Rast.', 'Instalação (GPRS)': 'R$ 0,00', 'Mensalidade (GPRS)': 'R$ 45,00', 'Instalação (Satelital)': '–', 'Mensalidade (Satelital)': '–'},
    ],
    "funcionalidades_nacionais": [
        {'Empresa': 'VERDIO (Rovema)', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '✅ Sim', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Sascar', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Omnilink', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Onixsat', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Veltec', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Positron', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❔ Opcional', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Autotrac', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Maxtrack', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
    ],
    "funcionalidades_regionais": [
        {'Empresa': 'VERDIO (Rovema)', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '✅ Sim', 'Sensor de Fadiga': '✅ Sim', 'Controle de Jornada': '✅ Sim', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Elite Rastro', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'NJ Rastreamento', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'TK Rastreadores', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '✅ Sim', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '❔ Comercial', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'vtrackrastreamento', 'Telemetria (CAN)': '✅ Sim', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'rastrek', 'Telemetria (CAN)': '❔ Parcial', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '✅ Sim', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Pro Lion', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
        {'Empresa': 'Impacto Rast.', 'Telemetria (CAN)': '❌ Não', 'Vídeo': '❌ Não', 'Sensor de Fadiga': '❌ Não', 'Controle de Jornada': '❌ Não', 'Roteirizador': '❌ Não', 'Com. Satelital': '❌ Não', 'Suporte 24h': '✅ Sim', 'App de Gestão': '✅ Sim'},
    ],
    "localizacoes_regionais": [
        {"Empresa": "VERDIO (CSC Rovema)", "lat": -8.75242, "lon": -63.90317, "cor": "green"},
        {'Empresa': 'Elite Rastro', "lat": -8.76797, "lon": -63.84175, "cor": "blue"},
        {'Empresa': 'NJ Rastreamento', "lat": -8.76494, "lon": -63.87658, "cor": "blue"},
        {'Empresa': 'TK Rastreadores', "lat": -8.75304, "lon": -63.90038, "cor": "blue"},
        {'Empresa': 'vtrackrastreamento', "lat": -8.74052, "lon": -63.84815, "cor": "blue"},
        {'Empresa': 'rastrek', "lat": -8.75011, "lon": -63.84796, "cor": "blue"},
        {'Empresa': 'Pro Lion', "lat": -8.75608, "lon": -63.87928, "cor": "blue"},
        {'Empresa': 'Impacto Rast.', "lat": -8.76647, "lon": -63.88595, "cor": "blue"},
    ]
}

# --- 3. CONVERSÃO E PROCESSAMENTO DE DADOS ---
df_preco_nacionais = pd.DataFrame(MARKET_DATA["precos_nacionais"])
df_preco_regionais = pd.DataFrame(MARKET_DATA["precos_regionais"])
df_funci_nacionais = pd.DataFrame(MARKET_DATA["funcionalidades_nacionais"])
df_funci_regionais = pd.DataFrame(MARKET_DATA["funcionalidades_regionais"])
df_localizacoes = pd.DataFrame(MARKET_DATA["localizacoes_regionais"])
df_prices_all = pd.concat([df_preco_nacionais, df_preco_regionais]).drop_duplicates(subset=['Empresa']).reset_index(drop=True)

df_localizacoes['Merge_Key'] = df_localizacoes['Empresa'].str.replace(r'\s*\(.*\)', '', regex=True).str.strip()
df_prices_all['Merge_Key'] = df_prices_all['Empresa'].str.replace(r'\s*\(.*\)', '', regex=True).str.strip()
df_mapa = pd.merge(df_localizacoes, df_prices_all, on='Merge_Key', how='left', suffixes=('', '_price'))

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

st.markdown("---")

# --- 6. GRÁFICOS DE BUSINESS INTELLIGENCE (BI) ---
st.subheader("Visualização e Inteligência de Mercado (BI)")

# --- GRÁFICO 1: PONTUAÇÃO DE FUNCIONALIDADES ---
st.markdown("##### Pontuação Total de Funcionalidades")
df_func_all = pd.concat([df_funci_nacionais, df_funci_regionais]).drop_duplicates(subset=['Empresa']).reset_index(drop=True)
score_map = {'✅ Sim': 1.0, '❔ Opcional': 0.5, '❔ Parcial': 0.5, '❌ Não': 0.0, '❔ Comercial': 0.0}
features_to_score = ['Telemetria (CAN)', 'Vídeo', 'Sensor de Fadiga', 'Controle de Jornada', 'Roteirizador', 'Com. Satelital', 'Suporte 24h', 'App de Gestão']

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

# --- GRÁFICO 2: CUSTO-BENEFÍCIO (GPRS) ---
st.markdown("##### Análise de Custo-Benefício (GPRS)")
def clean_price(price_str):
    try:
        return float(re.findall(r'\d+[\.,]\d+', str(price_str))[0].replace(',', '.'))
    except (IndexError, TypeError):
        return None

df_prices_all_for_bi = df_prices_all.copy()
df_prices_all_for_bi['Mensalidade_GPRS_Num'] = df_prices_all_for_bi['Mensalidade (GPRS)'].apply(clean_price)
df_func_all['Merge_Key'] = df_func_all['Empresa'].str.replace(r'\s*\(.*\)', '', regex=True)
df_prices_all_for_bi['Merge_Key'] = df_prices_all_for_bi['Empresa'].str.replace(r'\s*\(.*\)', '', regex=True)

df_bi = pd.merge(df_func_all, df_prices_all_for_bi, on='Merge_Key', how='inner', suffixes=('', '_price'))
df_bi.dropna(subset=['Mensalidade_GPRS_Num'], inplace=True)
df_bi['Empresa'] = df_bi['Empresa_price']

unique_companies = df_bi['Empresa'].unique()
color_palette = px.colors.qualitative.Plotly
color_map = {company: color_palette[i % len(color_palette)] for i, company in enumerate(unique_companies)}
if 'VERDIO (Referência)' in color_map:
    color_map['VERDIO (Referência)'] = '#2ca02c'

df_bi['color'] = df_bi['Empresa'].map(color_map)
df_bi['size'] = df_bi['Pontuação Total'].apply(lambda y: y * 4 + 15)

fig_bubble_bi = go.Figure()
for empresa in df_bi['Empresa'].unique():
    df_empresa = df_bi[df_bi['Empresa'] == empresa]
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

# --- GRÁFICO 3: COMPARATIVO DE CUSTOS - SATELITAL ---
st.markdown("##### Análise de Custos - Comunicação Satelital")
df_prices_all['Instalacao_Satelital_Num'] = df_prices_all['Instalação (Satelital)'].apply(clean_price)
df_prices_all['Mensalidade_Satelital_Num'] = df_prices_all['Mensalidade (Satelital)'].apply(clean_price)
df_satelital = df_prices_all.dropna(subset=['Mensalidade_Satelital_Num'])

fig_satelital = go.Figure()
fig_satelital.add_trace(go.Bar(
    x=df_satelital['Empresa'], y=df_satelital['Instalacao_Satelital_Num'],
    name='Custo de Instalação (R$)', marker_color='indianred'
))
fig_satelital.add_trace(go.Bar(
    x=df_satelital['Empresa'], y=df_satelital['Mensalidade_Satelital_Num'],
    name='Custo da Mensalidade (R$)', marker_color='lightsalmon'
))
fig_satelital.update_layout(
    title='Comparativo de Custos - Rastreadores via Satélite',
    xaxis_title='Empresa', yaxis_title='Valor (R$)', barmode='group',
    legend_title_text='Tipo de Custo', height=500
)
st.plotly_chart(fig_satelital, use_container_width=True)

# --- 7. MAPA DE CONCORRENTES REGIONAIS (COM ETIQUETAS FIXAS) ---
st.markdown("---")
st.subheader("Mapa de Concorrentes Regionais")
st.write("Visualização da distribuição geográfica dos concorrentes em Porto Velho, com informações de preço.")

porto_velho_centro = [-8.755, -63.875]
zoom_level = 13

mapa = folium.Map(location=porto_velho_centro, zoom_start=zoom_level, tiles="CartoDB positron")

for index, row in df_mapa.iterrows():
    tooltip_html = f"""
    <div style="font-family: sans-serif; font-size: 12px;">
        <strong>{row['Empresa']}</strong><br>
        <hr style='margin: 2px 0;'>
        <strong>GPRS:</strong> {row.get('Mensalidade (GPRS)', 'N/A')}<br>
        <strong>Satelital:</strong> {row.get('Mensalidade (Satelital)', 'N/A')}
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        icon=folium.Icon(color=row['cor'], icon='building', prefix='fa')
    ).add_to(mapa)
    
    folium.Tooltip(
        text=tooltip_html,
        permanent=True,
        direction='right',
        offset=(10, 0),
        style="""
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px 3px rgba(0, 0, 0, 0.2);
            padding: 5px;
        """
    ).add_to(
        folium.CircleMarker(location=[row['lat'], row['lon']], radius=1, fill_opacity=0, opacity=0)
    )

st_folium(mapa, use_container_width=True, height=500)
