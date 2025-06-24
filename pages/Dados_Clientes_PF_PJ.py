import streamlit as st
import pandas as pd
import io

def processar_por_marcador(uploaded_file):
    """
    Processa a planilha usando a coluna 'Tipo Cliente' como marcador de início de um novo cliente.
    """
    st.info(f"Iniciando processamento por marcador: `{uploaded_file.name}`")
    
    try:
        # --- ETAPA 1: Leitura e Padronização ---
        df = pd.read_excel(uploaded_file)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.dropna(axis='rows', how='all', inplace=True)
        
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'nome do cliente': 'Nome do Cliente', 'razão social': 'Nome do Cliente',
            'cpf/cnpj': 'CPF/CNPJ', 'cnpj': 'CPF/CNPJ',
            'tipo cliente': 'Tipo Cliente', 'tipo de cliente': 'Tipo Cliente',
            'nome de usuário': 'Nome de Usuário', 'usuário': 'Nome de Usuário', 'nome de usuario': 'Nome de Usuário',
            'email': 'Email', 'e-mail': 'Email',
            'telefone': 'Telefone', 'fone': 'Telefone'
        }
        df.rename(columns=rename_map, inplace=True)

        st.markdown(f"#### Diagnóstico: Dados Lidos e Padronizados")
        st.dataframe(df.head(20).fillna(''))

        if 'Tipo Cliente' not in df.columns:
            st.error("ERRO CRÍTICO: A coluna 'Tipo Cliente' não foi encontrada. Esta coluna é essencial para o processamento.")
            return pd.DataFrame()
            
        # --- ETAPA 2: Criação dos Grupos de Clientes ---
        # Marca 'True' para cada linha que inicia um novo cliente
        is_new_client = df['Tipo Cliente'].str.contains('Jurídica|Jurídico', case=False, na=False)
        # Cria um ID de grupo que incrementa a cada novo cliente
        df['client_group_id'] = is_new_client.cumsum()
        
        # Filtra apenas os blocos que de fato pertencem a um cliente (ID > 0)
        client_groups = df[df['client_group_id'] > 0].groupby('client_group_id')
        
        all_clients_data = []

        # --- ETAPA 3: Processamento de Cada Grupo ---
        for group_id, group_df in client_groups:
            # Pega a primeira linha para os dados principais
            main_row = group_df.iloc[0]
            
            # Busca o primeiro telefone válido em todo o grupo do cliente
            first_valid_phone = group_df['Telefone'].dropna().astype(str).unique()
            
            client_data = {
                'Nome do Cliente': main_row.get('Nome do Cliente'),
                'CPF/CNPJ': main_row.get('CPF/CNPJ'),
                'Tipo Cliente': 'Pessoa Jurídica', # Definido pela regra
                'Telefone': ', '.join(first_valid_phone) if len(first_valid_phone) > 0 else None
            }
            
            # Filtra as linhas de usuário dentro do grupo
            users_df = group_df[group_df['Nome de Usuário'].notna()].reset_index(drop=True)
            
            # Adiciona colunas de usuário dinamicamente
            for i, user_row in users_df.iterrows():
                user_num = i + 1
                client_data[f'Nome Usuário {user_num}'] = user_row.get('Nome de Usuário')
                client_data[f'Email Usuário {user_num}'] = user_row.get('Email')
                
            all_clients_data.append(client_data)

        if not all_clients_data:
            st.warning("Nenhum cliente com o marcador 'Jurídica' foi encontrado no arquivo.")
            return pd.DataFrame()

        # --- ETAPA 4: Consolidação Final ---
        final_df = pd.DataFrame(all_clients_data)
        return final_df

    except Exception as e:
        st.error(f"Ocorreu um erro crítico durante o processamento: {e}")
        return pd.DataFrame()

def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Final')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="📊", layout="wide")
st.title("⚙️ Organizador de Clientes por Marcador")
st.write(
    "Faça o upload da sua planilha. A aplicação usará a coluna **'Tipo Cliente'** para identificar o início de cada cliente "
    "e irá reestruturar os dados no formato largo."
)

uploaded_files = st.file_uploader(
    "Selecione o arquivo da planilha", type=['xlsx', 'csv'], accept_multiple_files=False
)

if uploaded_files:
    final_df = processar_por_marcador(uploaded_files)
    
    if final_df is not None and not final_df.empty:
        st.success("✅ Processamento concluído com sucesso!")
        st.dataframe(final_df.fillna(''))
        
        st.download_button(
            "📥 Baixar Planilha Final (.xlsx)",
            to_excel(final_df),
            'relatorio_clientes_final.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("Não foi possível gerar a tabela final. Verifique os diagnósticos acima e o conteúdo do arquivo.")
else:
    st.info("Aguardando o upload de um arquivo...")
