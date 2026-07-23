# Relatório de validação

## Verificações concluídas

- compilação de todos os arquivos Python com `compileall`;
- análise sintática individual dos 23 arquivos Python;
- quatro testes automatizados aprovados;
- validação de todos os destinos usados por `st.page_link` e `st.switch_page`;
- verificação de ausência da página de cadastro de veículos;
- verificação de ausência de Selenium, WebDriver, Chromium e `packages.txt`;
- verificação de ausência das credenciais reais fornecidas no código entregue;
- verificação de ausência de emojis e nomes de arquivos codificados com `#U00`;
- conferência dos endpoints atuais da BrasilAPI e FIPE;
- conferência das APIs utilizadas do Streamlit 1.56 e Streamlit-Authenticator 0.3.3.

## Limitação do ambiente de validação

O ambiente de execução usado para preparar esta entrega não disponibilizou o pacote Streamlit em seu índice interno e bloqueou acesso direto ao PyPI. Por isso, a inicialização visual em navegador não pôde ser executada aqui. O projeto foi fixado em `streamlit==1.56.0`, teve suas assinaturas de API verificadas na documentação oficial e passou pelas verificações estáticas e testes listados acima.
