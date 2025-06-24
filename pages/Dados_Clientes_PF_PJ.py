import streamlit as st
import pandas as pd
import io
import re  # Módulo para validação com Expressões Regulares (Regex)

def is_valid_email(email_text):
    """
    Função robusta para validar se uma string tem o formato de um e-mail.
    """
    if not isinstance(email_text, str):
        return False
    
    email_text = email_text.strip()
    if not email_text:
        return False
        
    if email_text.lower() in ['e-mail', 'email', 'cpf/cnpj']:
        return False

    email_regex = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
    
    return re.fullmatch(email_regex, email_text) is not None


def processar_planilha_final(uploaded_file):
    """
    Versão final que processa tanto clientes Pessoa Jurídica quanto Física,
    usando seus respectivos marcadores para agrupamento.
    """
    try:
        # ETAPA 1: Leitura com cabeçalho fixo na linha 11
        st.info("Iniciando... Lendo o arquivo com o cabeçalho fixo na linha 11.")
        df = pd.read_excel(uploaded_file, header=10)
        
        # ETAPA 2: Limpeza e padronização
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
            st.error("ERRO CRÍTICO: A coluna 'Tipo Cliente' não foi encontrada na linha 11.")
            return None
            
        # ETAPA 3: Agrupamento por Marcador 'JURÍDICA' OU 'FÍSICA'
        df['tipo_cliente'] = df['tipo_cliente'].astype(str).str.strip()
        # A regra agora inclui 'Física' como um iniciador de novo cliente
        is_new_client = df['tipo_cliente'].str.contains('Jurídica|Jurídico|Física', case=False)
        
        if not is_new_client.any():
            st.error("ERRO CRÍTICO: Nenhum marcador ('Jurídica' ou 'Física') foi encontrado na coluna 'Tipo Cliente'.")
            return None

        df['client_group_id'] = is_new_client.cumsum()
        
        client_groups = df[df['client_group_id'] > 0].groupby('client_group_id')
        st.success(f"Análise completa. Encontrados {len(client_groups)} blocos de clientes para processar.")
        
        all_clients_data = []

        # ETAPA 4: Processamento de cada grupo
        for group_id, group_df in client_groups:
            if group_df.empty:
                continue

            main_row = group_df.iloc[0]
            
            # Determina o tipo de cliente (Física ou Jurídica) com base no marcador da linha
            client_type_from_row = str(main_row.get('tipo_cliente')).lower()
            if 'física' in client_type_from_row:
                final_type = 'Pessoa Física'
            else:
                final_type = 'Pessoa Jurídica'
            
            client_data = {
                'nome_cliente': main_row.get('nome_cliente'),
                'cpf_cnpj': main_row.get('cpf_cnpj'),
                'tipo_cliente': final_type, # Usa o tipo determinado
                'telefone': main_row.get('telefone')
            }
            
            valid_emails = []
            user_rows = group_df.iloc[1:]
            
            for _, user_row in user_rows.iterrows():
                user_name_check = user_row.get('nome_cliente')
                if pd.notna(user_name_check) and str(user_name_check).strip() != '':
                    
                    potential_email = user_row.get('cpf_cnpj')
                    
                    if is_valid_email(potential_email):
                        valid_emails.append(potential_email.strip())
            
            for i, email in enumerate(valid_emails):
                client_data[f'Email Usuário {i + 1}'] = email
                
            all_clients_data.append(client_data)

        if not all_clients_data:
            st.warning("O processamento terminou, mas nenhum dado de cliente foi extraído.")
            return None

        final_df = pd.DataFrame(all_clients_data)

        # ETAPA 5: Formatação final e ordenação
        final_rename_map = {
            'nome_cliente': 'Nome do Cliente',
            'cpf_cnpj': 'CPF/CNPJ',
            'tipo_cliente': 'Tipo Cliente',
            'telefone': 'Telefone',
        }
        final_df.rename(columns=final_rename_map, inplace=True)
        
        cols_principais = ['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone']
        
        email_cols = [col for col in final_df.columns if col.startswith('Email Usuário')]
        cols_usuarios_ordenados = sorted(email_cols, key=lambda col: int(col.split(' ')[-1]))
        
        return final_df[cols_principais + cols_usuarios_ordenados]

    except Exception as e:
        st.error(f"UM ERRO INESPERADO OCORREU: {e}")
        return None

def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- Interface do Streamlit ---
st.set_page_config(page_title="Organizador de Planilhas", page_icon="🏆", layout="wide")
st.title("🏆 Organizador de Planilhas de Clientes (PF e PJ)")
st.write(
    "Versão Final: Lê os dados **a partir da linha 11**, agrupa por 'Jurídica' ou 'Física', valida cada e-mail e ordena as colunas de usuário."
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
        st.error("O processamento falhou ou não encontrou dados válidos. Verifique o arquivo de origem.")
else:
    st.info("Aguardando o upload de um arquivo...")
