import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import base64

# --- Configurações da Página ---
st.set_page_config(
    page_title="Dashboard Operacional de Frota",
    page_icon="🚚",
    layout="wide"
)

# --- URLs da API (configure se necessário) ---
API_BASE_URL = "http://api.etrac.com.br"
ENDPOINT_ULTIMAS_POSICOES = "/monitoramento/ultimas-posicoes"
ENDPOINT_HISTORICO = "/monitoramento/ultimasposicoesterminal"

# --- Inicialização do Estado da Sessão ---
# Guarda o estado do app: se está conectado, os dados, o mapeamento, etc.
if 'data_loaded' not in st.session_state: st.session_state.data_loaded = False
if 'dashboard_generated' not in st.session_state: st.session_state.dashboard_generated = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'session_cookie' not in st.session_state: st.session_state.session_cookie = ""
if 'df_fleet' not in st.session_state: st.session_state.df_fleet = pd.DataFrame()
if 'df_history' not in st.session_state: st.session_state.df_history = pd.DataFrame()
if 'mapping' not in st.session_state: st.session_state.mapping = {}

# --- Funções de Autenticação e API ---
def get_auth_headers(username, api_key, session_cookie):
    """Cria o dicionário de headers completo, incluindo Authorization e Cookie."""
    if not all([username, api_key, session_cookie]):
        return None
        
    auth_string = f"{username}:{api_key}"
    auth_bytes = auth_string.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_string = base64_bytes.decode('ascii')
    
    headers = {
        'Authorization': f'Basic {base64_string}',
        'Cookie': f'PHPSESSID={session_cookie}'
    }
    return headers

@st.cache_data(ttl=60)
def get_fleet_last_positions(headers):
    """Busca as últimas posições usando o header completo."""
    if headers is None:
        return None
    url = f"{API_BASE_URL}{ENDPOINT_ULTIMAS_POSICOES}"
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            st.warning("A API retornou uma resposta válida, mas sem dados de veículos.")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ou URL não encontrada: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        st.error("Falha ao decodificar a resposta da API. Não é um JSON válido.")
        return None

