# pages/Faturamento.py
import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Assistente de Faturamento",
    page_icon="💲"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO AUXILIAR ---
@st.cache_data
def processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital):
    """
    Lê a planilha de terminais, classifica, calcula e retorna os dataframes de faturamento.
    """
    df = pd.read_excel(uploaded_file, header=11, engine='openpyxl')

    # ***** CORREÇÃO DEFINITIVA AQUI *****
    # Atribui manualmente os nomes corretos às colunas com base na sua ordem no ficheiro.
    df.columns = [
        'Cliente', 'Terminal', 'Placa', 'Rastreador', 'Rastreador Fabricante',
        'Rastreador Modelo', 'Número SimCard', 'Data Ativação', 'Data Desativação',
        'Suspenso Dias Mes'
    ]
    
    # Validação para garantir que as colunas essenciais existem após a renomeação
    required_cols = ['Terminal', 'Data Desativação', 'Suspenso Dias Mes']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"A estrutura do ficheiro parece ter mudado. Verifique as colunas.")

    # Limpeza e preparação dos dados
    df.dropna(subset=['Terminal'], inplace=True)
    df['Terminal'] = df['Terminal'].astype(str)
    df['Data Desativação'] = pd.to_datetime(df['Data Desativação'], errors='coerce')
    df['Suspenso Dias Mes'] = pd.to_numeric(df['Suspenso Dias Mes'], errors='coerce').fillna(0)

    # Classificação por tipo de equipamento
    df['Tipo'] = df['Terminal'].apply(lambda x: 'Satelital' if len(x) == 8 else 'GPRS')
    
    # Atribuição do valor unitário
    df['Valor Unitario'] = df['Tipo'].apply(lambda x: valor_satelital if x == 'Satelital' else valor_gprs)

    # Separação entre ativos e desativados
    df_ativos = df[df['Data Desativação'].isna()]
    df_desativados = df[df['Data Desativação'].notna()]

    # Cálculo do faturamento proporcional para os desativados
    if not df_desativados.empty:
        # Pega o número de dias no mês da primeira data de desativação (suficiente para o cálculo)
        dias_no_mes = df_desativados['Data Desativação'].iloc[0].days_in_month
        
        df_desativados['Dias Ativos'] = df_desativados['Data Desativação'].dt.day
        df_desativados['Dias a Faturar'] = (df_desativados['Dias Ativos'] - df_desativados['Suspenso Dias Mes']).clip(lower=0)
        df_desativados['Valor Proporcional'] = (df_desativados['Valor Unitario'] / dias_no_mes) * df_desativados['Dias a Faturar']
    
    return df_ativos, df_desativados

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>💲 Assistente de Faturamento</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. INPUTS DE CONFIGURAÇÃO ---
st.sidebar.header("Valores de Faturamento")
valor_gprs = st.sidebar.number_input("Valor Unitário Mensal (GPRS)", min_value=0.0, step=1.0, format="%.2f")
valor_satelital = st.sidebar.number_input("Valor Unitário Mensal (Satelital)", min_value=0.0, step=1.0, format="%.2f")

# --- 5. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório de Terminais")
st.info("Por favor, carregue o ficheiro `relatorio_terminal_xx-xx-xxxx_xx-xx-xxxx.xlsx` exportado do sistema.")

uploaded_file = st.file_uploader(
    "Selecione o relatório",
    type=['xlsx']
)

st.markdown("---")

# --- 6. ANÁLISE E EXIBIÇÃO ---
if uploaded_file:
    if valor_gprs == 0.0 or valor_satelital == 0.0:
        st.warning("Por favor, insira os valores unitários de GPRS e Satelital na barra lateral para continuar.")
    else:
        try:
            df_ativos, df_desativados = processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital)
            
            # --- CÁLCULO DOS TOTAIS ---
            total_faturamento_ativos = df_ativos['Valor Unitario'].sum()
            total_faturamento_desativados = df_desativados['Valor Proporcional'].sum()
            faturamento_total_geral = total_faturamento_ativos + total_faturamento_desativados

            st.header("Resumo do Faturamento")
            
            # --- CARDS DE MÉTRICAS ---
            col1, col2 = st.columns(2)
            col1.metric("Nº de Terminais Ativos (Faturamento Cheio)", value=len(df_ativos))
            col2.metric("Nº de Terminais Desativados (Faturamento Proporcional)", value=len(df_desativados))
            
            col_a, col_b, col_c = st.columns(3)
            col_a.success(f"**Faturamento (Ativos):** R$ {total_faturamento_ativos:,.2f}")
            col_b.warning(f"**Faturamento (Desativados):** R$ {total_faturamento_desativados:,.2f}")
            col_c.info(f"**FATURAMENTO TOTAL:** R$ {faturamento_total_geral:,.2f}")

            st.markdown("---")
            
            # --- TABELA DE TERMINAIS DESATIVADOS ---
            st.subheader("Detalhamento do Faturamento Proporcional (Terminais Desativados)")
            if not df_desativados.empty:
                st.dataframe(
                    df_desativados[['Terminal', 'Placa', 'Tipo', 'Data Desativação', 'Dias Ativos', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor Proporcional']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Data Desativação": st.column_config.DatetimeColumn("Data Desativação", format="DD/MM/YYYY"),
                        "Valor Unitario": st.column_config.NumberColumn("Valor Mensal Cheio (R$)", format="R$ %.2f"),
                        "Valor Proporcional": st.column_config.NumberColumn("Valor a Faturar (R$)", format="R$ %.2f")
                    }
                )
            else:
                st.info("Nenhum terminal foi desativado no período analisado.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
            st.info("Por favor, verifique se o ficheiro tem o formato e as colunas esperadas.")
else:
    st.info("Aguardando o carregamento do relatório para iniciar a análise.")
