import streamlit as st
import pandas as pd
import io

def processar_planilha_final(uploaded_file):
    """
    Script definitivo para processar a planilha. Inclui detecção automática de cabeçalho
    e uma lógica de agrupamento robusta baseada em marcadores.
    """
    try:
        # --- ETAPA 1: DETECÇÃO AUTOMÁTICA DE CABEÇALHO ---
        st.info("Iniciando... Tentando encontrar o cabeçalho da planilha.")
        file_buffer = io.BytesIO(uploaded_file.getvalue())
        header_row = None
        
        for i in range(15):  # Tenta encontrar o cabeçalho nas primeiras 15 linhas
            try:
                df_test = pd.read_excel(file_buffer, header=i, nrows=1)
                file_buffer.seek(0)
                # Um cabeçalho válido deve ter várias colunas com nomes em formato de texto
                if len([col for col in df_test.columns if isinstance(col, str)]) > 3:
                    header_row = i
                    st.success(f"Cabeçalho encontrado na linha {i + 1}.")
                    break
            except Exception:
                file_buffer.seek(0)
                continue
        
        if header_row is None:
            st.error("ERRO CRÍTICO: Não foi possível encontrar um cabeçalho válido nas primeiras 15 linhas do arquivo.")
            return None

        df = pd.read_excel(file_buffer, header=header_row)
        
        # --- ETAPA 2: LIMPEZA E PADRONIZAÇÃO INTERNA ---
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
        df.dropna(axis='rows', how='all', inplace=True)
        
        st.markdown("#### Diagnóstico 1: Dados Brutos Lidos (10 Primeiras Linhas)")
        st.dataframe(df.head(10).fillna(''))

        original_columns = df.columns.tolist()
        df.columns = df.columns.str.strip().str.lower()
        
        rename_map = {
            'razão social': 'nome_cliente', 'nome do cliente': 'nome_cliente',
            'cnpj': 'cpf_cnpj', 'cpf/cnpj': 'cpf_cnpj',
            'tipo cliente': 'tipo_cliente', 'tipo de cliente': 'tipo_cliente',
            'nome de usuário': 'nome_usuario', 'usuário': 'nome_usuario', 'nome de usuario': 'nome_usuario',
            'email': 'email', 'e-mail': 'email',
            'telefone': 'telefone', 'fone': 'telefone'
        }
        df.rename(columns=rename_map, inplace=True)

        st.markdown("#### Diagnóstico 2: Nomes das Colunas")
        st.write("**Colunas Originais Lidas:**", original_columns)
        st.write("**Colunas Padronizadas para Processamento:**", df.columns.tolist())

        if 'tipo_cliente' not in df.columns:
            st.error("ERRO CRÍTICO: A coluna 'Tipo Cliente' é essencial e não foi encontrada após a padronização.")
            return None
            
        # --- ETAPA 3: AGRUPAMENTO POR MARCADOR 'JURÍDICA' ---
        df['tipo_cliente'] = df['tipo_cliente'].astype(str).str.strip()
        is_new_client = df['tipo_cliente'].str.contains('Jurídica|Jurídico', case=False, na=False)
        
        if not is_new_client.any():
            st.error("ERRO CRÍTICO: Nenhum marcador 'Jurídica' ou 'Jurídico' foi encontrado na coluna 'Tipo Cliente'. Não é possível agrupar os dados.")
            return None

        df['client_group_id'] = is_new_client.cumsum()
        
        st.markdown("#### Diagnóstico 3: Agrupamento de Clientes")
        st.write("A coluna 'client_group_id' mostra como as linhas foram agrupadas. Cada número representa um cliente.")
        st.dataframe(df[df['client_group_id'] > 0][['nome_cliente', 'tipo_cliente', 'client_group_id']].head(20).fillna(''))

        client_groups = df[df['client_group_id'] > 0].groupby('client_group_id')
        st.success(f"Análise inicial completa. Encontrados {len(client_groups)} blocos de clientes para processar.")
        
        all_clients_data = []

        # --- ETAPA 4: PROCESSAMENTO DE CADA GRUPO ---
        for group_id, group_df in client_groups:
            main_row = group_df.iloc[0]
            telefones = group_df['telefone'].dropna().astype(str).unique()
            
            client_data = {
                'nome_cliente': main_row.get('nome_cliente'),
                'cpf_cnpj': main_row.get('cpf_cnpj'),
                'tipo_cliente': 'Pessoa Jurídica',
                'telefone': ', '.join(telefones) if len(telefones) > 0 else None
            }
            
            users_df = group_df[group_df['nome_usuario'].notna()].reset_index(drop=True)
            
            for i, user_row in users_df.iterrows():
                user_num = i + 1
                client_data[f'Nome Usuário {user_num}'] = user_row.get('nome_usuario')
                client_data[f'Email Usuário {user_num}'] = user_row.get('email')
                
            all_clients_data.append(client_data)

        if not all_clients_data:
            st.warning("O processamento terminou, mas nenhum dado de cliente foi extraído.")
            return None

        final_df = pd.DataFrame(all_clients_data)

        # --- ETAPA 5: FORMATAÇÃO FINAL ---
        final_rename_map = {
            'nome_cliente': 'Nome do Cliente',
            'cpf_cnpj': 'CPF/CNPJ',
            'tipo_cliente': 'Tipo Cliente',
            'telefone': 'Telefone',
        }
        final_df.rename(columns=final_rename_map, inplace=True)
        
        cols_principais = ['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone']
        cols_usuarios = sorted([col for col in final_df.columns if col.startswith('Nome Usuário') or col.startswith('Email Usuário')])
        
        return final_df[cols_principais + cols_usuarios]

    except Exception as e:
        st.error(f"UM ERRO INESPERADO OCORREU: {e}")
        st.error("Verifique se o arquivo enviado é um Excel (.xlsx) válido e não está protegido por senha.")
        return None

def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="🚀", layout="wide")
st.title("🚀 Organizador de Planilhas de Clientes (Versão de Alta Robustez)")
st.write(
    "Faça o upload da sua planilha. Esta versão avançada detecta o cabeçalho automaticamente e usa o marcador 'Jurídica' na coluna 'Tipo Cliente' para estruturar os dados."
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo da planilha", type=['xlsx', 'csv'], accept_multiple_files=False
)

if uploaded_file:
    final_df = processar_planilha_final(uploaded_file)
    
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
        st.error("O processamento falhou. Verifique as mensagens de erro e os diagnósticos acima para identificar a causa.")
else:
    st.info("Aguardando o upload de um arquivo...")
