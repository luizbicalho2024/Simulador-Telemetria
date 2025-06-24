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

def processar_para_formato_largo(uploaded_file):
    """
    Processa a planilha e a transforma em um formato "largo", com colunas dinâmicas para cada usuário.
    """
    st.info(f"Iniciando processamento para formato largo: `{uploaded_file.name}`")
    
    try:
        # --- ETAPA 1: Leitura e Limpeza Inicial ---
        df = pd.read_excel(uploaded_file, header=None)
        
        header_row = 0
        for i, row in df.head(15).iterrows():
            text_count = sum(1 for item in row if isinstance(item, str) and len(str(item)) > 2)
            if text_count > 2:
                header_row = i
                break
        
        df = pd.read_excel(uploaded_file, header=header_row)
        df.dropna(axis='columns', how='all', inplace=True)
        df.dropna(axis='rows', how='all', inplace=True)

        st.markdown(f"### Diagnóstico: Dados Lidos do Arquivo `{uploaded_file.name}`")
        st.dataframe(df.head(15))

        # --- ETAPA 2: Padronização das Colunas ---
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'nome': 'Nome do Cliente', 'razão social': 'Nome do Cliente',
            'cpf': 'CPF/CNPJ', 'cnpj': 'CPF/CNPJ',
            'nome de usuário': 'Nome de Usuário', 'usuário': 'Nome de Usuário',
            'e-mail': 'Email', 'email': 'Email', 'mail': 'Email',
            'fone': 'Telefone', 'telefone': 'Telefone', 'celular': 'Telefone'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # --- ETAPA 3: Associação de Usuários a Clientes ---
        id_cols = ['Nome do Cliente', 'CPF/CNPJ']
        for col in id_cols:
            if col not in df.columns:
                st.error(f"Coluna essencial '{col}' não encontrada no arquivo. Verifique a planilha.")
                return pd.DataFrame()
        
        df[id_cols] = df[id_cols].ffill()

        # --- ETAPA 4: Separação e Transformação ---
        # Guarda o telefone principal (primeira ocorrência por cliente)
        telefones_principais = df.dropna(subset=['Telefone']).drop_duplicates(subset=id_cols)
        
        # Filtra apenas as linhas que contêm informações de usuários
        df_users = df.dropna(subset=['Nome de Usuário', 'Email'], how='any').copy()
        
        if df_users.empty:
            st.warning("Nenhum usuário com 'Nome de Usuário' e 'Email' foi encontrado.")
            # Retorna apenas os dados básicos do cliente se não houver usuários
            df_clients = df[id_cols].drop_duplicates().merge(telefones_principais[[*id_cols, 'Telefone']], on=id_cols, how='left')
            df_clients['Tipo Cliente'] = df_clients['CPF/CNPJ'].apply(get_tipo_cliente)
            return df_clients

        # Numera os usuários dentro de cada grupo de cliente
        df_users['user_num'] = df_users.groupby(id_cols).cumcount() + 1
        
        # Pivota a tabela para criar as colunas de usuário e email
        pivoted_users = df_users.pivot_table(
            index=id_cols,
            columns='user_num',
            values=['Nome de Usuário', 'Email'],
            aggfunc='first'
        )
        
        # Achata os nomes das colunas (de multi-nível para nível único)
        pivoted_users.columns = [f'{val[0]} {val[1]}' for val in pivoted_users.columns]
        
        # --- ETAPA 5: Junção e Finalização ---
        # Pega a lista única de clientes
        df_clients = df[id_cols].drop_duplicates()
        
        # Junta os dados dos clientes com os telefones e com os usuários pivotados
        final_df = df_clients.merge(telefones_principais[[*id_cols, 'Telefone']], on=id_cols, how='left')
        final_df = final_df.merge(pivoted_users, on=id_cols, how='left')
        
        # Adiciona a coluna "Tipo Cliente"
        final_df['Tipo Cliente'] = final_df['CPF/CNPJ'].apply(get_tipo_cliente)
        
        # Reorganiza as colunas para o formato final desejado
        cols_principais = ['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone']
        cols_usuarios = sorted([col for col in final_df.columns if col.startswith('Nome Usuário') or col.startswith('Email')])
        
        ordem_final = cols_principais + cols_usuarios
        return final_df[ordem_final]

    except Exception as e:
        st.error(f"Ocorreu um erro crítico ao processar o arquivo: {e}")
        return pd.DataFrame()

def to_excel(df: pd.DataFrame):
    """Converte um DataFrame para um arquivo Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Formato_Largo')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="📊", layout="wide")
st.title("⚙️ Transformador de Planilhas para Formato Largo")
st.write(
    "Faça o upload da sua planilha de clientes. A aplicação irá converter os dados para um formato "
    "onde cada cliente ocupa uma única linha e seus usuários são listados em colunas sequenciais."
)

uploaded_files = st.file_uploader(
    "Selecione os arquivos", type=['xlsx', 'csv'], accept_multiple_files=True
)

if uploaded_files:
    all_dfs = [processar_para_formato_largo(file) for file in uploaded_files]
    valid_dfs = [df for df in all_dfs if not df.empty]
    
    if valid_dfs:
        final_combined_df = pd.concat(valid_dfs, ignore_index=True)
        st.success("✅ Transformação concluída! Veja os dados abaixo.")
        st.dataframe(final_combined_df.fillna(''))
        
        st.download_button(
            label="📥 Baixar Planilha Final (.xlsx)",
            data=to_excel(final_combined_df),
            file_name='relatorio_clientes_formato_largo.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("Nenhum dado válido foi extraído dos arquivos. Verifique os diagnósticos acima.")
else:
    st.info("Aguardando o upload de planilhas...")
