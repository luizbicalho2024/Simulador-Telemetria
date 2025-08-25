import streamlit as st
import pandas as pd
# Removido 'user_management_db' e 'json' pois não são usados na lógica principal,
# mas você pode adicioná-los de volta se precisar deles para outra coisa.
import io

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Vínculo de Clientes e Terminais",
    page_icon="🔗"
)

# Simula um estado de login para teste. 
# Em seu ambiente real, este estado será controlado pelo seu sistema de login.
# Para testar o acesso negado, mude para False.
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = True 

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- O RESTANTE DA APLICAÇÃO SÓ É EXECUTADO SE O LOGIN FOR VÁLIDO ---

# --- Funções de Processamento de Dados ---

def processar_relatorio_clientes(df):
    """
    Processa o DataFrame do relatório de clientes para extrair e estruturar
    as informações de clientes e suas frotas.
    """
    processed_data = []
    current_client_info = {}

    for _, row in df.iterrows():
        if row.isnull().all():
            continue

        row_values = [str(v) if pd.notna(v) else '' for v in row]
        
        if 'Nome do Cliente' in row_values[1] or 'Terminal' in row_values[1]:
            continue

        if 'Física' in row_values[3] or 'Jurídica' in row_values[3]:
            current_client_info = {
                'Cliente': row_values[1],
                'CPF_CNPJ': row_values[2],
                'Tipo_Cliente': row_values[3],
                'Telefone': row_values[4]
            }
        elif current_client_info and row_values[5]:
            vehicle_data = {
                'Cliente': current_client_info.get('Cliente'),
                'CPF_CNPJ': current_client_info.get('CPF_CNPJ'),
                'Tipo_Cliente': current_client_info.get('Tipo_Cliente'),
                'Telefone': current_client_info.get('Telefone'),
                'Frota': row_values[2],
                'Descricao': row_values[3],
                'SimCard': row_values[4],
                'Rastreador': row_values[5]
            }
            processed_data.append(vehicle_data)

    cols = ['Cliente', 'CPF_CNPJ', 'Tipo_Cliente', 'Telefone', 'Frota', 'Descricao', 'SimCard', 'Rastreador']
    df_processed = pd.DataFrame(processed_data)
    return df_processed[cols]


def to_csv(df):
    """Converte um DataFrame para CSV em memória para o botão de download."""
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    processed_data = output.getvalue()
    return processed_data

# --- Interface Principal da Aplicação ---

st.title("🔗 Ferramenta para Vínculo de Clientes e Terminais")
st.markdown("""
Esta aplicação automatiza a organização e combinação de relatórios. 
Faça o upload dos **dois arquivos** CSV solicitados para gerar o relatório final consolidado.
""")

# --- Seção de Upload de Arquivos ---
st.header("1. Faça o upload dos arquivos")

col1, col2 = st.columns(2)

with col1:
    uploaded_clientes = st.file_uploader(
        "Relatório de Clientes",
        type="csv",
        help="Arquivo CSV contendo os dados básicos dos clientes e frotas (ex: relatorio_clientes.xlsx - Clientes.csv)"
    )

with col2:
    uploaded_rastreadores = st.file_uploader(
        "Estoque de Rastreadores",
        type="csv",
        help="Relatório com o modelo de cada rastreador, baseado no Nº de Série (ex: relatorio_rastreador.xlsx - Estoque de Rastreadores.csv)"
    )


# --- Lógica de Processamento e Exibição ---

if uploaded_clientes and uploaded_rastreadores:
    st.header("2. Processamento e Resultado")
    try:
        with st.spinner('Processando Relatório de Clientes...'):
            df_clientes_raw = pd.read_csv(uploaded_clientes, skiprows=11, header=None, usecols=range(6))
            df_base = processar_relatorio_clientes(df_clientes_raw)
            st.success("Relatório de Clientes processado com sucesso!")

        with st.spinner('Cruzando informações com o estoque de rastreadores...'):
            df_rastreador = pd.read_csv(uploaded_rastreadores, skiprows=11)
            df_lookup = df_rastreador[['Modelo', 'Nº Série']].drop_duplicates(subset=['Nº Série'])
            
            df_base['Rastreador'] = df_base['Rastreador'].astype(str).str.replace(r'\.0$', '', regex=True)
            df_lookup['Nº Série'] = df_lookup['Nº Série'].astype(str).str.replace(r'\.0$', '', regex=True)

            df_final = pd.merge(df_base, df_lookup, left_on='Rastreador', right_on='Nº Série', how='left')
            df_final.drop(columns=['Nº Série'], inplace=True)
            df_final['Modelo'].fillna('Modelo não encontrado', inplace=True)
            st.success("Modelo do rastreador adicionado!")

        st.subheader("Relatório Final Consolidado")
        st.dataframe(df_final)

        st.download_button(
            label="📥 Baixar Relatório Final em CSV",
            data=to_csv(df_final),
            file_name='relatorio_final_consolidado.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento: {e}")
        st.warning("Verifique se os arquivos enviados estão no formato correto e se correspondem aos esperados.")

else:
    st.info("Aguardando o upload dos dois arquivos para iniciar o processamento.")
