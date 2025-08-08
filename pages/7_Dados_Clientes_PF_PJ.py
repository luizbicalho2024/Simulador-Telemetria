# pages/7_Dados_Clientes_PF_PJ.py
import streamlit as st
import pandas as pd
import io
import re
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Organizador de Planilhas",
    page_icon="📊"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES DE APOIO ---
def is_valid_email(email_text):
    if not isinstance(email_text, str): return False
    email_text = email_text.strip()
    if not email_text or email_text.lower() in ['e-mail', 'email', 'cpf/cnpj']: return False
    email_regex = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
    return re.fullmatch(email_regex, email_text) is not None

@st.cache_data
def processar_planilha_final(uploaded_file):
    """
    Processa a planilha de clientes lendo diretamente a partir da linha 12.
    """
    try:
        # Lê a planilha assumindo que o cabeçalho está na linha 12 (índice 11)
        df = pd.read_excel(uploaded_file, header=11)
        
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
        df.dropna(axis='rows', how='all', inplace=True)
        
        df.columns = df.columns.str.strip().str.lower()
        
        rename_map = {
            'razão social': 'nome_cliente', 'nome do cliente': 'nome_cliente',
            'cnpj': 'cpf_cnpj', 'cpf/cnpj': 'cpf_cnpj',
            'tipo cliente': 'tipo_cliente', 'tipo de cliente': 'tipo_cliente', 'tipo': 'tipo_cliente',
            'telefone': 'telefone', 'fone': 'telefone'
        }
        df.rename(columns=rename_map, inplace=True)

        if 'tipo_cliente' not in df.columns:
            st.error("ERRO CRÍTICO: A coluna 'Tipo Cliente' (ou uma variação como 'Tipo') não foi encontrada no cabeçalho. Verifique a linha 12 do seu ficheiro.")
            st.write("Colunas encontradas:", df.columns.tolist())
            return None
        
        df['tipo_cliente'] = df['tipo_cliente'].astype(str).str.strip()
        is_new_client = df['tipo_cliente'].str.contains('Jurídica|Jurídico|Física', case=False, na=False)
        
        if not is_new_client.any():
            st.error("ERRO CRÍTICO: Nenhum marcador ('Jurídica' ou 'Física') foi encontrado na coluna 'Tipo Cliente'.")
            return None

        df['client_group_id'] = is_new_client.cumsum()
        
        client_groups = df[df['client_group_id'] > 0].groupby('client_group_id')
        all_clients_data = []

        for group_id, group_df in client_groups:
            if group_df.empty: continue
            main_row = group_df.iloc[0]
            final_type = 'Pessoa Física' if 'física' in str(main_row.get('tipo_cliente')).lower() else 'Pessoa Jurídica'
            
            client_data = {
                'nome_cliente': main_row.get('nome_cliente'), 'cpf_cnpj': main_row.get('cpf_cnpj'),
                'tipo_cliente': final_type, 'telefone': main_row.get('telefone')
            }
            
            valid_emails = []
            for _, user_row in group_df.iloc[1:].iterrows():
                if pd.notna(user_row.get('nome_cliente')) and str(user_row.get('nome_cliente')).strip() != '':
                    if is_valid_email(user_row.get('cpf_cnpj')):
                        valid_emails.append(str(user_row.get('cpf_cnpj')).strip())
            
            for i, email in enumerate(valid_emails):
                client_data[f'Email Usuário {i + 1}'] = email
            
            all_clients_data.append(client_data)

        if not all_clients_data: return None

        final_df = pd.DataFrame(all_clients_data)
        final_rename_map = {
            'nome_cliente': 'Nome do Cliente', 'cpf_cnpj': 'CPF/CNPJ',
            'tipo_cliente': 'Tipo Cliente', 'telefone': 'Telefone',
        }
        final_df.rename(columns=final_rename_map, inplace=True)
        
        cols_principais = ['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Telefone']
        email_cols = sorted([col for col in final_df.columns if col.startswith('Email Usuário')], key=lambda col: int(col.split(' ')[-1]))
        
        return final_df[cols_principais + email_cols]
    except Exception as e:
        st.error(f"UM ERRO INESPERADO OCORREU: {e}")
        st.info("Verifique se o ficheiro está formatado corretamente e se o cabeçalho da tabela está na linha 12.")
        return None

def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes_Organizados')
    return output.getvalue()

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>📊 Organizador de Planilhas de Clientes</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

# --- 4. CONTEÚDO PRINCIPAL ---
st.write(
    "Faça o upload da sua planilha. A aplicação irá ler os dados a partir da linha 12, agrupar por 'Jurídica' ou 'Física', validar e-mails e organizar os dados."
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo da planilha", type=['xlsx'], key="organizer_upload"
)

if uploaded_file:
    st.markdown("---")
    final_df = processar_planilha_final(uploaded_file)
    
    if final_df is not None and not final_df.empty:
        st.toast("Processamento concluído com sucesso!", icon="✅")
        st.dataframe(final_df.fillna(''))
        
        umdb.add_log(st.session_state["username"], "Processou Planilha de Clientes", details={"ficheiro": uploaded_file.name, "linhas_processadas": len(final_df)})
        
        st.download_button(
            label="📥 Baixar Planilha Final (.xlsx)",
            data=to_excel(final_df),
            file_name='relatorio_clientes_final.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("O processamento falhou. Verifique as mensagens de erro acima e a estrutura do seu ficheiro.")
else:
    st.info("Aguardando o upload de um arquivo para iniciar a análise.")
