import streamlit as st
import pandas as pd
import io

# --- Funções Auxiliares ---

def processar_planilha(uploaded_file):
    """
    Processa um arquivo de planilha (Excel ou CSV) de forma mais robusta.
    1. Encontra dinamicamente a linha do cabeçalho.
    2. Limpa e padroniza os dados.
    3. Retorna um DataFrame com as colunas de interesse.
    """
    st.info(f"Iniciando processamento do arquivo: `{uploaded_file.name}`")
    
    # Tenta ler como Excel ou CSV
    try:
        # Usamos uma cópia em memória para não consumir o arquivo original
        file_buffer = io.BytesIO(uploaded_file.getvalue())
        is_excel = True
        try:
            # Tenta carregar como Excel para ver se é válido
            pd.ExcelFile(file_buffer)
        except Exception:
            is_excel = False
        
        file_buffer.seek(0) # Retorna ao início do buffer

        # --- 1. Detecção automática da linha do cabeçalho ---
        header_row = None
        for i in range(15):  # Tenta encontrar o cabeçalho nas primeiras 15 linhas
            try:
                if is_excel:
                    df_test = pd.read_excel(file_buffer, header=i, nrows=5)
                else:
                    df_test = pd.read_csv(file_buffer, header=i, nrows=5, sep=None, engine='python')
                
                file_buffer.seek(0) # Sempre retorna ao início após a leitura

                # Converte os nomes das colunas para minúsculas para uma busca mais fácil
                potential_cols = [str(c).lower().strip() for c in df_test.columns]
                
                # Critérios para identificar um cabeçalho válido (presença de colunas chave)
                if any(key in ' '.join(potential_cols) for key in ['nome', 'razão', 'cpf', 'cnpj', 'mail', 'email']):
                    header_row = i
                    st.write(f"✔️ Cabeçalho encontrado na linha {i + 1} do arquivo.")
                    break
            except Exception:
                file_buffer.seek(0)
                continue
        
        if header_row is None:
            st.warning(f"⚠️ Não foi possível encontrar um cabeçalho com colunas conhecidas (Nome, CPF, CNPJ, etc.) no arquivo `{uploaded_file.name}`. O arquivo será ignorado.")
            return pd.DataFrame()

        # --- 2. Leitura completa do arquivo com o cabeçalho correto ---
        if is_excel:
            df = pd.read_excel(file_buffer, header=header_row)
        else:
            df = pd.read_csv(file_buffer, header=header_row, sep=None, engine='python')

        # --- 3. Limpeza do DataFrame ---
        df.dropna(axis='columns', how='all', inplace=True)
        df.dropna(axis='rows', how='all', inplace=True)
        
        # Armazena os nomes originais para diagnóstico
        original_columns = df.columns.tolist()
        
        # Padroniza os nomes das colunas (minúsculas, sem espaços extras)
        df.columns = df.columns.str.strip().str.lower()

        # --- 4. Mapeamento e Renomeação das Colunas ---
        rename_map = {
            'nome': 'Nome / Razão Social', 'razão social': 'Nome / Razão Social',
            'nome fantasia': 'Nome Fantasia',
            'cpf': 'CPF / CNPJ', 'cnpj': 'CPF / CNPJ',
            'e-mail': 'Email', 'email': 'Email', 'mail': 'Email',
            'fone': 'Telefone', 'telefone': 'Telefone', 'celular': 'Telefone',
            'endereço': 'Endereço', 'logradouro': 'Endereço',
            'cidade': 'Cidade',
            'uf': 'Estado', 'estado': 'Estado'
        }
        
        df.rename(columns=rename_map, inplace=True)

        st.write(f"Colunas Originais Encontradas: `{original_columns}`")

        # --- 5. Seleção e Ordem das Colunas Finais ---
        colunas_finais = [
            'Nome / Razão Social', 'Nome Fantasia', 'CPF / CNPJ',
            'Email', 'Telefone', 'Endereço', 'Cidade', 'Estado'
        ]
        
        colunas_existentes = [col for col in colunas_finais if col in df.columns]
        
        if not colunas_existentes:
            st.warning(f"Nenhuma das colunas esperadas foi encontrada em `{uploaded_file.name}` após a padronização.")
            return pd.DataFrame()
            
        return df[colunas_existentes]

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
st.title("📊 Organizador e Consolidador de Planilhas")
st.write(
    "Faça o upload de suas planilhas de clientes (XLSX ou CSV). "
    "A aplicação irá encontrar os dados, padronizar as colunas e consolidar tudo em um único arquivo."
)

# --- Upload dos Arquivos ---
uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    type=['xlsx', 'csv'],
    accept_multiple_files=True
)

if uploaded_files:
    lista_dfs = [processar_planilha(file) for file in uploaded_files]
    
    # Filtra DataFrames que possam estar vazios após o processamento
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
        st.error("Nenhum dado válido foi extraído dos arquivos. Por favor, verifique se as planilhas contêm colunas como 'Nome', 'CPF', 'CNPJ', etc.")

else:
    st.info("Aguardando o upload de planilhas...")
