import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Configurações da Página ---
st.set_page_config(
    page_title="Dashboard Operacional de Frota",
    page_icon="🚚",
    layout="wide"
)

# URL base da API
API_BASE_URL = "http://api.etrac.com.br/monitoramento"

# --- Inicialização do Estado da Sessão ---
# Usamos o session_state para controlar o fluxo do app
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'df_fleet' not in st.session_state:
    st.session_state.df_fleet = pd.DataFrame()
if 'df_history' not in st.session_state:
    st.session_state.df_history = pd.DataFrame()


# --- Funções para Acessar a API eTrac ---
# As funções agora recebem as credenciais como argumentos

# Cacheia os dados por 60 segundos. O cache depende das credenciais.
@st.cache_data(ttl=60)
def get_fleet_last_positions(username, api_key):
    """Busca as últimas posições de todos os veículos da frota."""
    url = f"{API_BASE_URL}/ultimas-posicoes"
    try:
        response = requests.post(url, auth=(username, api_key))
        response.raise_for_status()
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ou credenciais inválidas: {e}")
        return None # Retorna None em caso de erro

@st.cache_data(ttl=3600)
def get_vehicle_history(username, api_key, placa, start_date, end_date):
    """Busca o histórico de posições para um veículo em um período."""
    url = f"{API_BASE_URL}/ultimasposicoesterminal"
    payload = {
        "placa": placa,
        "data_inicio": start_date.strftime("%d/%m/%Y %H:%M:%S"),
        "data_fim": end_date.strftime("%d/%m/%Y %H:%M:%S")
    }
    try:
        response = requests.post(url, auth=(username, api_key), json=payload)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar histórico para {placa}: {e}")
        return pd.DataFrame()


# --- Barra Lateral (Sidebar) ---
st.sidebar.header("Credenciais da API eTrac")
input_username = st.sidebar.text_input("E-mail de Acesso", value=st.session_state.username)
input_api_key = st.sidebar.text_input("Chave da API", type="password", value=st.session_state.api_key)

if st.sidebar.button("Conectar e Carregar Dados", type="primary"):
    # Quando o botão é pressionado, tentamos carregar os dados
    with st.spinner('Autenticando e buscando dados da frota...'):
        df_fleet_temp = get_fleet_last_positions(input_username, input_api_key)
        
        # Se o carregamento for bem-sucedido (não retorna None)
        if df_fleet_temp is not None:
            st.session_state.username = input_username
            st.session_state.api_key = input_api_key
            st.session_state.df_fleet = df_fleet_temp
            st.session_state.data_loaded = True
            st.rerun() # Reinicia o script para redesenhar a página
        else:
            st.session_state.data_loaded = False
            # O erro já é exibido dentro da função get_fleet_last_positions

st.sidebar.divider()

