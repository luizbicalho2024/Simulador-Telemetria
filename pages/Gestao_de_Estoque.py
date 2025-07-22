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

# --- 2. FUNÇÃO AUXILIAR (SIMPLIFICADA) ---
def processar_estoque_fisico(df_fisico):
    """Processa e limpa o DataFrame do estoque físico."""
    # Garante que a primeira coluna se chama 'Serial'
    df_fisico.columns = ['Serial'] + list(df_fisico.columns[1:])
    df_fisico = df_fisico[['Serial']] # Seleciona apenas a coluna 'Serial'
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
    st.warning("⚠️ **Instruções:** Exporte o `relatorio_rastreador.xls` do sistema e guarde-o como **CSV (separado por ponto e vírgula)**.")
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
        # Lê o CSV especificando que o cabeçalho está na linha 12 (índice 11)
        df_sistema = pd.read_csv(
            uploaded_sistema,
            delimiter=';',
            header=11, # FIXADO: Linha 12 do ficheiro
            encoding='latin-1',
            on_bad_lines='warn'
        )
        
        # ***** CORREÇÃO DEFINITIVA AQUI *****
        # Atribui manualmente os nomes corretos às colunas, ignorando os nomes corrompidos do ficheiro.
        df_sistema.columns = [
            'Modelo', 'Gateway', 'N_Equipamento', 'Serial', 'P_Entrada',
            'Kit', 'Status', 'Tipo_Equipamento', 'Situacao'
        ]
        
        # Limpa e converte a coluna Serial
        df_sistema.dropna(subset=['Serial'], inplace=True)
        df_sistema = df_sistema[df_sistema['Serial'].astype(str).str.strip() != '']
        df_sistema['Serial'] = df_sistema['Serial'].astype(str).str.strip()
        
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
                
                df_faltantes = df_sistema[df_sistema['Serial'].isin(faltando_no_fisico)]
                # Seleciona as colunas que sabemos que existem
                st.dataframe(
                    df_faltantes[['Serial', 'Status', 'Modelo', 'Situacao']],
                    use_container_width=True, hide_index=True
                )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
        st.info("Por favor, verifique se o ficheiro do sistema foi guardado como CSV, se o cabeçalho está na linha 12 e se o ficheiro de estoque físico está correto.")

else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
