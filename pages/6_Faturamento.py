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
    Lê a planilha, classifica, e aplica as regras de negócio para o faturamento.
    """
    df = pd.read_excel(uploaded_file, header=11, engine='openpyxl')

    # Renomeia as colunas para um padrão limpo e previsível
    df = df.rename(columns={
        'Suspenso Dias Mês': 'Suspenso Dias Mes'
    })

    required_cols = ['Terminal', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes']
    if not all(col in df.columns for col in required_cols):
        st.error(f"O ficheiro não contém todas as colunas necessárias. Verifique o cabeçalho na linha 12.")
        st.write("Colunas encontradas:", df.columns.tolist())
        return None, None

    # Limpeza e preparação dos dados
    df.dropna(subset=['Terminal'], inplace=True)
    df['Terminal'] = df['Terminal'].astype(str).str.strip()
    df['Data Desativação'] = pd.to_datetime(df['Data Desativação'], errors='coerce')
    df['Dias Ativos Mês'] = pd.to_numeric(df['Dias Ativos Mês'], errors='coerce').fillna(0)
    df['Suspenso Dias Mes'] = pd.to_numeric(df['Suspenso Dias Mes'], errors='coerce').fillna(0)

    # Classificação por tipo de equipamento
    df['Tipo'] = df['Terminal'].apply(lambda x: 'Satelital' if len(x) == 8 else 'GPRS')
    df['Valor Unitario'] = df['Tipo'].apply(lambda x: valor_satelital if x == 'Satelital' else valor_gprs)

    # ***** LÓGICA DE FATURAMENTO CORRIGIDA *****
    # Determina o número de dias no mês (baseado na data de hoje, pode ser ajustado se o relatório for de outro mês)
    dias_no_mes = pd.Timestamp(datetime.now()).days_in_month
    
    # Calcula os dias a faturar, garantindo que nunca seja negativo
    df['Dias a Faturar'] = (df['Dias Ativos Mês'] - df['Suspenso Dias Mes']).clip(lower=0)
    
    # Calcula o valor a faturar para todos
    df['Valor a Faturar'] = (df['Valor Unitario'] / dias_no_mes) * df['Dias a Faturar']
    
    # Separa os terminais: 'Ativos' são os que serão cobrados pelo mês completo
    # (Dias a Faturar = Dias no Mês), todos os outros são proporcionais.
    df_faturamento_cheio = df[df['Dias a Faturar'] == dias_no_mes]
    df_faturamento_proporcional = df[df['Dias a Faturar'] < dias_no_mes]
    
    return df_faturamento_cheio, df_faturamento_proporcional

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
            df_cheio, df_proporcional = processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital)
            
            if df_cheio is not None:
                total_faturamento_cheio = df_cheio['Valor a Faturar'].sum()
                total_faturamento_proporcional = df_proporcional['Valor a Faturar'].sum()
                faturamento_total_geral = total_faturamento_cheio + total_faturamento_proporcional

                st.header("Resumo do Faturamento")
                
                col1, col2 = st.columns(2)
                col1.metric("Nº de Terminais com Faturamento Cheio", value=len(df_cheio))
                col2.metric("Nº de Terminais com Faturamento Proporcional", value=len(df_proporcional))
                
                col_a, col_b, col_c = st.columns(3)
                col_a.success(f"**Faturamento (Cheio):** R$ {total_faturamento_cheio:,.2f}")
                col_b.warning(f"**Faturamento (Proporcional):** R$ {total_faturamento_proporcional:,.2f}")
                col_c.info(f"**FATURAMENTO TOTAL:** R$ {faturamento_total_geral:,.2f}")

                st.markdown("---")
                
                st.subheader("Detalhamento do Faturamento Proporcional")
                if not df_proporcional.empty:
                    st.dataframe(
                        df_proporcional[['Terminal', 'Placa', 'Tipo', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor a Faturar']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Data Desativação": st.column_config.DatetimeColumn("Data Desativação", format="DD/MM/YYYY"),
                            "Valor Unitario": st.column_config.NumberColumn("Valor Mensal Cheio (R$)", format="R$ %.2f"),
                            "Valor a Faturar": st.column_config.NumberColumn("Valor a Faturar (R$)", format="R$ %.2f")
                        }
                    )
                else:
                    st.info("Nenhum terminal com faturamento proporcional neste período.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
            st.info("Por favor, verifique se o ficheiro tem o formato e as colunas esperadas.")
else:
    st.info("Aguardando o carregamento do relatório para iniciar a análise.")
