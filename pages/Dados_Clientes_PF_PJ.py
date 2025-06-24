import streamlit as st
import pandas as pd
import io

def processar_planilha_final(uploaded_file):
    """
    Script definitivo que lê o cabeçalho da linha 11 e entende que os dados de usuário
    estão nas mesmas colunas que os dados do cliente, mas em linhas subsequentes.
    """
    try:
        # --- ETAPA 1: LEITURA COM CABEÇALHO FIXO NA LINHA 11 ---
        st.info("Iniciando... Lendo o arquivo com o cabeçalho fixo na linha 11.")
        # header=10 significa que a linha 11 da planilha será usada como cabeçalho
        df = pd.read_excel(uploaded_file, header=10)
        
        # --- ETAPA 2: LIMPEZA E PADRONIZAÇÃO INTERNA ---
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
        df.dropna(axis='rows', how='all', inplace=True)
        
        st.markdown("#### Diagnóstico 1: Dados Brutos Lidos a Partir da Linha 11")
        st.dataframe(df.head(10).fillna(''))

        # Padroniza nomes de colunas para um formato interno estável (minúsculas)
        # Importante: Mantemos apenas os nomes que sabemos que existem.
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'razão social': 'nome_cliente', 'nome do cliente': 'nome_cliente',
            'cnpj': 'cpf_cnpj', 'cpf/cnpj': 'cpf_cnpj',
            'tipo cliente': 'tipo_cliente', 'tipo de cliente': 'tipo_cliente',
            'telefone': 'telefone', 'fone': 'telefone'
        }
        df.rename(columns=rename_map, inplace=True)

        st.markdown("#### Diagnóstico 2: Colunas Após Padronização")
        st.write(df.columns.tolist())

        # Verificação crítica da coluna que serve como marcador
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
        st.success(f"Análise inicial completa. Encontrados {len(client_groups)} blocos de clientes para processar.")
        
        all_clients_data = []

        # --- ETAPA 4: PROCESSAMENTO DE CADA GRUPO COM A LÓGICA CORRETA ---
        for group_id, group_df in client_groups:
            if group_df.empty:
                continue

            # A primeira linha do grupo contém os dados do cliente
            main_row = group_df.iloc[0]
            
            client_data = {
                'nome_cliente': main_row.get('nome_cliente'),
                'cpf_cnpj': main_row.get('cpf_cnpj'),
                'tipo_cliente': 'Pessoa Jurídica',
                'telefone': main_row.get('telefone')
            }
            
            # As linhas SEGUINTES (a partir da segunda) contêm os dados dos usuários
            user_rows = group_df.iloc[1:]
            
            user_num = 1
            for _, user_row in user_rows.iterrows():
                # A MÁGICA ACONTECE AQUI:
                # O nome do usuário está na coluna 'nome_cliente' desta linha
                # O email do usuário está na coluna 'cpf_cnpj' desta linha
                user_name = user_row.get('nome_cliente')
                user_email = user_row.get('cpf_cnpj')
                
                # Adiciona o usuário apenas se um nome de usuário for encontrado
                if pd.notna(user_name) and user_name.strip() != '':
                    client_data[f'Nome Usuário {user_num}'] = user_name
                    client_data[f'Email Usuário {user_num}'] = user_email
                    user_num += 1
                
            all_clients_data.append(client_data)

        if not all_clients_data:
            st.warning("O processamento terminou, mas nenhum dado de cliente foi extraído.")
            return None

        final_df = pd.DataFrame(all_clients_data)

        # --- ETAPA 5: FORMATAÇÃO FINAL PARA EXIBIÇÃO ---
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
    "Este script está configurado para ler os dados **a partir da linha 11** da sua planilha e usar o marcador 'Jurídica' na coluna 'Tipo Cliente' para estruturar os dados."
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
        st.error("O processamento falhou. Verifique as mensagens de erro e os diagnósticos acima.")
else:
    st.info("Aguardando o upload de um arquivo...")
