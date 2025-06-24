import streamlit as st
import pandas as pd
import io

# --- Funções Auxiliares ---

def get_tipo_cliente(documento):
    """Analisa um documento (CPF ou CNPJ) e retorna o tipo de cliente."""
    if pd.isna(documento):
        return "Não Identificado"
    # Limpa o documento, mantendo apenas os números
    doc_limpo = ''.join(filter(str.isdigit, str(documento)))
    
    if len(doc_limpo) == 11:
        return "Pessoa Física"
    elif len(doc_limpo) == 14:
        return "Pessoa Jurídica"
    else:
        return "Indefinido"

def processar_planilha(uploaded_file):
    """
    Processa um arquivo de planilha, limpa os dados e formata as colunas conforme solicitado.
    """
    st.info(f"Iniciando processamento do arquivo: `{uploaded_file.name}`")
    
    try:
        file_buffer = io.BytesIO(uploaded_file.getvalue())
        is_excel = uploaded_file.name.endswith('.xlsx')
        
        # --- 1. Detecção automática da linha do cabeçalho ---
        header_row = None
        for i in range(15):
            try:
                if is_excel:
                    df_test = pd.read_excel(file_buffer, header=i, nrows=5)
                else:
                    df_test = pd.read_csv(file_buffer, header=i, nrows=5, sep=None, engine='python')
                file_buffer.seek(0)
                
                potential_cols = [str(c).lower().strip() for c in df_test.columns]
                if any(key in ' '.join(potential_cols) for key in ['nome', 'razão', 'cpf', 'cnpj', 'mail', 'email']):
                    header_row = i
                    st.write(f"✔️ Cabeçalho encontrado na linha {i + 1} do arquivo.")
                    break
            except Exception:
                file_buffer.seek(0)
                continue
        
        if header_row is None:
            st.warning(f"⚠️ Não foi possível encontrar um cabeçalho válido no arquivo `{uploaded_file.name}`.")
            return pd.DataFrame()

        # --- 2. Leitura completa do arquivo ---
        if is_excel:
            df = pd.read_excel(file_buffer, header=header_row)
        else:
            df = pd.read_csv(file_buffer, header=header_row, sep=None, engine='python')

        # --- 3. Limpeza inicial ---
        df.dropna(axis='columns', how='all', inplace=True)
        df.dropna(axis='rows', how='all', inplace=True)
        
        df.columns = df.columns.str.strip().str.lower()

        # --- 4. Mapeamento para nomes intermediários ---
        rename_map = {
            'nome': 'Nome do Cliente', 'razão social': 'Nome do Cliente',
            'cpf': 'CPF/CNPJ', 'cnpj': 'CPF/CNPJ',
            'e-mail': 'email', 'email': 'email', 'mail': 'email',
            'fone': 'Telefone', 'telefone': 'Telefone', 'celular': 'Telefone'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # --- 5. Criação da coluna 'Tipo Cliente' ---
        if 'CPF/CNPJ' in df.columns:
            df['Tipo Cliente'] = df['CPF/CNPJ'].apply(get_tipo_cliente)
        else:
            df['Tipo Cliente'] = "Não Identificado"
        
        # --- 6. Seleção e ordenação final das colunas ---
        colunas_finais_desejadas = [
            'Nome do Cliente',
            'CPF/CNPJ',
            'Tipo Cliente',
            'Telefone',
            'email'
        ]
        
        colunas_existentes_no_df = [col for col in colunas_finais_desejadas if col in df.columns]
        
        if not colunas_existentes_no_df:
            st.warning(f"Nenhuma das colunas desejadas foi encontrada em `{uploaded_file.name}`.")
            return pd.DataFrame()
            
        return df[colunas_existentes_no_df]

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar o arquivo {uploaded_file.name}: {e}")
        return pd.DataFrame()

def to_excel(df: pd.DataFrame):
    """Converte um DataFrame para um arquivo Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="📊", layout="wide")
st.title("📊 Organizador e Consolidador de Planilhas de Clientes")
st.write(
    "Faça o upload de suas planilhas de clientes (XLSX ou CSV). "
    "A aplicação irá organizar os dados nas colunas corretas e permitir o download do resultado."
)

# --- Upload dos Arquivos ---
uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    type=['xlsx', 'csv'],
    accept_multiple_files=True
)

if uploaded_files:
    lista_dfs = [processar_planilha(file) for file in uploaded_files]
    
    lista_dfs_validos = [df for df in lista_dfs if not df.empty]
    
    if lista_dfs_validos:
        df_final = pd.concat(lista_dfs_validos, ignore_index=True)
        st.success("✅ Processamento concluído! Veja os dados consolidados abaixo.")
        st.dataframe(df_final)
        
        st.download_button(
            label="📥 Baixar Planilha Consolidada (.xlsx)",
            data=to_excel(df_final),
            file_name='relatorio_clientes_consolidado.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("Nenhum dado válido foi extraído dos arquivos. Por favor, verifique o conteúdo das planilhas.")

else:
    st.info("Aguardando o upload de planilhas...")
