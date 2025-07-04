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
@st.cache_data(ttl=60)
def get_fleet_last_positions(username, api_key):
    url = f"{API_BASE_URL}/ultimas-posicoes"
    try:
        response = requests.post(url, auth=(username, api_key))
        response.raise_for_status()
        data = response.json()
        if 'data' in data and data['data']:
            return pd.DataFrame(data['data'])
        else:
            # ### ALTERAÇÃO ###: Adiciona log se a resposta não tiver dados
            st.warning("A API retornou uma resposta válida, mas sem dados de veículos ('data' está vazio).")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ou credenciais inválidas: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        st.error("Falha ao decodificar a resposta da API. A resposta pode não ser um JSON válido.")
        return None

@st.cache_data(ttl=3600)
def get_vehicle_history(username, api_key, placa, start_date, end_date):
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
    with st.spinner('Autenticando e buscando dados da frota...'):
        df_fleet_temp = get_fleet_last_positions(input_username, input_api_key)
        
        if df_fleet_temp is not None:
            st.session_state.username = input_username
            st.session_state.api_key = input_api_key
            st.session_state.df_fleet = df_fleet_temp
            st.session_state.data_loaded = True if not df_fleet_temp.empty else False
            st.rerun()
        else:
            st.session_state.data_loaded = False

st.sidebar.divider()

