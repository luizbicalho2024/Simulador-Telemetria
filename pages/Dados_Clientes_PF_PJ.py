import streamlit as st
import pandas as pd
import io
import numpy as np

# --- Funções Auxiliares ---

def get_tipo_cliente(documento):
    """Analisa um documento (CPF ou CNPJ) e retorna o tipo de cliente."""
    if pd.isna(documento):
        return "Não Identificado"
    doc_limpo = ''.join(filter(str.isdigit, str(documento)))
    if len(doc_limpo) == 11:
        return "Pessoa Física"
    elif len(doc_limpo) == 14:
        return "Pessoa Jurídica"
    else:
        return "Indefinido"

def processar_planilha_avancado(uploaded_file):
    """
    Processa, agrupa e limpa dados de clientes que podem ocupar múltiplas linhas.
    """
    st.info(f"Iniciando processamento avançado do arquivo: `{uploaded_file.name}`")
    
    try:
        # --- ETAPA 1: Leitura e Diagnóstico ---
        file_buffer = io.BytesIO(uploaded_file.getvalue())
        df = pd.read_excel(file_buffer, header=None) # Lemos sem cabeçalho para analisar tudo

        # Encontra a primeira linha que parece ser o cabeçalho
        header_row = 0
        for i, row in df.head(15).iterrows():
            # Conta quantos valores na linha parecem ser texto de cabeçalho
            text_count = sum(1 for item in row if isinstance(item, str) and len(str(item)) > 2)
            if text_count > 2: # Se uma linha tem mais de 2 células com texto, consideramos cabeçalho
                header_row = i
                break
        
        # Recarrega o DataFrame usando a linha de cabeçalho encontrada
        file_buffer.seek(0)
        df = pd.read_excel(file_buffer, header=header_row)

        # Limpeza inicial
        df.dropna(axis='columns', how='all', inplace=True)
        df.dropna(axis='rows', how='all', inplace=True)

        st.markdown(f"### Diagnóstico do Arquivo: `{uploaded_file.name}`")
        st.write(f"Cabeçalho identificado na linha {header_row + 1}. Abaixo estão as primeiras linhas lidas:")
        st.dataframe(df.head(20))

        # --- ETAPA 2: Padronização dos Nomes das Colunas ---
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'nome': 'Nome do Cliente', 'razão social': 'Nome do Cliente',
            'cpf': 'CPF/CNPJ', 'cnpj': 'CPF/CNPJ',
            'e-mail': 'email', 'email': 'email', 'mail': 'email',
            'fone': 'Telefone', 'telefone': 'Telefone', 'celular': 'Telefone'
        }
        df.rename(columns=rename_map, inplace=True)

        # Garante que as colunas principais existam, senão não há como prosseguir
        if 'Nome do Cliente' not in df.columns or 'CPF/CNPJ' not in df.columns:
            st.warning(f"Não foi possível encontrar as colunas 'Nome do Cliente' e 'CPF/CNPJ' no arquivo `{uploaded_file.name}`. O arquivo não pode ser processado.")
            return pd.DataFrame()
        
        # --- ETAPA 3: Agrupamento de Múltiplas Linhas por Cliente ---
        # Substitui células vazias por 'NaN' para podermos usar o ffill
        df.replace('', np.nan, inplace=True)
        # Propaga o nome do cliente e o CPF/CNPJ para as linhas abaixo
        df['Nome do Cliente'] = df['Nome do Cliente'].ffill()
        df['CPF/CNPJ'] = df['CPF/CNPJ'].ffill()

        st.write("Dados após propagação de informações do cliente (antes do agrupamento):")
        st.dataframe(df.head(20))
        
        # Função para agregar os dados, juntando múltiplos valores com vírgula e removendo duplicatas
        def aggregate_text(series):
            return ', '.join(series.dropna().astype(str).unique())

        # Agrupa tudo pelo Nome e CPF/CNPJ
        aggregated_df = df.groupby(['Nome do Cliente', 'CPF/CNPJ']).agg({
            'email': aggregate_text,
            'Telefone': aggregate_text
        }).reset_index()
        
        # --- ETAPA 4: Criação da Coluna 'Tipo Cliente' e Finalização ---
        aggregated_df['Tipo Cliente'] = aggregated_df['CPF/CNPJ'].apply(get_tipo_cliente)

        colunas_finais = [
            'Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone', 'email'
        ]
        
        # Retorna apenas as colunas que existem no df final, na ordem correta
        return aggregated_df[[col for col in colunas_finais if col in aggregated_df.columns]]

    except Exception as e:
        st.error(f"Ocorreu um erro crítico ao processar o arquivo {uploaded_file.name}: {e}")
        return pd.DataFrame()


def to_excel(df: pd.DataFrame):
    """Converte um DataFrame para um arquivo Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="📊", layout="wide")
st.title("📊 Organizador Avançado de Planilhas de Clientes")
st.write(
    "Faça o upload de suas planilhas. A aplicação irá agrupar clientes com múltiplos contatos, "
    "organizar os dados nas colunas corretas e permitir o download."
)

# --- Upload dos Arquivos ---
uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    type=['xlsx', 'csv'],
    accept_multiple_files=True
)

if uploaded_files:
    lista_dfs = [processar_planilha_avancado(file) for file in uploaded_files]
    
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
        st.error("Nenhum dado válido foi extraído dos arquivos. Verifique os diagnósticos acima e o conteúdo das planilhas.")

else:
    st.info("Aguardando o upload de planilhas...")
