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
def processar_estoque_sistema(df_sistema):
    """
    Processa e limpa o DataFrame do estoque do sistema, localizando o cabeçalho dinamicamente.
    Esta função é mais robusta para lidar com ficheiros exportados de sistemas.
    """
    header_row_index = -1
    # Procura pelo cabeçalho nas primeiras 15 linhas do ficheiro
    for i, row in df_sistema.head(15).iterrows():
        # Converte a linha para uma string única para facilitar a busca
        row_str = ' '.join(map(str, row.values))
        # Procura por palavras-chave que identificam o cabeçalho
        if 'ID' in row_str and 'Serial' in row_str and 'Status' in row_str:
            header_row_index = i
            break
            
    if header_row_index == -1:
        raise ValueError("Não foi possível encontrar a linha de cabeçalho no ficheiro do sistema. Verifique se o ficheiro contém colunas como 'ID', 'Serial' e 'Status'.")

    # Define a linha encontrada como o novo cabeçalho
    df_sistema.columns = df_sistema.iloc[header_row_index]
    
    # Remove todas as linhas acima e incluindo o cabeçalho
    df_sistema = df_sistema.iloc[header_row_index + 1:].reset_index(drop=True)
    
    # Renomeia as colunas para um formato padronizado para evitar problemas
    df_sistema.columns = ['ID', 'Data Cadastro', 'Última Transmissão', 'Modelo', 'Versão', 'Serial', 'Status']
    
    # Remove linhas onde o 'Serial' é nulo, vazio ou não numérico, que podem ser rodapés
    df_sistema.dropna(subset=['Serial'], inplace=True)
    df_sistema = df_sistema[df_sistema['Serial'].astype(str).str.strip() != '']
    df_sistema = df_sistema[pd.to_numeric(df_sistema['Serial'], errors='coerce').notnull()]

    # Limpa os dados da coluna Serial
    df_sistema['Serial'] = df_sistema['Serial'].astype(str).str.strip()
    return df_sistema

def processar_estoque_fisico(df_fisico):
    """Processa e limpa o DataFrame do estoque físico."""
    df_fisico.columns = ['Serial']
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
    st.warning("⚠️ **Importante:** Abra o ficheiro `relatorio_rastreador.xls` no Excel e guarde-o como .CSV (separado por vírgulas) antes de o carregar aqui.")
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
        # Lê o CSV sem cabeçalho para que a nossa função possa encontrá-lo
        df_sistema_raw = pd.read_csv(uploaded_sistema, delimiter=';', header=None, encoding='latin-1', on_bad_lines='skip')
        
        try:
            df_fisico_raw = pd.read_excel(uploaded_fisico)
        except Exception:
            uploaded_fisico.seek(0)
            df_fisico_raw = pd.read_csv(uploaded_fisico)

        df_sistema = processar_estoque_sistema(df_sistema_raw)
        df_fisico = processar_estoque_fisico(df_fisico_raw)

        st.subheader("Resultados da Conciliação de Estoque")

        with st.expander("🔍 Análise do Estoque Físico", expanded=True):
            df_fisico_com_status = pd.merge(df_fisico, df_sistema[['Serial', 'Status', 'Modelo']], on='Serial', how='left')
            df_fisico_com_status['Status'].fillna('Não Encontrado no Sistema', inplace=True)
            
            st.metric("Total de Rastreadores no Estoque Físico", value=len(df_fisico))
            
            disponivel_revisao = df_fisico_com_status[df_fisico_com_status['Status'].isin(['Disponível', 'Revisão'])]
            indisponivel = df_fisico_com_status[df_fisico_com_status['Status'] == 'Indisponível']
            manutencao = df_fisico_com_status[df_fisico_com_status['Status'] == 'Manutenção']
            
            col_a, col_b, col_c = st.columns(3)
            col_a.success(f"Disponível/Revisão: **{len(disponivel_revisao)}**")
            col_b.warning(f"Indisponível (Em Uso): **{len(indisponivel)}**")
            col_c.error(f"Manutenção: **{len(manutencao)}**")
            st.dataframe(df_fisico_com_status, use_container_width=True, hide_index=True)

        with st.expander("⚠️ Análise de Divergências", expanded=True):
            seriais_sistema = set(df_sistema['Serial'])
            seriais_fisico = set(df_fisico['Serial'])
            
            faltando_no_fisico = seriais_sistema - seriais_fisico
            
            if not faltando_no_fisico:
                st.success("🎉 Parabéns! Todos os rastreadores do sistema foram encontrados no estoque físico.")
            else:
                st.error(f"Atenção: {len(faltando_no_fisico)} rastreador(es) não foram encontrados no estoque físico.")
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
