# pages/🤖_Automação_Cadastro.py
import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Diagnóstico de Planilha",
    page_icon="🔎"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. CONSTANTES ---
COLUNAS_OBRIGATORIAS = [
    'ID_cliente', 'Segmento', 'Placa', 'Chassi', 'Marca', 'Modelo', 
    'Ano Modelo', 'Ano de Fabricação', 'Combustível', 'Cor', 
    'Origem de Veículo', 'Tanque de Combustivel', 'Mes Licenciamento'
]

# --- 3. INTERFACE DA PÁGINA ---
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🔎 Ferramenta de Diagnóstico de Planilha</h1>", unsafe_allow_html=True)
st.markdown("---")

st.info("Esta ferramenta serve apenas para diagnosticar o problema de leitura da sua planilha. Carregue o ficheiro abaixo para ver como o sistema está a interpretar as colunas.")

uploaded_file = st.file_uploader(
    "Carregue a sua planilha (`.xlsx` ou `.csv`)",
    type=['xlsx', 'csv']
)

st.markdown("---")

if uploaded_file:
    try:
        df = None
        # Tenta ler como Excel primeiro, depois como CSV
        try:
            st.write("Tentando ler como ficheiro Excel (`.xlsx`)...")
            df = pd.read_excel(uploaded_file, header=1, engine='openpyxl')
            st.success("Ficheiro lido como Excel com sucesso!")
        except Exception as e_excel:
            st.warning(f"Não foi possível ler como Excel ({e_excel}). A tentar como CSV...")
            # É importante rebobinar o ficheiro antes de tentar ler novamente
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, header=1)
                st.success("Ficheiro lido como CSV com sucesso!")
            except Exception as e_csv:
                st.error(f"Falha ao ler o ficheiro como Excel e como CSV. Erro CSV: {e_csv}")
                st.stop()
        
        if df is not None:
            st.subheader("1. Colunas Originais Encontradas")
            st.info("Esta é a lista exata dos nomes das colunas que o Pandas leu da segunda linha do seu ficheiro.")
            st.code(str(df.columns.tolist()), language='text')

            # Limpa os nomes das colunas
            colunas_limpas = df.columns.str.replace(r'\s*\(\*\)', '', regex=True).str.strip()
            
            st.subheader("2. Colunas Após a Limpeza")
            st.info("Esta é a lista de colunas após o script tentar limpar os nomes (removendo `(*)` e espaços).")
            st.code(str(colunas_limpas.tolist()), language='text')

            st.subheader("3. Colunas Obrigatórias Esperadas pelo Script")
            st.info("Esta é a lista de colunas que o script procura para poder funcionar.")
            st.code(str(COLUNAS_OBRIGATORIAS), language='text')

            st.markdown("---")
            st.subheader("4. Verificação Final")

            missing_cols = [col for col in COLUNAS_OBRIGATORIAS if col not in colunas_limpas]

            if missing_cols:
                st.error(f"**Diagnóstico:** Falha! As seguintes colunas obrigatórias não foram encontradas após a limpeza:")
                st.code(str(missing_cols), language='text')
                st.warning("Por favor, compare a lista do passo 2 com a do passo 3 para encontrar a discrepância. Pode ser um acento, um espaço extra ou um nome ligeiramente diferente.")
            else:
                st.success("**Diagnóstico:** Sucesso! Todas as colunas obrigatórias foram encontradas e correspondem ao esperado.")
                st.info("Agora que validámos a leitura, posso construir o script final com a automação completa.")

    except Exception as e:
        st.error(f"Ocorreu um erro geral durante a leitura do ficheiro: {e}")
