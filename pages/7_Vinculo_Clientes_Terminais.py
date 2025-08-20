# pages/🔗_Vinculo_Clientes_Terminais.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
import json

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Diagnóstico de Vínculos",
    page_icon="🔗"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO DE PROCESSAMENTO PARA JSON ---
@st.cache_data
def organizar_clientes_em_json(file_clientes):
    """
    Lê a planilha de clientes com estrutura aninhada e a transforma em um JSON organizado.
    """
    try:
        df_clientes_raw = pd.read_excel(file_clientes, header=None, engine='openpyxl')
        
        clientes_organizados = []
        cliente_atual_dict = None
        
        # Encontra o índice da linha do cabeçalho principal para saber onde os dados começam
        header_row_index = -1
        for i, row in df_clientes_raw.head(20).iterrows():
            row_str = ' '.join(map(str, row.values)).lower()
            if 'nome do cliente' in row_str and 'cpf/cnpj' in row_str:
                header_row_index = i
                break
        
        if header_row_index == -1:
            st.error("Diagnóstico falhou: Não foi possível encontrar a linha de cabeçalho (com 'Nome do Cliente', 'CPF/CNPJ') no `relatorio_clientes.xlsx`.")
            return None

        # Itera sobre as linhas de dados reais
        for index, row in df_clientes_raw.iloc[header_row_index + 1:].iterrows():
            # Converte a linha para uma lista de strings para facilitar a verificação
            row_values = [str(cell).strip() for cell in row.values]
            
            # Heurística para identificar uma linha de cliente:
            # A coluna 'Tipo Cliente' (índice 3 do cabeçalho) tem 'Jurídica' ou 'Física'
            tipo_cliente_str = row_values[3]
            if 'Jurídica' in tipo_cliente_str or 'Física' in tipo_cliente_str:
                # Se já tínhamos um cliente a ser processado, guarda-o na lista final
                if cliente_atual_dict:
                    clientes_organizados.append(cliente_atual_dict)
                
                # Inicia um novo cliente
                cliente_atual_dict = {
                    "Nome do Cliente": row_values[1],
                    "CPF/CNPJ": row_values[2],
                    "Tipo de Cliente": tipo_cliente_str,
                    "Terminais": []
                }
            
            # Heurística para identificar uma linha de terminal:
            # A coluna 'Terminal' (índice 0 do cabeçalho de terminais) não está vazia ou com 'nan'
            # E já temos um cliente atual identificado
            terminal_str = row_values[0]
            if cliente_atual_dict and terminal_str != 'nan' and 'Terminal' not in terminal_str:
                 cliente_atual_dict["Terminais"].append({
                     "Terminal": terminal_str,
                     "Rastreador": row_values[4] # A coluna "Rastreador" é a 5ª na sub-linha
                 })

        # Adiciona o último cliente processado à lista
        if cliente_atual_dict:
            clientes_organizados.append(cliente_atual_dict)

        return clientes_organizados

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar a planilha de clientes: {e}")
        return None

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔗 Diagnóstico de Vínculos (JSON)</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório de Clientes para Diagnóstico")
uploaded_clientes = st.file_uploader(
    "Carregue o `relatorio_clientes.xlsx`",
    type=['xlsx']
)
st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO EM JSON ---
if uploaded_clientes:
    try:
        with st.spinner("A processar a estrutura da planilha..."):
            dados_json = organizar_clientes_em_json(uploaded_clientes)
        
        st.subheader("Estrutura de Dados Extraída (Formato JSON)")
        
        if dados_json:
            st.success("A estrutura aninhada foi processada! Abaixo estão os clientes e os seus terminais associados.")
            st.json(dados_json)
        else:
            st.error("Não foi possível extrair uma estrutura válida da planilha. Verifique se o ficheiro está correto.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
else:
    st.info("Por favor, carregue o `relatorio_clientes.xlsx` para iniciar o diagnóstico.")
