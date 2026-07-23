from __future__ import annotations

import streamlit as st

from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Ajuda e Documentação")
apply_branding()
require_auth()
render_sidebar()
render_hero("Ajuda e documentação", "Orientações rápidas para os principais fluxos da plataforma.")

with st.expander("Simuladores comerciais", expanded=True):
    st.markdown(
        """
        **Pessoa Jurídica:** selecione o prazo, a quantidade de veículos e os produtos. O sistema calcula os valores mensais e o total contratual, registra a proposta e gera o documento em DOCX.

        **Pessoa Física:** selecione o produto, informe desconto e parcelamento. O valor final é registrado no dashboard.

        **Licitações:** informe escopo, margem, custos e serviços. O sistema calcula mensalidade por veículo e valor global estimado.
        """
    )

with st.expander("Planilhas e análises"):
    st.markdown(
        """
        **Dados de clientes:** o cabeçalho do relatório deve estar na linha 12. A ferramenta agrupa clientes PF/PJ e organiza os e-mails vinculados.

        **Gestão de estoque:** carregue o relatório do sistema em XLSX e a contagem física em XLSX ou CSV. A conciliação mostra itens não cadastrados e equipamentos faltantes.

        **Análise de terminais:** carregue o relatório de terminais e defina o limite de dias sem transmissão. A ferramenta gera a lista crítica e um modelo de comunicação.

        **Análise de jornada:** carregue o relatório de jornada em XLSX ou CSV para verificar direção contínua e interjornada.
        """
    )

with st.expander("Administração"):
    st.markdown(
        """
        Na página inicial, administradores podem:

        - cadastrar, editar, desativar e excluir usuários;
        - redefinir senhas;
        - atualizar preços e produtos;
        - alterar nome, logomarca e cores do sistema;
        - consultar o diagnóstico de MongoDB e Twilio;
        - acessar a auditoria de atividades.
        """
    )

with st.expander("Configuração do Streamlit Cloud"):
    st.code(
        '''MONGO_CONNECTION_STRING = "mongodb+srv://USUARIO:SENHA@cluster.mongodb.net/?retryWrites=true&w=majority"
AUTH_COOKIE_NAME = "simulador_telemetria_auth"
AUTH_COOKIE_KEY = "SUBSTITUA_POR_UMA_CHAVE_ALEATORIA_COM_64_CARACTERES"
AUTH_COOKIE_EXPIRY_DAYS = 30

TWILIO_ACCOUNT_SID = "AC..."
TWILIO_AUTH_TOKEN = "..."
TWILIO_PHONE_NUMBER = "+55..."''',
        language="toml",
    )
    st.caption("A Twilio é opcional. Sem essas três chaves, os comandos continuam sendo gerados, mas o envio por SMS fica indisponível.")
