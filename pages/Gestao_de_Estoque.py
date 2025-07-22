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

# --- 2. FUNÇÕES AUXILIARES (MAIS ROBUSTAS) ---
def processar_estoque_sistema(df_sistema_raw):
    """
    Processa e limpa o DataFrame do sistema, localizando o cabeçalho dinamicamente
    com base nas novas colunas fornecidas.
    """
    header_row_index = -1
    # Procura pelo cabeçalho nas primeiras 20 linhas do ficheiro
    for i, row in df_sistema_raw.head(20).iterrows():
        # Converte a linha para uma string única para facilitar a busca
        row_str = ' '.join(map(str, row.values)).lower()
        # Procura por palavras-chave que identificam o cabeçalho
        if 'modelo' in row_str and 'nº série' in row_str and 'status' in row_str:
            header_row_index = i
            break
            
    if header_row_index == -1:
        raise ValueError("Não foi possível encontrar a linha de cabeçalho. Verifique se o ficheiro contém as colunas 'Modelo', 'Nº Série' e 'Status'.")

    df_sistema = df_sistema_raw.copy()
    df_sistema.columns = df_sistema.iloc[header_row_index]
    df_sistema = df_sistema.iloc[header_row_index + 1:].reset_index(drop=True)
    
    # Renomeia as colunas para um formato padronizado, mapeando 'Nº Série' para 'Serial'
    df_sistema = df_sistema.rename(columns={
        'Nº Série': 'Serial',
        'Última Transmissão': 'Ultima_Transmissao' # Exemplo de como renomear outras se necessário
    })
    
    # Garante que a coluna 'Serial' existe após a renomeação
    if 'Serial' not in df_sistema.columns:
        raise ValueError("A coluna 'Nº Série' não foi encontrada no cabeçalho do ficheiro do sistema.")

    # Remove linhas onde o 'Serial' é nulo ou vazio
    df_sistema.dropna(subset=['Serial'], inplace=True)
    df_sistema = df_sistema[df_sistema['Serial'].astype(str).str.strip() != '']
    
    df_sistema['Serial'] = df_sistema['Serial'].astype(str).str.strip()
    return df_sistema

def processar_estoque_fisico(df_fisico):
    """Processa e limpa o DataFrame do estoque físico."""
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
    st.warning("⚠️ **Instruções:** Exporte o `relatorio_rastreador.xls` do sistema e guarde-o como **CSV (separado por ponto e vírgula)** no Excel antes de carregar.")
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
                # Garante que a coluna 'Última Transmissão' existe para exibição
                if 'Ultima_Transmissao' not in df_sistema.columns:
                     df_sistema['Ultima_Transmissao'] = "N/A"
                df_faltantes = df_sistema[df_sistema['Serial'].isin(faltando_no_fisico)]
                st.dataframe(
                    df_faltantes[['Serial', 'Status', 'Modelo', 'Ultima_Transmissao']],
                    use_container_width=True, hide_index=True
                )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas, seguindo as instruções acima.")

else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