# O restante da barra lateral só aparece se os dados foram carregados com sucesso
if st.session_state.data_loaded:
    st.sidebar.header("Filtros do Dashboard")
    # Filtro de Data
    today = datetime.now()
    default_start_date = today - timedelta(days=7)
    date_range = st.sidebar.date_input(
        "Selecione o Período de Análise",
        (default_start_date.date(), today.date()),
        format="DD/MM/YYYY"
    )
    try:
        start_datetime = datetime.combine(date_range[0], datetime.min.time())
        end_datetime = datetime.combine(date_range[1], datetime.max.time())
    except IndexError:
        st.warning("Por favor, selecione um período válido.")
        st.stop()
    
    # Filtro de Limite de Velocidade
    speed_limit = st.sidebar.number_input("Definir Limite de Velocidade (km/h)", min_value=0, value=80)
    
    # Botão de Logout/Limpar
    if st.sidebar.button("Desconectar / Limpar Dados"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- Conteúdo Principal do Dashboard ---
st.title("🚚 Dashboard Operacional de Frota")

if not st.session_state.data_loaded:
    st.info("Por favor, insira suas credenciais na barra lateral e clique em 'Conectar e Carregar Dados' para começar.")
    st.stop()

# Se chegou aqui, os dados estão carregados. Agora podemos processar e exibir.
df_fleet = st.session_state.df_fleet

with st.spinner('Processando dados históricos... Isso pode levar um momento.'):
    # Conversão de tipos de dados para análise
    df_fleet['latitude'] = pd.to_numeric(df_fleet['latitude'], errors='coerce')
    df_fleet['longitude'] = pd.to_numeric(df_fleet['longitude'], errors='coerce')
    df_fleet['velocidade'] = pd.to_numeric(df_fleet['velocidade'], errors='coerce')
    df_fleet['ignicao'] = pd.to_numeric(df_fleet['ignicao'], errors='coerce')

    # Coleta de dados históricos
    all_vehicles_history = []
    placas = df_fleet['placa'].unique()
    progress_bar = st.progress(0, text="Buscando histórico dos veículos...")
    for i, placa in enumerate(placas):
        history = get_vehicle_history(st.session_state.username, st.session_state.api_key, placa, start_datetime, end_datetime)
        if not history.empty:
            all_vehicles_history.append(history)
        progress_bar.progress((i + 1) / len(placas), text=f"Buscando histórico para: {placa}")
    progress_bar.empty()
    
    if not all_vehicles_history:
        st.session_state.df_history = pd.DataFrame()
    else:
        df_history = pd.concat(all_vehicles_history, ignore_index=True)
        df_history['velocidade'] = pd.to_numeric(df_history['velocidade'], errors='coerce')
        df_history['ignicao'] = pd.to_numeric(df_history['ignicao'], errors='coerce')
        df_history['odometro'] = pd.to_numeric(df_history['odometro'], errors='coerce')
        df_history['data_gravacao'] = pd.to_datetime(df_history['data_gravacao'], errors='coerce')
        df_history = df_history.sort_values(by=['placa', 'data_gravacao']).dropna(subset=['data_gravacao'])
        st.session_state.df_history = df_history

# --- ANÁLISES E GRÁFICOS (exatamente como antes, mas usando st.session_state.df_history) ---

# 1. KPIs Principais
st.header("Visão Geral da Frota")
total_vehicles = df_fleet.shape[0]
vehicles_on = df_fleet[df_fleet['ignicao'] == 1].shape[0]
vehicles_off = total_vehicles - vehicles_on
vehicles_speeding_now = df_fleet[df_fleet['velocidade'] > speed_limit].shape[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Veículos", total_vehicles)
col2.metric("Veículos Ligados", vehicles_on)
col3.metric("Veículos Desligados", vehicles_off)
col4.metric("Em Excesso de Velocidade (Agora)", vehicles_speeding_now, delta_color="inverse")
st.divider()

# 2. Mapa da Frota em Tempo Real
st.subheader("Localização da Frota em Tempo Real")
df_map = df_fleet.dropna(subset=['latitude', 'longitude'])
if not df_map.empty:
    st.map(df_map[['latitude', 'longitude']], zoom=4)
else:
    st.info("Não há dados de localização para exibir no mapa.")
st.divider()

# --- ANÁLISE DO PERÍODO SELECIONADO ---
st.header(f"Análise do Período: {date_range[0].strftime('%d/%m/%Y')} a {date_range[1].strftime('%d/%m/%Y')}")

df_history = st.session_state.df_history
if df_history.empty:
    st.warning("Não há dados históricos para gerar as análises do período selecionado.")
else:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Ranking: Infrações de Velocidade")
        speeding_events = df_history[df_history['velocidade'] > speed_limit]
        speeding_counts = speeding_events['placa'].value_counts().reset_index()
        speeding_counts.columns = ['Veículo', 'Nº de Ocorrências']
        if not speeding_counts.empty:
            fig_speed = px.bar(speeding_counts, x='Nº de Ocorrências', y='Veículo', orientation='h', title=f"Veículos que ultrapassaram {speed_limit} km/h")
            fig_speed.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_speed, use_container_width=True)
        else:
            st.info(f"Nenhum veículo ultrapassou {speed_limit} km/h no período.")

    with col_b:
        st.subheader("Distância Percorrida por Veículo (KM)")
        km_per_vehicle = df_history.groupby('placa')['odometro'].agg(['min', 'max']).reset_index()
        km_per_vehicle['Distância (KM)'] = km_per_vehicle['max'] - km_per_vehicle['min']
        km_per_vehicle = km_per_vehicle.sort_values(by='Distância (KM)', ascending=False)
        if not km_per_vehicle.empty and km_per_vehicle['Distância (KM)'].sum() > 0:
            fig_km = px.bar(km_per_vehicle, x='Distância (KM)', y='placa', orientation='h', title="Quilometragem Total por Veículo")
            fig_km.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_km, use_container_width=True)
        else:
            st.info("Dados de odômetro insuficientes para calcular a distância.")
    
    st.divider()
    
    st.subheader("Ranking: Tempo de Motor Ocioso")
    idle_df = df_history[(df_history['ignicao'] == 1) & (df_history['velocidade'] <= 5)].copy()
    idle_df['time_diff'] = idle_df.groupby('placa')['data_gravacao'].diff().dt.total_seconds()
    max_time_gap_seconds = 15 * 60
    idle_df['idle_seconds'] = idle_df['time_diff'].apply(lambda x: x if pd.notnull(x) and x < max_time_gap_seconds else 0)
    idle_summary = idle_df.groupby('placa')['idle_seconds'].sum().reset_index()
    idle_summary['idle_hours'] = idle_summary['idle_seconds'] / 3600
    idle_summary = idle_summary.sort_values(by='idle_hours', ascending=False)
    if not idle_summary.empty and idle_summary['idle_hours'].sum() > 0:
        fig_idle = px.bar(idle_summary, x='idle_hours', y='placa', orientation='h', title="Total de Horas com Motor Ocioso por Veículo", labels={'idle_hours': 'Horas Ociosas'})
        fig_idle.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_idle, use_container_width=True)
    else:
        st.info("Não foram encontrados registros de tempo ocioso.")

    st.subheader("Atividade da Frota por Dia (KM)")
    df_history['data'] = df_history['data_gravacao'].dt.date
    daily_km = df_history.groupby(['placa', 'data'])['odometro'].agg(['min', 'max']).reset_index()
    daily_km['km_dia'] = daily_km['max'] - daily_km['min']
    total_daily_km = daily_km.groupby('data')['km_dia'].sum().reset_index()
    if not total_daily_km.empty:
        fig_daily = px.line(total_daily_km, x='data', y='km_dia', title='Total de KM Percorridos pela Frota por Dia', markers=True)
        st.plotly_chart(fig_daily, use_container_width=True)

# --- Tabela de Dados Brutos ---
st.divider()
if st.checkbox("Mostrar dados brutos da frota (última posição)"):
    st.dataframe(df_fleet)

if not df_history.empty and st.checkbox("Mostrar dados brutos do histórico (período selecionado)"):
    st.dataframe(df_history)
