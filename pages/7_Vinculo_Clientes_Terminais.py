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
@st.cache_data(show_spinner=False)
def processar_clientes_hierarquico(file_clientes):
    """
    Lê a planilha de clientes com estrutura aninhada e a transforma em um JSON organizado.
    Identifica linhas de cliente e terminal, ignorando cabeçalhos de terminal.
    """
    try:
        # Lê a planilha inteira sem cabeçalho para ter controlo total
        df_raw = pd.read_excel(file_clientes, header=None, engine='openpyxl')

        clientes_organizados = []
        cliente_atual_dict = None

        # Itera sobre todas as linhas do ficheiro
        for index, row in df_raw.iterrows():
            # Converte cada célula em string e remove espaços para uma comparação fiável
            row_values = [str(cell).strip() if pd.notna(cell) else "" for cell in row.values]

            # Heurística para identificar uma linha de CLIENTE:
            # A 4ª coluna (índice 3) contém 'Jurídica' ou 'Física'
            if len(row_values) > 3 and ("jurídica" in row_values[3].lower() or "física" in row_values[3].lower()):
                # Se já tínhamos um cliente a ser processado, guarda-o na lista final
                if cliente_atual_dict is not None:
                    clientes_organizados.append(cliente_atual_dict)

                # Inicia um novo dicionário para o cliente atual
                cliente_atual_dict = {
                    "Nome do Cliente": row_values[1],
                    "CPF/CNPJ": row_values[2],
                    "Tipo Cliente": row_values[3],
                    "Terminais": []
                }
                continue # Pula para a próxima linha

            # Se já identificámos um cliente, procuramos por linhas de TERMINAL
            if cliente_atual_dict is not None:
                terminal_str = row_values[0]
                rastreador_str = row_values[4].replace(".0", "") if len(row_values) > 4 and row_values[4] else ""

                # Um terminal válido tem um valor na primeira coluna e não é um sub-cabeçalho
                if terminal_str and terminal_str.lower() != "terminal":
                    cliente_atual_dict["Terminais"].append({
                        "Terminal/Frota": terminal_str,
                        "Rastreador": rastreador_str
                    })

        # Adiciona o último cliente processado à lista
        if cliente_atual_dict is not None:
            clientes_organizados.append(cliente_atual_dict)

        return clientes_organizados if clientes_organizados else None

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar a planilha: {e}")
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

# --- 4. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório de Clientes")
st.info("Esta ferramenta irá ler a estrutura hierárquica do `relatorio_clientes.xlsx` e organizar os dados.")

uploaded_clientes = st.file_uploader(
    "Carregue o `relatorio_clientes.xlsx`",
    type=['xlsx']
)

st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO EM JSON ---
if uploaded_clientes:
    try:
        with st.spinner("A processar a estrutura da planilha..."):
            dados_json = processar_clientes_hierarquico(uploaded_clientes)
        
        st.subheader("Estrutura de Vínculos Extraída (Formato JSON)")
        
        if dados_json:
            total_terminais = sum(len(cliente['Terminais']) for cliente in dados_json)
            st.success(f"Análise concluída! Foram encontrados **{total_terminais}** terminais vinculados a **{len(dados_json)}** clientes.")
            st.json(dados_json)
        else:
            st.warning("Não foi possível extrair uma estrutura válida da planilha. Verifique se o ficheiro está correto.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
else:
    st.info("Por favor, carregue o `relatorio_clientes.xlsx` para iniciar a análise.")
