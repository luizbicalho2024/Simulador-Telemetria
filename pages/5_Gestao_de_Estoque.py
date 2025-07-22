# pages/Gestao_de_Estoque.py
import streamlit as st
import pandas as pd
import io
import plotly.express as px

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Gestão de Estoque",
    page_icon="📦"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES AUXILIARES ---
def processar_estoque_fisico(df_fisico):
    df_fisico.columns = ['Serial'] + list(df_fisico.columns[1:])
    df_fisico = df_fisico[['Serial']]
    df_fisico['Serial'] = df_fisico['Serial'].astype(str).str.strip()
    return df_fisico

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, sep=';', encoding='latin-1').encode('latin-1')

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>📦 Dashboard de Gestão de Estoque</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. UPLOAD DOS FICHEIROS ---
st.subheader("Carregamento dos Ficheiros de Estoque")
col1, col2 = st.columns(2)

with col1:
    st.info("**1. Estoque do Sistema**")
    st.warning("⚠️ **Instruções:** Abra o `relatorio_rastreador.xls` no Excel e guarde-o como **Pasta de Trabalho do Excel (*.xlsx)**.")
    uploaded_sistema = st.file_uploader(
        "Carregue o ficheiro do sistema (guardado como .xlsx)",
        type=['xlsx']
    )

with col2:
    st.info("**2. Estoque Físico**")
    uploaded_fisico = st.file_uploader(
        "Carregue a planilha do inventário físico",
        type=['xlsx', 'csv']
    )

st.markdown("---")

# --- 5. ANÁLISE E COMPARAÇÃO ---
if uploaded_sistema and uploaded_fisico:
    try:
        df_sistema = pd.read_excel(
            uploaded_sistema, header=11, engine='openpyxl'
        )
        df_sistema = df_sistema.rename(columns={'Nº Série': 'Serial'})
        
        required_columns = ['Serial', 'Status', 'Modelo']
        if not all(col in df_sistema.columns for col in required_columns):
            st.error(f"Erro de Colunas: O cabeçalho na linha 12 do seu ficheiro .xlsx não contém as colunas necessárias.")
            st.stop()

        df_sistema['Serial'] = df_sistema['Serial'].astype(str).str.strip()
        df_sistema.dropna(subset=['Serial'], inplace=True)

        try:
            df_fisico_raw = pd.read_excel(uploaded_fisico)
        except Exception:
            uploaded_fisico.seek(0)
            df_fisico_raw = pd.read_csv(uploaded_fisico)
        
        df_fisico = processar_estoque_fisico(df_fisico_raw)

        st.subheader("Resultados da Conciliação de Estoque")
        
        df_fisico_com_status = pd.merge(df_fisico, df_sistema[['Serial', 'Status', 'Modelo']], on='Serial', how='left')
        df_fisico_com_status['Status'].fillna('Não Encontrado no Sistema', inplace=True)

        st.markdown("##### Análise Visual do Estoque Físico")
        col_graph1, col_graph2 = st.columns(2)
        with col_graph1:
            df_status_counts = df_fisico_com_status['Status'].value_counts().reset_index()
            df_status_counts.columns = ['Status', 'Quantidade']
            fig_pie = px.pie(df_status_counts, names='Status', values='Quantidade', title='Distribuição de Status')
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_graph2:
            df_model_counts = df_fisico_com_status['Modelo'].value_counts().reset_index()
            df_model_counts.columns = ['Modelo', 'Quantidade']
            fig_bar = px.bar(df_model_counts.head(10), x='Modelo', y='Quantidade', title='Top 10 Modelos em Estoque')
            st.plotly_chart(fig_bar, use_container_width=True)

        with st.expander("🔍 Detalhes do Estoque Físico", expanded=False):
            st.metric("Total de Rastreadores no Estoque Físico", value=len(df_fisico))
            disponivel_revisao = df_fisico_com_status[df_fisico_com_status['Status'].isin(['Disponível', 'Revisão'])]
            indisponivel = df_fisico_com_status[df_fisico_com_status['Status'] == 'Indisponível']
            manutencao = df_fisico_com_status[df_fisico_com_status['Status'] == 'Manutenção']
            
            col_a, col_b, col_c = st.columns(3)
            col_a.success(f"Disponível/Revisão: **{len(disponivel_revisao)}**")
            col_b.warning(f"Indisponível (Em Uso): **{len(indisponivel)}**")
            col_c.error(f"Manutenção: **{len(manutencao)}**")
            st.dataframe(df_fisico_com_status, use_container_width=True, hide_index=True)
        
        df_nao_encontrados = df_fisico_com_status[df_fisico_com_status['Status'] == 'Não Encontrado no Sistema']
        with st.expander("🚫 Seriais do Físico Não Encontrados no Sistema", expanded=False):
            if not df_nao_encontrados.empty:
                st.warning(f"Foram encontrados {len(df_nao_encontrados)} seriais que precisam ser cadastrados.")
                st.dataframe(df_nao_encontrados[['Serial']], use_container_width=True, hide_index=True)
                csv_nao_encontrados = convert_df_to_csv(df_nao_encontrados[['Serial']])
                st.download_button("📥 Exportar Lista (.csv)", csv_nao_encontrados, "seriais_a_cadastrar.csv", "text/csv")
            else:
                st.success("Todos os seriais do estoque físico foram encontrados no sistema.")

        with st.expander("⚠️ Análise de Divergências (Itens Faltando no Físico)", expanded=True):
            df_sistema_para_conferencia = df_sistema[df_sistema['Status'] != 'Indisponível']
            seriais_sistema_conferencia = set(df_sistema_para_conferencia['Serial'])
            seriais_fisico = set(df_fisico['Serial'])
            
            faltando_no_fisico = seriais_sistema_conferencia - seriais_fisico
            
            if not faltando_no_fisico:
                st.success("🎉 Parabéns! Todos os rastreadores que deveriam estar em estoque foram encontrados.")
            else:
                st.error(f"Atenção: {len(faltando_no_fisico)} rastreador(es) não foram encontrados no estoque físico (excluindo os já 'Indisponíveis').")
                
                if 'Última Transmissão' not in df_sistema.columns:
                     df_sistema['Última Transmissão'] = "N/A"
                
                df_faltantes = df_sistema[df_sistema['Serial'].isin(faltando_no_fisico)]
                st.dataframe(
                    df_faltantes[['Serial', 'Status', 'Modelo', 'Última Transmissão']],
                    use_container_width=True, hide_index=True
                )
                csv_faltantes = convert_df_to_csv(df_faltantes[['Serial', 'Status', 'Modelo', 'Última Transmissão']])
                st.download_button("📥 Exportar Lista de Faltantes (.csv)", csv_faltantes, "rastreadores_faltantes.csv", "text/csv")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas.")

else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
