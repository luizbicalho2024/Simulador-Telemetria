# pages/Ajuda.py
import streamlit as st

st.set_page_config(layout="wide", page_title="Ajuda e Documentação", page_icon="❓")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado!"); st.stop()

st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")

st.title("❓ Ajuda e Documentação da Plataforma")
st.markdown("Bem-vindo ao guia de utilizador do Simulador de Telemetria.")

with st.expander("📄 Como usar a página de Gestão de Estoque?", expanded=True):
    st.markdown("""
    Esta ferramenta foi desenhada para comparar o seu estoque registado no sistema com o seu inventário físico. Siga estes passos para uma análise correta:

    **1. Preparar o Ficheiro do Sistema:**
    - Exporte o relatório `relatorio_rastreador.xls` do seu sistema.
    - Abra este ficheiro no Microsoft Excel ou similar.
    - Vá a **Ficheiro -> Guardar Como...**.
    - No tipo de ficheiro, escolha **Pasta de Trabalho do Excel (*.xlsx)**. É crucial usar este formato para evitar erros.
    - Garanta que a linha com os cabeçalhos (`Modelo`, `Nº Série`, `Status`, etc.) está na **linha 12** do ficheiro.

    **2. Preparar o Ficheiro do Estoque Físico:**
    - Crie uma planilha simples com uma única coluna.
    - O cabeçalho da coluna deve ser **Serial**.
    - Liste todos os números de série dos rastreadores que você contou fisicamente.

    **3. Fazer o Upload:**
    - Na página "Gestão de Estoque", carregue o ficheiro `.xlsx` do sistema no campo da esquerda.
    - Carregue a sua planilha do estoque físico no campo da direita.

    **4. Analisar os Resultados:**
    - A aplicação irá mostrar automaticamente os gráficos, contagens, listas e divergências encontradas.
    """)

with st.expander("⚙️ O que cada Simulador faz?"):
    st.markdown("""
    - **Simulador PJ:** Gera propostas comerciais completas em formato `.docx` para clientes Pessoa Jurídica.
    - **Simulador PF:** Calcula o valor de venda de produtos para o consumidor final.
    - **Simulador Licitação:** Cria cotações detalhadas para editais e concorrências.
    """)

with st.expander("👑 Funcionalidades de Administrador"):
    st.markdown("""
    Os utilizadores com o papel de 'Admin' têm acesso a funcionalidades exclusivas na página principal:
    - **Gestão de Utilizadores:** Criar, editar, ver e apagar contas de utilizadores.
    - **Reset de Senhas:** Definir uma nova senha para qualquer utilizador.
    - **Gestão de Preços:** Alterar os preços e taxas usados em todos os simuladores da plataforma.
    """)
