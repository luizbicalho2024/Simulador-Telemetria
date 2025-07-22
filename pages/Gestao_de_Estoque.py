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

# --- 2. FUNÇÃO AUXILIAR ---
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
    st.warning("⚠️ **Instruções:** Abra o `relatorio_rastreador.xls` no Excel e guarde-o como **Pasta de Trabalho do Excel (*.xlsx)** antes de o carregar.")
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
        # Lê o ficheiro do sistema diretamente como .xlsx, assumindo o cabeçalho na linha 12
        df_sistema = pd.read_excel(
            uploaded_sistema,
            header=11, # Linha 12 do Excel (índice 11)
            engine='openpyxl'
        )
        
        # Renomeia as colunas para um formato padronizado e seguro
        df_sistema = df_sistema.rename(columns={'Nº Série': 'Serial', 'Nº Equipamento': 'N_Equipamento'})
        
        # Validação crucial para garantir que a leitura foi bem-sucedida
        required_columns = ['Serial', 'Status', 'Modelo']
        if not all(col in df_sistema.columns for col in required_columns):
            st.error(f"Erro de Colunas: O cabeçalho na linha 12 do seu ficheiro .xlsx não contém as colunas necessárias (Ex: 'Nº Série', 'Status', 'Modelo').")
            st.write("Colunas encontradas:", df_sistema.columns.tolist())
            st.stop()

        df_sistema['Serial'] = df_sistema['Serial'].astype(str).str.strip()
        df_sistema.dropna(subset=['Serial'], inplace=True)

        # Lê o ficheiro do estoque físico
        try:
            df_fisico_raw = pd.read_excel(uploaded_fisico)
        except Exception:
            uploaded_fisico.seek(0)
            df_fisico_raw = pd.read_csv(uploaded_fisico)
        
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

        with st.expander("⚠️ Análise de Divergências (Excluindo 'Indisponíveis')", expanded=True):
            df_sistema_para_conferencia = df_sistema[df_sistema['Status'] != 'Indisponível']
            seriais_sistema_conferencia = set(df_sistema_para_conferencia['Serial'])
            seriais_fisico = set(df_fisico['Serial'])
            
            faltando_no_fisico = seriais_sistema_conferencia - seriais_fisico
            
            if not faltando_no_fisico:
                st.success("🎉 Parabéns! Todos os rastreadores que deveriam estar em estoque foram encontrados.")
            else:
                st.error(f"Atenção: {len(faltando_no_fisico)} rastreador(es) não foram encontrados no estoque físico.")
                
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
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas, e se o cabeçalho está realmente na linha 12 do ficheiro do sistema.")

else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