@st.cache_data(ttl=3600)
def get_vehicle_history(headers, placa, start_date, end_date):
    """Busca o histórico de um veículo usando o header completo."""
    if headers is None:
        return pd.DataFrame()
    url = f"{API_BASE_URL}{ENDPOINT_HISTORICO}"
    payload = {
        "placa": placa,
        "data_inicio": start_date.strftime("%d/%m/%Y %H:%M:%S"),
        "data_fim": end_date.strftime("%d/%m/%Y %H:%M:%S")
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame()
    except requests.exceptions.RequestException:
        return pd.DataFrame()

# --- Barra Lateral (Sidebar) ---
st.sidebar.header("1. Conexão com a API")
input_username = st.sidebar.text_input("E-mail de Acesso", value=st.session_state.username)
input_api_key = st.sidebar.text_input("Chave da API", type="password", value=st.session_state.api_key)
input_session_cookie = st.sidebar.text_input("Cookie de Sessão (PHPSESSID)", type="password", help="Veja como obter este valor nas instruções.")

if st.sidebar.button("Conectar e Buscar Dados", type="primary"):
    st.session_state.dashboard_generated = False
    
    auth_headers = get_auth_headers(input_username, input_api_key, input_session_cookie)
    
    if auth_headers:
        with st.spinner('Autenticando e buscando dados da frota...'):
            df_fleet_temp = get_fleet_last_positions(auth_headers)
            
            if df_fleet_temp is not None and not df_fleet_temp.empty:
                st.session_state.username = input_username
                st.session_state.api_key = input_api_key
                st.session_state.session_cookie = input_session_cookie
                st.session_state.df_fleet = df_fleet_temp
                st.session_state.data_loaded = True
                st.rerun()
            else:
                st.session_state.data_loaded = False
                st.error("Conexão bem-sucedida, mas nenhum dado foi retornado. Verifique as permissões da sua conta, veículos associados ou se o PHPSESSID expirou.")
    else:
        st.sidebar.error("Preencha todos os 3 campos de credenciais.")

if st.sidebar.button("Desconectar / Limpar Tudo"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.sidebar.divider()

if st.session_state.data_loaded:
    st.sidebar.header("2. Mapeamento de Colunas")
    st.sidebar.info("Selecione as colunas da API que correspondem aos campos do dashboard.")
    
    df_fleet = st.session_state.df_fleet
    available_cols = [""] + df_fleet.columns.tolist()

    def find_default_index(options, candidates):
        for candidate in candidates:
            if candidate in options:
                return options.index(candidate)
        return 0

    mapping = {}
    map_placa = st.sidebar.selectbox("Campo 'Placa' do Veículo", available_cols, index=find_default_index(available_cols, ['placa', 'veiculo', 'vehicle', 'descricao']))
    map_lat = st.sidebar.selectbox("Campo 'Latitude'", available_cols, index=find_default_index(available_cols, ['latitude', 'lat']))
    map_lon = st.sidebar.selectbox("Campo 'Longitude'", available_cols, index=find_default_index(available_cols, ['longitude', 'lon', 'lng']))
    map_vel = st.sidebar.selectbox("Campo 'Velocidade'", available_cols, index=find_default_index(available_cols, ['velocidade', 'speed']))
    map_ign = st.sidebar.selectbox("Campo 'Ignição'", available_cols, index=find_default_index(available_cols, ['ignicao', 'ignition']))
    map_odo = st.sidebar.selectbox("Campo 'Odômetro'", available_cols, index=find_default_index(available_cols, ['odometro', 'odometer', 'odometro_can']))
    map_data = st.sidebar.selectbox("Campo 'Data de Gravação'", available_cols, index=find_default_index(available_cols, ['data_gravacao', 'data_transmissao', 'data']))

    st.session_state.mapping = {
        'placa': map_placa, 'latitude': map_lat, 'longitude': map_lon,
        'velocidade': map_vel, 'ignicao': map_ign, 'odometro': map_odo, 'data_gravacao': map_data
    }
    
    st.sidebar.divider()
    st.sidebar.header("3. Filtros e Ação")
    today = datetime.now()
    default_start_date = today - timedelta(days=7)
    date_range = st.sidebar.date_input("Selecione o Período", (default_start_date.date(), today.date()), format="DD/MM/YYYY")
    speed_limit = st.sidebar.number_input("Limite de Velocidade (km/h)", min_value=0, value=80)
    
    if st.sidebar.button("✔️ Gerar Dashboard", type="primary"):
        if all(st.session_state.mapping.values()):
            st.session_state.dashboard_generated = True
            st.session_state.filters = {'date_range': date_range, 'speed_limit': speed_limit}
        else:
            st.sidebar.error("Mapeie todos os campos antes de gerar o dashboard.")
            st.session_state.dashboard_generated = False

# --- Conteúdo Principal do Dashboard ---
st.title("🚚 Dashboard Operacional de Frota")

if not st.session_state.data_loaded:
    st.info("👈 Por favor, insira suas 3 credenciais na barra lateral e conecte-se para começar.")
    st.stop()

with st.expander("Clique para ver as colunas e dados brutos recebidos da API"):
    st.markdown("**Passo 1:** Use esta tabela para identificar os nomes corretos das colunas.")
    st.markdown("**Passo 2:** Vá para a barra lateral e selecione a coluna correspondente em cada campo do 'Mapeamento de Colunas'.")
    st.dataframe(st.session_state.df_fleet)

if not st.session_state.dashboard_generated:
    st.info("☝️ Após conectar, mapeie as colunas e defina os filtros na barra lateral, depois clique em '✔️ Gerar Dashboard'.")
    st.stop()

# --- LÓGICA DE GERAÇÃO DO DASHBOARD ---
mapping = st.session_state.mapping
filters = st.session_state.filters
date_range = filters['date_range']
speed_limit = filters['speed_limit']
start_datetime = datetime.combine(date_range[0], datetime.min.time())
end_datetime = datetime.combine(date_range[1], datetime.max.time())

def process_dataframe(df, mapping):
    rename_map = {v: k for k, v in mapping.items() if v}
    df_renamed = df.rename(columns=rename_map)
    cols_to_numeric = ['latitude', 'longitude', 'velocidade', 'ignicao', 'odometro']
    for col in cols_to_numeric:
        if col in df_renamed.columns:
            df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce')
    if 'data_gravacao' in df_renamed.columns:
        df_renamed['data_gravacao'] = pd.to_datetime(df_renamed['data_gravacao'], errors='coerce')
    return df_renamed

df_fleet_processed = process_dataframe(st.session_state.df_fleet, mapping)
auth_headers = get_auth_headers(st.session_state.username, st.session_state.api_key, st.session_state.session_cookie)

with st.spinner('Carregando e processando dados históricos... Isso pode levar um momento.'):
    all_vehicles_history = []
    placas = df_fleet_processed['placa'].dropna().unique()
    progress_bar = st.progress(0, text="Buscando histórico dos veículos...")
    for i, placa in enumerate(placas):
        history = get_vehicle_history(auth_headers, placa, start_datetime, end_datetime)
        if not history.empty:
            all_vehicles_history.append(history)
        progress_bar.progress((i + 1) / len(placas), text=f"Buscando histórico para: {placa}")
    progress_bar.empty()

    if all_vehicles_history:
        df_history_raw = pd.concat(all_vehicles_history, ignore_index=True)
        df_history_processed = process_dataframe(df_history_raw, mapping)
        df_history_processed = df_history_processed.sort_values(by='data_gravacao').dropna(subset=['data_gravacao'])
    else:
        df_history_processed = pd.DataFrame()

# --- ANÁLISES E GRÁFICOS ---
st.header("Visão Geral da Frota (Agora)")
total_vehicles = df_fleet_processed.shape[0]
vehicles_on = df_fleet_processed[df_fleet_processed['ignicao'] == 1].shape[0]
vehicles_off = total_vehicles - vehicles_on
vehicles_speeding_now = df_fleet_processed[df_fleet_processed['velocidade'] > speed_limit].shape[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Veículos", total_vehicles)
col2.metric("Veículos Ligados", vehicles_on)
col3.metric("Veículos Desligados", vehicles_off)
col4.metric("Em Excesso de Velocidade", vehicles_speeding_now, delta_color="inverse")
st.divider()

st.subheader("Localização da Frota em Tempo Real")
df_map = df_fleet_processed.dropna(subset=['latitude', 'longitude'])
if not df_map.empty:
    st.map(df_map[['latitude', 'longitude']], zoom=4)
else:
    st.warning("Não há dados de localização válidos para exibir no mapa.")
st.divider()

st.header(f"Análise do Período: {date_range[0].strftime('%d/%m/%Y')} a {date_range[1].strftime('%d/%m/%Y')}")
if df_history_processed.empty:
    st.warning("Nenhum dado histórico encontrado para o período selecionado.")
else:
    df_history = df_history_processed
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Ranking: Infrações de Velocidade")
        speeding_events = df_history[df_history['velocidade'] > speed_limit]
        if not speeding_events.empty:
            speeding_counts = speeding_events['placa'].value_counts().reset_index()
            speeding_counts.columns = ['Veículo', 'Nº de Ocorrências']
            fig_speed = px.bar(speeding_counts, x='Nº de Ocorrências', y='Veículo', orientation='h', title=f"Veículos que ultrapassaram {speed_limit} km/h")
            fig_speed.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_speed, use_container_width=True)
        else:
            st.info(f"Nenhum veículo ultrapassou {speed_limit} km/h no período.")

    with col_b:
        st.subheader("Distância Percorrida (KM)")
        km_per_vehicle = df_history.groupby('placa')['odometro'].agg(['min', 'max']).dropna()
        km_per_vehicle['Distância (KM)'] = km_per_vehicle['max'] - km_per_vehicle['min']
        km_per_vehicle = km_per_vehicle[km_per_vehicle['Distância (KM)'] > 0].sort_values(by='Distância (KM)', ascending=False).reset_index()
        if not km_per_vehicle.empty:
            fig_km = px.bar(km_per_vehicle, x='Distância (KM)', y='placa', orientation='h', title="Quilometragem por Veículo")
            fig_km.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_km, use_container_width=True)
        else:
            st.info("Dados de odômetro insuficientes para calcular a distância.")

    st.divider()
    
    st.subheader("Ranking: Tempo de Motor Ocioso")
    idle_df = df_history[(df_history['ignicao'] == 1) & (df_history['velocidade'] <= 5)].copy()
    if not idle_df.empty:
        idle_df['time_diff'] = idle_df.groupby('placa')['data_gravacao'].diff().dt.total_seconds()
        max_time_gap_seconds = 15 * 60
        idle_df['idle_seconds'] = idle_df['time_diff'].apply(lambda x: x if pd.notnull(x) and x < max_time_gap_seconds else 0)
        idle_summary = idle_df.groupby('placa')['idle_seconds'].sum().reset_index()
        idle_summary['idle_hours'] = idle_summary['idle_seconds'] / 3600
        idle_summary = idle_summary[idle_summary['idle_hours'] > 0].sort_values(by='idle_hours', ascending=False)
        if not idle_summary.empty:
            fig_idle = px.bar(idle_summary, x='idle_hours', y='placa', orientation='h', title="Total de Horas com Motor Ocioso", labels={'idle_hours': 'Horas Ociosas'})
            fig_idle.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_idle, use_container_width=True)
        else:
            st.info("Não foram encontrados registros de tempo ocioso.")
    else:
        st.info("Não foram encontrados registros de tempo ocioso.")
