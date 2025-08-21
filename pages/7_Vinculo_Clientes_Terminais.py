# pages/🔗_Vinculo_Clientes_Terminais.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
import json

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Vínculo de Clientes e Terminais",
    page_icon="🔗"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO AUXILIAR ROBUSTA ---
@st.cache_data
def processar_vinculos_para_json(file_clientes, file_rastreadores):
    """
    Lê as duas planilhas, processa a estrutura aninhada dos clientes e
    retorna uma estrutura JSON com os vínculos.
    """
    try:
        # Etapa 1: Preparar o mapa de Rastreador -> Modelo
        df_rastreadores = pd.read_excel(file_rastreadores, header=11, engine='openpyxl')
        df_rastreadores = df_rastreadores.rename(columns={'Nº Série': 'Rastreador', 'Modelo': 'Modelo_Rastreador'})
        df_rastreadores.dropna(subset=['Rastreador'], inplace=True)
        df_rastreadores['Rastreador'] = df_rastreadores['Rastreador'].astype(str).str.replace(r'\.0$', '', regex=True)
        mapa_modelos = df_rastreadores.set_index('Rastreador')['Modelo_Rastreador'].to_dict()

        # Etapa 2: Ler e processar a planilha de clientes
        df_clientes_raw = pd.read_excel(file_clientes, header=11, engine='openpyxl')
        df_clientes_raw.columns = df_clientes_raw.columns.str.strip()
        df_clientes_raw = df_clientes_raw.rename(columns={'Tipo Cliente': 'Tipo de Cliente'})
        
        clientes_organizados = []
        cliente_atual_dict = None

        for index, row in df_clientes_raw.iterrows():
            tipo_cliente = str(row.get('Tipo de Cliente', '')).strip()
            
            # Se a linha define um novo cliente
            if 'Jurídica' in tipo_cliente or 'Física' in tipo_cliente:
                if cliente_atual_dict is not None:
                    clientes_organizados.append(cliente_atual_dict)
                
                cliente_atual_dict = {
                    "Nome do Cliente": row.get('Nome do Cliente'),
                    "CPF/CNPJ": row.get('CPF/CNPJ'),
                    "Tipo de Cliente": tipo_cliente,
                    "Terminais": []
                }
            
            # Se a linha contém um terminal, associa ao último cliente encontrado
            if pd.notna(row.get('Terminal')) and cliente_atual_dict is not None:
                rastreador_num = str(row.get('Rastreador')).replace('.0', '')
                
                # Ignora as linhas de sub-cabeçalho
                if str(row.get('Terminal')).lower() != 'terminal':
                    cliente_atual_dict["Terminais"].append({
                        "Terminal": row.get('Terminal'),
                        "Rastreador": rastreador_num,
                        "Modelo": mapa_modelos.get(rastreador_num, 'Modelo não encontrado')
                    })
        
        # Adiciona o último cliente processado à lista
        if cliente_atual_dict is not None:
            clientes_organizados.append(cliente_atual_dict)

        return clientes_organizados if registos_consolidados else None
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
            resultado_json = processar_vinculos_para_json(uploaded_clientes, uploaded_rastreadores)
        
        if resultado_json:
            total_terminais = sum(len(cliente['Terminais']) for cliente in resultado_json)
            st.success(f"Análise concluída! Foram encontrados **{total_terminais}** terminais vinculados a **{len(resultado_json)}** clientes.")
            
            st.subheader("Estrutura de Vínculos (JSON)")
            st.json(resultado_json)
        else:
            st.warning("Não foram encontrados vínculos válidos entre os ficheiros. Verifique se as planilhas contêm os dados e a estrutura esperados.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas.")
else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar a análise.")
