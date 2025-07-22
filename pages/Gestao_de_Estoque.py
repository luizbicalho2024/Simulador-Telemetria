# pages/Gestao_de_Estoque.py
import streamlit as st
import pandas as pd
import io

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
def processar_estoque_sistema(df_raw):
    """
    Processa o DataFrame do sistema, localizando o cabeçalho dinamicamente.
    """
    header_row_index = -1
    for i, row in df_raw.head(20).iterrows():
        row_str = ' '.join(map(str, row.values)).lower()
        if 'modelo' in row_str and 'nº série' in row_str and 'status' in row_str:
            header_row_index = i
            break
            
    if header_row_index == -1:
        raise ValueError("Cabeçalho não encontrado. Verifique se o ficheiro do sistema contém as colunas 'Modelo', 'Nº Série' e 'Status'.")

    df = df_raw.copy()
    df.columns = df.iloc[header_row_index]
    df = df.iloc[header_row_index + 1:].reset_index(drop=True)
    
    df = df.rename(columns={'Nº Série': 'Serial'})
    
    if 'Serial' not in df.columns:
        raise ValueError("A coluna 'Nº Série' não foi encontrada no cabeçalho identificado.")

    df.dropna(subset=['Serial'], inplace=True)
    df = df[df['Serial'].astype(str).str.strip() != '']
    df['Serial'] = df['Serial'].astype(str).str.strip()
    return df

def processar_estoque_fisico(df_fisico):
    """Processa o DataFrame do estoque físico."""
    df_fisico.columns = ['Serial'] + list(df_fisico.columns[1:])
    df_fisico = df_fisico[['Serial']]
    df_fisico['Serial'] = df_fisico['Serial'].astype(str).str.strip()
    return df_fisico

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
    st.warning("⚠️ **Instruções:** Exporte o `relatorio_rastreador.xls` e guarde-o como **CSV (separado por ponto e vírgula)**.")
    
    uploaded_sistema = st.file_uploader(
        "Carregue o ficheiro do sistema (guardado como .csv)",
        type=['csv']
    )

with col2:
    st.info("**2. Estoque Físico**")
    uploaded_fisico = st.file_uploader(
        "Carregue a planilha do inventário físico (`estoque_fisico.xlsx`)",
        type=['xlsx', 'csv']
    )

st.markdown("---")

# --- 5. ANÁLISE E COMPARAÇÃO ---
if uploaded_sistema and uploaded_fisico:
    try:
        df_sistema_raw = pd.read_csv(uploaded_sistema, delimiter=';', header=None, encoding='latin-1', on_bad_lines='skip')
        
        try:
            df_fisico_raw = pd.read_excel(uploaded_fisico)
        except Exception:
            uploaded_fisico.seek(0)
            df_fisico_raw = pd.read_csv(uploaded_fisico)

        df_sistema = processar_estoque_sistema(df_sistema_raw)
        df_fisico = processar_estoque_fisico(df_fisico_raw)

        st.subheader("Resultados da Conciliação de Estoque")

        # Junta os dados para análise completa
        df_fisico_com_status = pd.merge(df_fisico, df_sistema[['Serial', 'Status', 'Modelo']], on='Serial', how='left')
        df_fisico_com_status['Status'].fillna('Não Encontrado no Sistema', inplace=True)

        with st.expander("🔍 Análise do Estoque Físico", expanded=True):
            st.metric("Total de Rastreadores no Estoque Físico", value=len(df_fisico))
            
            disponivel_revisao = df_fisico_com_status[df_fisico_com_status['Status'].isin(['Disponível', 'Revisão'])]
            indisponivel = df_fisico_com_status[df_fisico_com_status['Status'] == 'Indisponível']
            manutencao = df_fisico_com_status[df_fisico_com_status['Status'] == 'Manutenção']
            
            col_a, col_b, col_c = st.columns(3)
            col_a.success(f"Disponível/Revisão: **{len(disponivel_revisao)}**")
            col_b.warning(f"Indisponível (Em Uso): **{len(indisponivel)}**")
            col_c.error(f"Manutenção: **{len(manutencao)}**")
            st.dataframe(df_fisico_com_status, use_container_width=True, hide_index=True)
        
        # ***** NOVA TABELA AQUI *****
        # Filtra apenas os seriais que não foram encontrados no sistema
        df_nao_encontrados = df_fisico_com_status[df_fisico_com_status['Status'] == 'Não Encontrado no Sistema']
        with st.expander("🚫 Seriais Não Encontrados no Sistema", expanded=False):
            if not df_nao_encontrados.empty:
                st.warning(f"Foram encontrados {len(df_nao_encontrados)} seriais no estoque físico que não constam no sistema. Estes itens precisam ser cadastrados.")
                st.dataframe(df_nao_encontrados[['Serial']], use_container_width=True, hide_index=True)
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
                
                # Prepara a coluna para exibição, se existir
                if 'Última Transmissão' not in df_sistema.columns:
                     df_sistema['Última Transmissão'] = "N/A"
                
                df_faltantes = df_sistema[df_sistema['Serial'].isin(faltando_no_fisico)]
                st.dataframe(
                    df_faltantes[['Serial', 'Status', 'Modelo', 'Última Transmissão']],
                    use_container_width=True, hide_index=True
                )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas.")

else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