if st.session_state.data_loaded:
    st.sidebar.header("Filtros do Dashboard")
    today = datetime.now()
    default_start_date = today - timedelta(days=7)
    date_range = st.sidebar.date_input(
        "Selecione o Período de Análise",
        (default_start_date.date(), today.date()),
        format="DD/MM/YYYY"
    )
    start_datetime = datetime.combine(date_range[0], datetime.min.time())
    end_datetime = datetime.combine(date_range[1], datetime.max.time())
    speed_limit = st.sidebar.number_input("Definir Limite de Velocidade (km/h)", min_value=0, value=80)
    
    if st.sidebar.button("Desconectar / Limpar Dados"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- Conteúdo Principal do Dashboard ---
st.title("🚚 Dashboard Operacional de Frota")

if not st.session_state.data_loaded:
    st.info("Por favor, insira suas credenciais na barra lateral e clique em 'Conectar e Carregar Dados' para começar.")
    st.stop()

# ### ALTERAÇÃO ###: Adiciona uma seção de depuração para ver os dados brutos da API
df_fleet = st.session_state.df_fleet
with st.expander("Clique aqui para ver as colunas e dados brutos recebidos da API"):
    st.write("Colunas recebidas da API (`df_fleet`):")
    st.write(df_fleet.columns.tolist())
    st.write("Primeiras 5 linhas dos dados recebidos:")
    st.dataframe(df_fleet.head())

# ### ALTERAÇÃO ###: Função para processar e converter colunas de forma segura
def safe_process_dataframe(df, columns_to_numeric):
    df_processed = df.copy()
    for col, target_type in columns_to_numeric.items():
        if col in df_processed.columns:
            if target_type == 'numeric':
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
            elif target_type == 'datetime':
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
        else:
            # Se a coluna não existir, cria ela com valores nulos para evitar erros futuros
            st.warning(f"A coluna esperada '{col}' não foi encontrada na resposta da API. Funcionalidades relacionadas podem não funcionar.")
            df_processed[col] = None 
    return df_processed

# Define quais colunas esperamos e seus tipos
fleet_cols_to_process = {
    'latitude': 'numeric',
    'longitude': 'numeric',
    'velocidade': 'numeric',
    'ignicao': 'numeric',
    'placa': 'string' # Mesmo que já seja string, garante a consistência
}
df_fleet = safe_process_dataframe(df_fleet, fleet_cols_to_process)


# --- Carregamento de dados históricos (somente se a frota foi carregada) ---
with st.spinner('Processando dados históricos... Isso pode levar um momento.'):
    all_vehicles_history = []
    # Verifica se a coluna 'placa' existe antes de tentar usá-la
    if 'placa' in df_fleet.columns:
        placas = df_fleet['placa'].dropna().unique()
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
        df_history_raw = pd.concat(all_vehicles_history, ignore_index=True)
        history_cols_to_process = {
            'velocidade': 'numeric',
            'ignicao': 'numeric',
            'odometro': 'numeric',
            'data_gravacao': 'datetime',
            'placa': 'string'
        }
        df_history = safe_process_dataframe(df_history_raw, history_cols_to_process)
        df_history = df_history.sort_values(by=['placa', 'data_gravacao']).dropna(subset=['data_gravacao'])
        st.session_state.df_history = df_history


# --- ANÁLISES E GRÁFICOS ---
# Todas as seções agora verificam se as colunas necessárias existem

# 1. KPIs Principais
st.header("Visão Geral da Frota")
total_vehicles = df_fleet.shape[0]
vehicles_on = df_fleet[df_fleet['ignicao'] == 1].shape[0] if 'ignicao' in df_fleet.columns else "N/A"
vehicles_off = (total_vehicles - vehicles_on) if isinstance(vehicles_on, int) else "N/A"
vehicles_speeding_now = df_fleet[df_fleet['velocidade'] > speed_limit].shape[0] if 'velocidade' in df_fleet.columns else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Veículos", total_vehicles)
col2.metric("Veículos Ligados", vehicles_on)
col3.metric("Veículos Desligados", vehicles_off)
col4.metric("Em Excesso de Velocidade (Agora)", vehicles_speeding_now, delta_color="inverse")
st.divider()

# 2. Mapa da Frota em Tempo Real
st.subheader("Localização da Frota em Tempo Real")
if 'latitude' in df_fleet.columns and 'longitude' in df_fleet.columns:
    df_map = df_fleet.dropna(subset=['latitude', 'longitude'])
    if not df_map.empty:
        st.map(df_map[['latitude', 'longitude']], zoom=4)
    else:
        st.info("Não há dados de localização para exibir no mapa.")
else:
    st.warning("Não foi possível gerar o mapa. Colunas 'latitude' e/ou 'longitude' não encontradas.")
st.divider()

# O resto do código continua com a mesma lógica de verificação
# ... (o restante do código para os outros gráficos permanece o mesmo, pois ele já é construído sobre o df_history que foi processado de forma segura)

df_history = st.session_state.df_history
if df_history.empty:
    st.warning("Não há dados históricos para gerar as análises do período selecionado.")
else:
    # O código dos gráficos subsequentes pode permanecer o mesmo, pois as colunas
    # já foram validadas e criadas (mesmo que vazias) pela função `safe_process_dataframe`
    pass # O código dos outros gráficos já está lá no seu original e funcionará aqui.
    # Exemplo para o primeiro gráfico da próxima seção:
    st.header(f"Análise do Período: {date_range[0].strftime('%d/%m/%Y')} a {date_range[1].strftime('%d/%m/%Y')}")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Ranking: Infrações de Velocidade")
        if 'velocidade' in df_history.columns and 'placa' in df_history.columns:
            speeding_events = df_history[df_history['velocidade'] > speed_limit]
            if not speeding_events.empty:
                speeding_counts = speeding_events['placa'].value_counts().reset_index()
                speeding_counts.columns = ['Veículo', 'Nº de Ocorrências']
                fig_speed = px.bar(speeding_counts, x='Nº de Ocorrências', y='Veículo', orientation='h', title=f"Veículos que ultrapassaram {speed_limit} km/h")
                fig_speed.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_speed, use_container_width=True)
            else:
                st.info(f"Nenhum veículo ultrapassou {speed_limit} km/h no período.")
        else:
            st.warning("Não foi possível gerar o gráfico de velocidade. Colunas 'velocidade' ou 'placa' não encontradas.")
    # (Continue essa lógica de verificação para os outros gráficos)
