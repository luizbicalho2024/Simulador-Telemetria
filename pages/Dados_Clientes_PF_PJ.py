import streamlit as st
import pandas as pd
import io

def processar_planilha_definitivo(uploaded_file):
    """
    Processa a planilha usando a coluna 'Tipo Cliente' como marcador de início de um novo cliente.
    Esta versão usa uma padronização interna de colunas para máxima robustez.
    """
    st.info(f"Iniciando processamento definitivo do arquivo: `{uploaded_file.name}`")
    
    try:
        # --- ETAPA 1: Leitura e Padronização para um formato interno ---
        df = pd.read_excel(uploaded_file)
        
        # Limpeza de colunas e linhas vazias que o Excel pode criar
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.dropna(axis='rows', how='all', inplace=True)
        
        # Guarda os nomes originais para diagnóstico
        original_columns = df.columns.tolist()
        
        # Converte os nomes das colunas para um padrão interno (minúsculas, sem espaços/acentos)
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapeia todas as variações possíveis para um nome interno único e estável
        rename_map_internal = {
            'razão social': 'nome_cliente', 'nome do cliente': 'nome_cliente',
            'cnpj': 'cpf_cnpj', 'cpf/cnpj': 'cpf_cnpj',
            'tipo cliente': 'tipo_cliente', 'tipo de cliente': 'tipo_cliente',
            'nome de usuário': 'nome_usuario', 'usuário': 'nome_usuario', 'nome de usuario': 'nome_usuario',
            'email': 'email', 'e-mail': 'email',
            'telefone': 'telefone', 'fone': 'telefone'
        }
        df.rename(columns=rename_map_internal, inplace=True)

        st.markdown("#### Diagnóstico")
        st.write("**Colunas Originais Lidas:**", original_columns)
        st.write("**Colunas Padronizadas (usadas internamente):**", df.columns.tolist())

        # Verificação crítica usando o nome interno padronizado
        if 'tipo_cliente' not in df.columns:
            st.error("ERRO CRÍTICO: A coluna 'Tipo Cliente' é essencial e não foi encontrada. Verifique o arquivo Excel.")
            return None
            
        # --- ETAPA 2: Criação dos Grupos de Clientes com Base no Marcador ---
        is_new_client = df['tipo_cliente'].str.contains('Jurídica|Jurídico', case=False, na=False)
        df['client_group_id'] = is_new_client.cumsum()
        
        client_groups = df[df['client_group_id'] > 0].groupby('client_group_id')
        
        all_clients_data = []

        # --- ETAPA 3: Processamento de Cada Grupo de Cliente ---
        for group_id, group_df in client_groups:
            main_row = group_df.iloc[0]
            
            # Busca o primeiro telefone válido em todo o grupo do cliente
            telefones = group_df['telefone'].dropna().astype(str).unique()
            
            client_data = {
                'nome_cliente': main_row.get('nome_cliente'),
                'cpf_cnpj': main_row.get('cpf_cnpj'),
                'tipo_cliente': 'Pessoa Jurídica',
                'telefone': ', '.join(telefones) if len(telefones) > 0 else None
            }
            
            # Filtra as linhas de usuário que possuem um nome de usuário
            users_df = group_df[group_df['nome_usuario'].notna()].reset_index(drop=True)
            
            for i, user_row in users_df.iterrows():
                user_num = i + 1
                client_data[f'Nome Usuário {user_num}'] = user_row.get('nome_usuario')
                client_data[f'Email Usuário {user_num}'] = user_row.get('email')
                
            all_clients_data.append(client_data)

        if not all_clients_data:
            st.warning("Nenhum cliente com o marcador 'Jurídica' foi encontrado no arquivo.")
            return None

        final_df = pd.DataFrame(all_clients_data)

        # --- ETAPA 4: Formatação Final para o Usuário ---
        # Renomeia as colunas do formato interno para o formato de exibição final
        final_rename_map_output = {
            'nome_cliente': 'Nome do Cliente',
            'cpf_cnpj': 'CPF/CNPJ',
            'tipo_cliente': 'Tipo Cliente',
            'telefone': 'Telefone',
        }
        final_df.rename(columns=final_rename_map_output, inplace=True)
        
        # Garante a ordem correta das colunas
        cols_principais = ['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone']
        cols_usuarios = sorted([col for col in final_df.columns if col.startswith('Nome Usuário') or col.startswith('Email Usuário')])
        
        ordem_final = cols_principais + cols_usuarios
        return final_df[ordem_final]

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado e crítico durante o processamento: {e}")
        st.error("Por favor, verifique se o arquivo Excel não está corrompido e se a primeira linha de dados contém os cabeçalhos.")
        return None

def to_excel(df: pd.DataFrame):
    """Converte um DataFrame para um arquivo Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="📊", layout="wide")
st.title("⚙️ Organizador de Clientes por Marcador")
st.write(
    "Faça o upload da sua planilha. A aplicação usará a coluna **'Tipo Cliente'** para identificar o início de cada cliente "
    "e irá reestruturar os dados no formato final."
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo da planilha (XLSX ou CSV)", type=['xlsx', 'csv'], accept_multiple_files=False
)

if uploaded_file:
    final_df = processar_planilha_definitivo(uploaded_file)
    
    if final_df is not None and not final_df.empty:
        st.success("✅ Processamento concluído com sucesso!")
        st.dataframe(final_df.fillna(''))
        
        st.download_button(
            label="📥 Baixar Planilha Final (.xlsx)",
            data=to_excel(final_df),
            file_name='relatorio_clientes_final.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("Não foi possível gerar a tabela final. Verifique os diagnósticos e o arquivo de origem.")
else:
    st.info("Aguardando o upload de um arquivo...")
