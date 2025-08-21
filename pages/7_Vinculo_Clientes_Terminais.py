# pages/🔗_Vinculo_Clientes_Terminais.py
import streamlit as st
import pandas as pd
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Vínculo de Clientes e Terminais",
    page_icon="🔗"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO AUXILIAR ---
@st.cache_data
def processar_vinculos(file_clientes, file_rastreadores):
    """
    Lê as duas planilhas, processa a estrutura aninhada dos clientes e
    junta com as informações de modelo dos rastreadores.
    """
    try:
        # Lê a planilha de rastreadores para criar um mapa de Serial -> Modelo
        df_rastreadores = pd.read_excel(file_rastreadores, header=11, engine='openpyxl')
        df_rastreadores = df_rastreadores.rename(columns={'Nº Série': 'Rastreador_Serial', 'Modelo': 'Modelo_Rastreador'})
        df_rastreadores.dropna(subset=['Rastreador_Serial'], inplace=True)
        # Garante que a chave de junção seja uma string sem casas decimais
        df_rastreadores['Rastreador_Serial'] = df_rastreadores['Rastreador_Serial'].astype(float).astype(int).astype(str)
        mapa_modelos = df_rastreadores.set_index('Rastreador_Serial')['Modelo_Rastreador'].to_dict()

        # Lê a planilha de clientes sem cabeçalho para processar a estrutura aninhada
        df_clientes_raw = pd.read_excel(file_clientes, header=None, engine='openpyxl')
        
        registos_consolidados = []
        cliente_atual = {}
        
        header_row_index = -1
        for i, row in df_clientes_raw.head(20).iterrows():
            row_str = ' '.join(map(str, row.values)).lower()
            if 'nome do cliente' in row_str and 'cpf/cnpj' in row_str:
                header_row_index = i
                break
        
        if header_row_index == -1:
            st.error("Não foi possível encontrar a linha de cabeçalho (com 'Nome do Cliente', 'CPF/CNPJ') no `relatorio_clientes.xlsx`.")
            return None
        
        df_clientes_proc = df_clientes_raw.copy()
        df_clientes_proc.columns = df_clientes_raw.iloc[header_row_index]
        df_clientes_proc = df_clientes_proc.iloc[header_row_index + 1:].reset_index(drop=True)
        
        df_clientes_proc.columns = df_clientes_proc.columns.str.strip()
        df_clientes_proc = df_clientes_proc.rename(columns={'Tipo Cliente': 'Tipo de Cliente'})

        for index, row in df_clientes_proc.iterrows():
            tipo_cliente = str(row.get('Tipo de Cliente', '')).strip()
            
            if 'Jurídica' in tipo_cliente or 'Física' in tipo_cliente:
                cliente_atual = {
                    'Nome do Cliente': row.get('Nome do Cliente'),
                    'CPF/CNPJ': row.get('CPF/CNPJ'),
                    'Tipo de Cliente': tipo_cliente
                }
            
            # Ignora as linhas de sub-cabeçalho
            if str(row.get('Terminal')).strip() == 'Terminal' or str(row.get('Rastreador')).strip() == 'Rastreador':
                continue

            if pd.notna(row.get('Terminal')) and cliente_atual:
                registos_consolidados.append({
                    **cliente_atual,
                    'Terminal': row.get('Terminal'),
                    # Garante que o rastreador seja uma string sem casas decimais
                    'Rastreador': str(int(float(row.get('Rastreador'))))
                })

        if not registos_consolidados:
            return None

        df_final = pd.DataFrame(registos_consolidados)
        df_final['Modelo'] = df_final['Rastreador'].map(mapa_modelos).fillna('Modelo não encontrado')
        
        return df_final[['Nome do Cliente', 'CPF/CNPJ', 'Tipo de Cliente', 'Terminal', 'Rastreador', 'Modelo']]
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar os ficheiros: {e}")
        return None


# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔗 Vínculo de Clientes e Terminais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. UPLOAD DOS FICHEIROS ---
st.subheader("Carregamento dos Relatórios da Etrac")
col1, col2 = st.columns(2)

with col1:
    st.info("**1. Relatório de Clientes**")
    uploaded_clientes = st.file_uploader("Carregue o `relatorio_clientes.xlsx`", type=['xlsx'], key="clientes_upload")

with col2:
    st.info("**2. Relatório de Rastreadores (Estoque)**")
    uploaded_rastreadores = st.file_uploader("Carregue o `relatorio_rastreador.xlsx`", type=['xlsx'], key="rastreadores_upload")

st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO ---
if uploaded_clientes and uploaded_rastreadores:
    try:
        with st.spinner("A processar e a comparar as planilhas..."):
            df_resultado = processar_vinculos(uploaded_clientes, uploaded_rastreadores)
        
        if df_resultado is not None and not df_resultado.empty:
            st.success(f"Análise concluída! Foram encontrados **{len(df_resultado)}** terminais vinculados a clientes.")
            
            st.subheader("Tabela de Terminais Vinculados por Cliente")
            st.dataframe(df_resultado, use_container_width=True, hide_index=True)
        else:
            st.warning("Não foram encontrados vínculos válidos entre os ficheiros. Verifique se as planilhas contêm os dados e a estrutura esperados.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas.")
else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
