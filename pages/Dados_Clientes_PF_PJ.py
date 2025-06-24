import streamlit as st
import pandas as pd
import io
import numpy as np

# --- Funções Auxiliares ---

def get_tipo_cliente(documento):
    """Analisa um documento (CPF ou CNPJ) e retorna o tipo de cliente."""
    if pd.isna(documento) or documento == '':
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
    Processa a planilha para um formato "largo", com colunas dinâmicas para cada usuário.
    VERSÃO CORRIGIDA E ROBUSTA.
    """
    st.info(f"Iniciando processamento para formato largo: `{uploaded_file.name}`")
    
    try:
        # --- ETAPA 1: Leitura e Limpeza Inicial ---
        df = pd.read_excel(uploaded_file, header=None)
        
        header_row = 0
        for i, row in df.head(15).iterrows():
            text_count = sum(1 for item in row if isinstance(item, str) and len(str(item)) > 1)
            if text_count > 2:
                header_row = i
                break
        
        df = pd.read_excel(uploaded_file, header=header_row)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # Remove colunas "Unnamed"
        df.dropna(axis='rows', how='all', inplace=True)

        st.markdown(f"#### Diagnóstico 1: Dados Brutos Lidos do Arquivo")
        st.dataframe(df.head(15).fillna(''))

        # --- ETAPA 2: Padronização das Colunas ---
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'nome': 'Nome do Cliente', 'razão social': 'Nome do Cliente',
            'cpf': 'CPF/CNPJ', 'cnpj': 'CPF/CNPJ',
            'nome de usuário': 'Nome de Usuário', 'usuário': 'Nome de Usuário', 'nome de usuario': 'Nome de Usuário',
            'e-mail': 'Email', 'email': 'Email', 'mail': 'Email',
            'fone': 'Telefone', 'telefone': 'Telefone', 'celular': 'Telefone'
        }
        df.rename(columns=rename_map, inplace=True)
        
        st.markdown(f"#### Diagnóstico 2: Colunas Após Padronização")
        st.write(df.columns.tolist())

        # --- ETAPA 3: Associação de Usuários a Clientes ---
        id_cols = ['Nome do Cliente', 'CPF/CNPJ']
        for col in id_cols:
            if col not in df.columns:
                st.error(f"ERRO CRÍTICO: Coluna essencial '{col}' não foi encontrada após a padronização. Verifique os nomes no arquivo original.")
                return pd.DataFrame()
        
        df[id_cols] = df[id_cols].ffill()
        df.replace('', np.nan, inplace=True)

        # --- ETAPA 4: Separação, Transformação e Junção ---
        # Pega a lista única de clientes
        df_clients = df[id_cols].drop_duplicates(keep='first').reset_index(drop=True)

        # Pega o telefone principal (primeira ocorrência não nula para cada cliente)
        telefones = df.dropna(subset=['Telefone']).drop_duplicates(subset=id_cols, keep='first')
        df_clients = df_clients.merge(telefones[[*id_cols, 'Telefone']], on=id_cols, how='left')

        # Isola as linhas de usuário (qualquer linha com um 'Nome de Usuário')
        df_users = df[df['Nome de Usuário'].notna()].copy()
        
        if not df_users.empty:
            # Numera os usuários dentro de cada grupo de cliente
            df_users['user_num'] = df_users.groupby(id_cols).cumcount() + 1
            
            # Pivota a tabela
            pivoted_users = df_users.pivot_table(
                index=id_cols,
                columns='user_num',
                values=['Nome de Usuário', 'Email'],
                aggfunc='first'
            )
            
            # Renomeia e achata as colunas
            pivoted_users.columns = [f'{val[0].replace("Email", "Email Usuário")} {val[1]}' for val in pivoted_users.columns]
            
            # Junta os dados dos clientes com seus respectivos usuários
            df_clients = df_clients.merge(pivoted_users, on=id_cols, how='left')
        else:
            st.warning("Nenhuma linha com 'Nome de Usuário' foi encontrada para criar colunas de usuário.")

        # --- ETAPA 5: Finalização ---
        df_clients['Tipo Cliente'] = df_clients['CPF/CNPJ'].apply(get_tipo_cliente)
        
        cols_principais = ['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone']
        cols_usuarios = sorted([col for col in df_clients.columns if col.startswith('Nome Usuário') or col.startswith('Email Usuário')])
        
        ordem_final = cols_principais + cols_usuarios
        return df_clients[ordem_final]

    except Exception as e:
        st.error(f"Ocorreu um erro crítico ao processar o arquivo: {e}")
        st.error("Verifique se o arquivo não está corrompido e se o formato das colunas está correto.")
        return pd.DataFrame()


def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Final')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="📊", layout="wide")
st.title("⚙️ Transformador de Planilhas para Formato Largo")
st.write("Faça o upload da sua planilha. A aplicação irá converter os dados para um formato com uma linha por cliente e colunas sequenciais para os usuários.")

uploaded_files = st.file_uploader(
    "Selecione os arquivos", type=['xlsx', 'csv'], accept_multiple_files=True
)

if uploaded_files:
    all_dfs = [processar_para_formato_largo(file) for file in uploaded_files]
    valid_dfs = [df for df in all_dfs if df is not None and not df.empty]
    
    if valid_dfs:
        final_combined_df = pd.concat(valid_dfs, ignore_index=True)
        st.success("✅ Transformação concluída! Veja os dados abaixo.")
        st.dataframe(final_combined_df.fillna(''))
        
        st.download_button(
            "📥 Baixar Planilha Final (.xlsx)",
            to_excel(final_combined_df),
            'relatorio_clientes_final.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("Nenhum dado válido foi extraído dos arquivos. Verifique os diagnósticos acima.")
else:
    st.info("Aguardando o upload de planilhas...")
