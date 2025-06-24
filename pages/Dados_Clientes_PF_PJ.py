import streamlit as st
import pandas as pd
import io

# --- Funções Auxiliares ---

def processar_planilha(uploaded_file):
    """
    Processa um arquivo de planilha (Excel ou CSV) para extrair e limpar os dados dos clientes.
    A função detecta o tipo de arquivo e tenta encontrar o início da tabela de dados.
    """
    try:
        # Tenta ler o arquivo como Excel. Se falhar, tenta como CSV.
        try:
            # O parâmetro `header` começa a procurar o cabeçalho a partir da linha 9 (índice 8).
            # Isso é útil para pular as linhas de cabeçalho iniciais que não são os nomes das colunas.
            df = pd.read_excel(uploaded_file, header=9)
        except Exception:
            # Se não for um Excel válido ou der erro, volta ao início do arquivo para ler como CSV.
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, header=9)

        # Remove colunas que são completamente vazias
        df.dropna(axis='columns', how='all', inplace=True)
        # Remove linhas que são completamente vazias
        df.dropna(axis='rows', how='all', inplace=True)

        # --- Padronização das Colunas ---
        # Renomeia as colunas para um formato padrão e consistente.
        # Adicione ou modifique este dicionário conforme a necessidade das suas planilhas.
        rename_map = {
            'Nome': 'Nome / Razão Social',
            'Razão Social': 'Nome / Razão Social',
            'CPF': 'CPF / CNPJ',
            'CNPJ': 'CPF / CNPJ',
            'E-mail': 'Email',
            'Telefone': 'Telefone',
            'Endereço': 'Endereço',
            'Cidade': 'Cidade',
            'UF': 'Estado'
        }

        # Filtra o rename_map para conter apenas as colunas que existem no DataFrame
        existing_rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
        df.rename(columns=existing_rename_map, inplace=True)

        # --- Seleção e Ordem das Colunas ---
        # Define a lista de colunas que queremos no resultado final e a ordem delas.
        colunas_finais = [
            'Nome / Razão Social',
            'CPF / CNPJ',
            'Email',
            'Telefone',
            'Endereço',
            'Cidade',
            'Estado'
        ]

        # Retorna um DataFrame apenas com as colunas desejadas que existem na planilha processada.
        return df[[col for col in colunas_finais if col in df.columns]]

    except Exception as e:
        st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {e}")
        return pd.DataFrame()


def to_excel(df: pd.DataFrame):
    """
    Converte um DataFrame do Pandas para um arquivo Excel em memória, pronto para download.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    processed_data = output.getvalue()
    return processed_data

# --- Configuração da Página do Streamlit ---

st.set_page_config(
    page_title="Organizador de Planilhas de Clientes",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Organizador de Planilhas de Clientes")

st.write(
    "Faça o upload das suas planilhas de clientes (PF e/ou PJ) nos formatos XLSX ou CSV. "
    "A aplicação irá organizar os dados, padronizar as colunas e apresentar uma tabela consolidada."
)

# --- Upload dos Arquivos ---

uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    type=['xlsx', 'csv'],
    accept_multiple_files=True
)

if uploaded_files:
    # Lista para armazenar os DataFrames processados de cada arquivo
    lista_dfs = []

    # Processa cada arquivo que o usuário subiu
    for file in uploaded_files:
        st.info(f"Processando o arquivo: `{file.name}`...")
        df_processado = processar_planilha(file)
        if not df_processado.empty:
            lista_dfs.append(df_processado)

    # Se a lista de DataFrames não estiver vazia, consolida tudo em um único DataFrame
    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)

        st.success("✅ Processamento concluído! Veja os dados organizados abaixo.")

        # --- Visualização dos Dados ---
        st.dataframe(df_final)

        # --- Botão de Download ---
        st.download_button(
            label="📥 Baixar Planilha Organizada (.xlsx)",
            data=to_excel(df_final),
            file_name='relatorio_clientes_organizado.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.warning("Nenhum dado válido foi encontrado nos arquivos. Verifique o formato das planilhas.")

else:
    st.info("Aguardando o upload de planilhas...")
