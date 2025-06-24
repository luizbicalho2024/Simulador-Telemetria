import streamlit as st
import pandas as pd
import io

def processar_planilha_ajustada(uploaded_file):
    """
    Versão final ajustada: lê da linha 11, remove nomes de usuário, ignora '0'
    e compacta os e-mails para a esquerda.
    """
    try:
        # --- ETAPA 1: LEITURA COM CABEÇALHO FIXO NA LINHA 11 ---
        st.info("Iniciando... Lendo o arquivo com o cabeçalho fixo na linha 11.")
        df = pd.read_excel(uploaded_file, header=10)
        
        # --- ETAPA 2: LIMPEZA E PADRONIZAÇÃO INTERNA ---
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
        df.dropna(axis='rows', how='all', inplace=True)
        
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'razão social': 'nome_cliente', 'nome do cliente': 'nome_cliente',
            'cnpj': 'cpf_cnpj', 'cpf/cnpj': 'cpf_cnpj',
            'tipo cliente': 'tipo_cliente', 'tipo de cliente': 'tipo_cliente',
            'telefone': 'telefone', 'fone': 'telefone'
        }
        df.rename(columns=rename_map, inplace=True)

        if 'tipo_cliente' not in df.columns:
            st.error("ERRO CRÍTICO: A coluna 'Tipo Cliente' não foi encontrada na linha 11. Verifique o arquivo Excel.")
            return None
            
        # --- ETAPA 3: AGRUPAMENTO POR MARCADOR 'JURÍDICA' ---
        df['tipo_cliente'] = df['tipo_cliente'].astype(str).str.strip()
        is_new_client = df['tipo_cliente'].str.contains('Jurídica|Jurídico', case=False)
        
        if not is_new_client.any():
            st.error("ERRO CRÍTICO: Nenhum marcador 'Jurídica' foi encontrado na coluna 'Tipo Cliente'.")
            return None

        df['client_group_id'] = is_new_client.cumsum()
        
        client_groups = df[df['client_group_id'] > 0].groupby('client_group_id')
        st.success(f"Análise completa. Encontrados {len(client_groups)} blocos de clientes para processar.")
        
        all_clients_data = []

        # --- ETAPA 4: PROCESSAMENTO AJUSTADO DE CADA GRUPO ---
        for group_id, group_df in client_groups:
            if group_df.empty:
                continue

            main_row = group_df.iloc[0]
            
            client_data = {
                'nome_cliente': main_row.get('nome_cliente'),
                'cpf_cnpj': main_row.get('cpf_cnpj'),
                'tipo_cliente': 'Pessoa Jurídica',
                'telefone': main_row.get('telefone')
            }
            
            # Coleta todos os emails válidos do grupo
            valid_emails = []
            user_rows = group_df.iloc[1:]
            
            for _, user_row in user_rows.iterrows():
                # A linha é de um usuário se tiver algo na coluna 'nome_cliente'
                user_name_check = user_row.get('nome_cliente')
                if pd.notna(user_name_check) and str(user_name_check).strip() != '':
                    
                    email = user_row.get('cpf_cnpj')
                    
                    # Verifica se o email é válido (não é nulo, vazio ou '0')
                    if pd.notna(email) and str(email).strip() not in ['', '0']:
                        valid_emails.append(email)
            
            # Adiciona os emails coletados em colunas sequenciais
            for i, email in enumerate(valid_emails):
                client_data[f'Email Usuário {i + 1}'] = email
                
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
        # A ordenação agora pega apenas as colunas de Email
        cols_usuarios = sorted([col for col in final_df.columns if col.startswith('Email Usuário')])
        
        return final_df[cols_principais + cols_usuarios]

    except Exception as e:
        st.error(f"UM ERRO INESPERADO OCORREU: {e}")
        st.error("Verifique se o arquivo é um Excel (.xlsx) válido e se a linha 11 realmente contém os cabeçalhos.")
        return None

def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="✅", layout="wide")
st.title("✅ Organizador de Planilhas de Clientes")
st.write(
    "Versão final: Lê os dados **a partir da linha 11**, usa o marcador 'Jurídica' para agrupar, e exibe apenas os e-mails dos usuários, ignorando valores '0'."
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo da planilha", type=['xlsx', 'csv'], accept_multiple_files=False
)

if uploaded_file:
    final_df = processar_planilha_ajustada(uploaded_file)
    
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
        st.error("O processamento falhou. Verifique as mensagens de erro e o arquivo de origem.")
else:
    st.info("Aguardando o upload de um arquivo...")
