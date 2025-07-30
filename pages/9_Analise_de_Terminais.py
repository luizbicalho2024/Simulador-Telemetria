# pages/Analise_de_Terminais.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Análise de Terminais",
    page_icon="📡"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO AUXILIAR ---
def processar_planilha_terminais(uploaded_file):
    """
    Lê a planilha, extrai o nome do cliente da linha 9, coluna 5,
    lê os dados da tabela, e realiza a análise de status.
    """
    df_cliente = pd.read_excel(uploaded_file, header=None, skiprows=8, nrows=1, engine='openpyxl')
    
    nome_cliente = "Cliente não identificado"
    if not df_cliente.empty and len(df_cliente.columns) > 4:
        nome_cliente_raw = df_cliente.iloc[0, 4]
        if pd.notna(nome_cliente_raw):
            nome_cliente = str(nome_cliente_raw).strip()

    df_terminais = pd.read_excel(uploaded_file, header=11, engine='openpyxl')

    df_terminais = df_terminais.rename(columns={
        'Última Transmissão': 'Data Transmissão',
        'Rastreador Modelo': 'Modelo'
    })

    required_cols = ['Terminal', 'Placa', 'Rastreador', 'Modelo', 'Data Transmissão']
    if not all(col in df_terminais.columns for col in required_cols):
        st.error(f"O ficheiro não contém todas as colunas necessárias. Verifique se o cabeçalho na linha 12 contém os nomes corretos.")
        st.write("Colunas encontradas:", df_terminais.columns.tolist())
        return None, None

    df_terminais.dropna(subset=['Terminal'], inplace=True)
    df_terminais['Data Transmissão'] = pd.to_datetime(df_terminais['Data Transmissão'], errors='coerce')
    df_terminais.dropna(subset=['Data Transmissão'], inplace=True)

    dez_dias_atras = datetime.now() - timedelta(days=10)
    df_terminais['Status_Atualizacao'] = df_terminais['Data Transmissão'].apply(
        lambda data: "Atualizado" if data >= dez_dias_atras else "Desatualizado"
    )
    
    return nome_cliente, df_terminais

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>📡 Análise de Status de Terminais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório")
st.info("Por favor, carregue o ficheiro `lista_de_terminais.xlsx` exportado do sistema.")

uploaded_file = st.file_uploader(
    "Selecione o relatório de terminais",
    type=['xlsx']
)

st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO ---
if uploaded_file:
    try:
        nome_cliente, df_analise = processar_planilha_terminais(uploaded_file)
        
        if nome_cliente is not None and df_analise is not None:
            st.header(f"Cliente: {nome_cliente}")
            
            df_atualizados = df_analise[df_analise['Status_Atualizacao'] == 'Atualizado']
            df_desatualizados = df_analise[df_analise['Status_Atualizacao'] == 'Desatualizado']
            
            col1, col2 = st.columns(2)
            col1.metric(
                label="✅ Total de Terminais Atualizados",
                value=len(df_atualizados),
                help="Terminais que transmitiram nos últimos 10 dias."
            )
            col2.metric(
                label="⚠️ Total de Terminais Desatualizados",
                value=len(df_desatualizados),
                help="Terminais que não transmitem há mais de 10 dias."
            )

            st.markdown("---")
            
            st.subheader("Lista de Terminais Desatualizados")
            if not df_desatualizados.empty:
                st.warning("Atenção: Os terminais abaixo precisam de verificação.")
                st.dataframe(
                    df_desatualizados[['Terminal', 'Placa', 'Rastreador', 'Modelo', 'Data Transmissão']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Data Transmissão": st.column_config.DatetimeColumn(
                            "Data da Última Transmissão",
                            format="DD/MM/YYYY HH:mm:ss"
                        )
                    }
                )

                # ***** NOVA SECÇÃO: MODELO DE E-MAIL *****
                st.markdown("---")
                st.subheader("📧 Modelo de E-mail para o Cliente")
                st.info("Copie o conteúdo abaixo para enviar uma notificação ao cliente.")

                # Cria a lista de veículos para o corpo do e-mail
                lista_veiculos_str = ""
                for index, row in df_desatualizados.iterrows():
                    placa = row['Placa']
                    data_transmissao = row['Data Transmissão'].strftime('%d/%m/%Y às %H:%M:%S')
                    lista_veiculos_str += f"- **Placa:** {placa} | **Última Comunicação:** {data_transmissao}\n"

                assunto_email = "Importante: Verificação Necessária no seu Sistema de Rastreamento"
                
                corpo_email = f"""
Prezado(a) Cliente,

Esperamos que este e-mail o encontre bem.

Nosso sistema de monitoramento indicou uma interrupção na comunicação com o(s) dispositivo(s) rastreador(es) instalado(s) no(s) seguinte(s) veículo(s) sob sua responsabilidade:

{lista_veiculos_str}
Essa ausência de sinal impede o acompanhamento em tempo real, o que é uma função essencial para a segurança do seu patrimônio e para a eficácia do serviço contratado.

Por isso, pedimos sua especial atenção: se o(s) veículo(s) listado(s) acima está(ão) sendo utilizado(s) normalmente, é imprescindível que uma verificação técnica seja agendada. Nossa equipe precisa diagnosticar a causa da falha para restabelecer a comunicação do rastreador.

Para agendar o atendimento da forma mais conveniente para você ou sua operação, por favor, entre em contato através de um de nossos canais:

- **WhatsApp:** (69) 9 9322-9855
- **Capitais:** 4020-1724
- **Outras Localidades:** 0800 025 8871
- **Suporte:** contato@rovemabank.com.br

Agradecemos sua cooperação para garantir que seu sistema de rastreamento opere corretamente e que seu(s) veículo(s) permaneça(m) protegido(s).

Atenciosamente,
                """

                st.text_input("Assunto:", value=assunto_email, key="email_subject")
                st.text_area("Corpo do E-mail:", value=corpo_email, height=500, key="email_body")

            else:
                st.success("🎉 Excelente! Todos os terminais estão atualizados.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
        st.info("Por favor, verifique se o ficheiro tem o formato e as colunas esperadas.")

else:
    st.info("Aguardando o carregamento de um ficheiro para iniciar a análise.")
