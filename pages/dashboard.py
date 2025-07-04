import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Configurações da Página e Título ---
st.set_page_config(
    page_title="Dashboard Operacional de Frota",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Dashboard Operacional de Frota")

# --- Funções para Acessar a API eTrac ---

# URL base da API
API_BASE_URL = "http://api.etrac.com.br/monitoramento"

# Carrega as credenciais de forma segura a partir do secrets.toml
try:
    USERNAME = st.secrets["ETRAC_USERNAME"]
    API_KEY = st.secrets["ETRAC_API_KEY"]
except FileNotFoundError:
    st.error("Arquivo de segredos (secrets.toml) não encontrado. Por favor, crie-o na pasta .streamlit/")
    st.stop()
except KeyError:
    st.error("Credenciais 'ETRAC_USERNAME' ou 'ETRAC_API_KEY' não encontradas no arquivo de segredos.")
    st.stop()


# Função para obter a última posição de toda a frota
@st.cache_data(ttl=60) # Cache de 60 segundos para não sobrecarregar a API
def get_fleet_last_positions():
    """Busca as últimas posições de todos os veículos da frota."""
    url = f"{API_BASE_URL}/ultimas-posicoes"
    try:
        response = requests.post(url, auth=(USERNAME, API_KEY))
        response.raise_for_status()  # Lança um erro para status HTTP 4xx/5xx
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame() # Retorna DF vazio se não houver dados
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar dados da frota: {e}")
        return pd.DataFrame()

# Função para buscar o histórico de posições de um veículo
@st.cache_data(ttl=3600) # Cache de 1 hora
def get_vehicle_history(placa, start_date, end_date):
    """Busca o histórico de posições para um veículo em um período."""
    url = f"{API_BASE_URL}/ultimasposicoesterminal"
    payload = {
        "placa": placa,
        "data_inicio": start_date.strftime("%d/%m/%Y %H:%M:%S"),
        "data_fim": end_date.strftime("%d/%m/%Y %H:%M:%S")
    }
    try:
        response = requests.post(url, auth=(USERNAME, API_KEY), json=payload)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        # Não mostra erro na tela para não poluir, mas registra no log (console)
        print(f"Erro ao buscar histórico para {placa}: {e}")
        return pd.DataFrame()

# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros do Dashboard")

# Filtro de Data
# Define o período padrão para os últimos 7 dias
today = datetime.now()
default_start_date = today - timedelta(days=7)

date_range = st.sidebar.date_input(
    "Selecione o Período de Análise",
    (default_start_date.date(), today.date()),
    format="DD/MM/YYYY"
)

# Converte as datas para datetime para usar nos filtros da API
try:
    start_datetime = datetime.combine(date_range[0], datetime.min.time())
    end_datetime = datetime.combine(date_range[1], datetime.max.time())
except IndexError:
    st.warning("Por favor, selecione um período válido.")
    st.stop()


# Filtro de Limite de Velocidade
speed_limit = st.sidebar.number_input("Definir Limite de Velocidade (km/h)", min_value=0, value=80)


# --- Carregamento e Processamento dos Dados ---
with st.spinner('Carregando dados da frota... Por favor, aguarde.'):
    df_fleet = get_fleet_last_positions()

    if df_fleet.empty:
        st.error("Não foi possível carregar os dados da frota. Verifique suas credenciais ou a API da eTrac.")
        st.stop()

    # Conversão de tipos de dados para análise
    df_fleet['latitude'] = pd.to_numeric(df_fleet['latitude'], errors='coerce')
    df_fleet['longitude'] = pd.to_numeric(df_fleet['longitude'], errors='coerce')
    df_fleet['velocidade'] = pd.to_numeric(df_fleet['velocidade'], errors='coerce')
    df_fleet['ignicao'] = pd.to_numeric(df_fleet['ignicao'], errors='coerce')

    # Coleta de dados históricos para todos os veículos no período selecionado
    all_vehicles_history = []
    placas = df_fleet['placa'].unique()

    progress_bar = st.progress(0, text="Buscando histórico dos veículos...")
    for i, placa in enumerate(placas):
        history = get_vehicle_history(placa, start_datetime, end_datetime)
        if not history.empty:
            all_vehicles_history.append(history)
        progress_bar.progress((i + 1) / len(placas), text=f"Buscando histórico para: {placa}")
    
    progress_bar.empty() # Limpa a barra de progresso

    if not all_vehicles_history:
        st.warning("Nenhum dado histórico encontrado para o período selecionado.")
        df_history = pd.DataFrame()
    else:
        df_history = pd.concat(all_vehicles_history, ignore_index=True)
        # Limpeza e conversão de tipos para o histórico
        df_history['velocidade'] = pd.to_numeric(df_history['velocidade'], errors='coerce')
        df_history['ignicao'] = pd.to_numeric(df_history['ignicao'], errors='coerce')
        df_history['odometro'] = pd.to_numeric(df_history['odometro'], errors='coerce')
        df_history['data_gravacao'] = pd.to_datetime(df_history['data_gravacao'], errors='coerce')
        df_history = df_history.sort_values(by=['placa', 'data_gravacao']).dropna(subset=['data_gravacao'])


# --- ANÁLISES E GRÁFICOS ---

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

if df_history.empty:
    st.warning("Não há dados históricos para gerar as análises do período.")
else:
    col_a, col_b = st.columns(2)

    # 3. Gráfico de Velocidade Acima do Limite
    with col_a:
        st.subheader("Ranking: Infrações de Velocidade")
        speeding_events = df_history[df_history['velocidade'] > speed_limit]
        speeding_counts = speeding_events['placa'].value_counts().reset_index()
        speeding_counts.columns = ['Veículo', 'Nº de Ocorrências']

        if not speeding_counts.empty:
            fig_speed = px.bar(
                speeding_counts,
                x='Nº de Ocorrências',
                y='Veículo',
                orientation='h',
                title=f"Veículos que ultrapassaram {speed_limit} km/h",
                labels={'Nº de Ocorrências': 'Número de Registros Acima do Limite'}
            )
            fig_speed.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_speed, use_container_width=True)
        else:
            st.info(f"Nenhum veículo ultrapassou {speed_limit} km/h no período selecionado.")

    # 4. Quilômetros Percorridos por Veículo
    with col_b:
        st.subheader("Distância Percorrida por Veículo (KM)")
        # Calculando a distância pelo odômetro
        km_per_vehicle = df_history.groupby('placa')['odometro'].agg(['min', 'max']).reset_index()
        km_per_vehicle['Distância (KM)'] = km_per_vehicle['max'] - km_per_vehicle['min']
        km_per_vehicle = km_per_vehicle.sort_values(by='Distância (KM)', ascending=False)
        
        if not km_per_vehicle.empty and km_per_vehicle['Distância (KM)'].sum() > 0:
            fig_km = px.bar(
                km_per_vehicle,
                x='Distância (KM)',
                y='placa',
                orientation='h',
                title="Quilometragem Total por Veículo no Período",
            )
            fig_km.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_km, use_container_width=True)
        else:
            st.info("Não foi possível calcular a distância percorrida (dados de odômetro insuficientes).")

    st.divider()

    # 5. Ranking de Maior Tempo de Motor Ocioso
    st.subheader("Ranking: Tempo de Motor Ocioso")
    
    # Motor ocioso: Ignição ligada (1) e velocidade baixa (ex: <= 5 km/h)
    idle_df = df_history[(df_history['ignicao'] == 1) & (df_history['velocidade'] <= 5)].copy()
    idle_df = idle_df.sort_values(by=['placa', 'data_gravacao'])
    
    # Calcula a diferença de tempo para o registro anterior
    idle_df['time_diff'] = idle_df.groupby('placa')['data_gravacao'].diff()
    
    # Consideramos a diferença de tempo válida se for menor que um limite (ex: 15 minutos)
    # para não contar grandes períodos offline como tempo ocioso.
    max_time_gap = timedelta(minutes=15)
    idle_df['idle_time'] = idle_df['time_diff'].apply(lambda x: x if pd.notnull(x) and x < max_time_gap else timedelta(0))
    
    idle_summary = idle_df.groupby('placa')['idle_time'].sum().reset_index()
    # Converte o timedelta para horas para o gráfico
    idle_summary['idle_hours'] = idle_summary['idle_time'].apply(lambda x: x.total_seconds() / 3600)
    idle_summary = idle_summary.sort_values(by='idle_hours', ascending=False)

    if not idle_summary.empty and idle_summary['idle_hours'].sum() > 0:
        fig_idle = px.bar(
            idle_summary,
            x='idle_hours',
            y='placa',
            orientation='h',
            title="Total de Horas com Motor Ocioso por Veículo",
            labels={'idle_hours': 'Horas Ociosas (Ignição Ligada, Veículo Parado)'}
        )
        fig_idle.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_idle, use_container_width=True)
    else:
        st.info("Não foram encontrados registros de tempo ocioso no período.")


    # 6. Gráfico de Atividade Diária (KM Percorridos)
    st.subheader("Atividade da Frota por Dia")
    df_history['data'] = df_history['data_gravacao'].dt.date
    daily_km = df_history.groupby(['placa', 'data'])['odometro'].agg(['min', 'max']).reset_index()
    daily_km['km_dia'] = daily_km['max'] - daily_km['min']
    
    total_daily_km = daily_km.groupby('data')['km_dia'].sum().reset_index()

    if not total_daily_km.empty:
        fig_daily_activity = px.line(
            total_daily_km,
            x='data',
            y='km_dia',
            title='Total de Quilômetros Percorridos pela Frota por Dia',
            markers=True,
            labels={'data': 'Data', 'km_dia': 'Distância Total (KM)'}
        )
        st.plotly_chart(fig_daily_activity, use_container_width=True)
    else:
        st.info("Não há dados de odômetro para gerar a atividade diária.")

# --- Tabela de Dados Brutos ---
st.divider()
if st.checkbox("Mostrar dados brutos da frota (última posição)"):
    st.subheader("Dados Brutos - Última Posição")
    st.dataframe(df_fleet)

if not df_history.empty and st.checkbox("Mostrar dados brutos do histórico (período selecionado)"):
    st.subheader("Dados Brutos - Histórico do Período")
    st.dataframe(df_history)
