# 🛰️ Simulador de Telemetria

Bem-vindo ao Simulador de Telemetria, uma aplicação web completa desenvolvida com Python e Streamlit para otimizar o processo comercial de uma empresa de rastreamento e telemetria.

Esta ferramenta permite a gestão de utilizadores com diferentes níveis de acesso e oferece um conjunto de simuladores para gerar propostas comerciais, cotações para licitações e comandos técnicos para rastreadores de forma rápida e padronizada.

---

## ✨ Funcionalidades Principais

* **🔐 Autenticação Segura:** Sistema de login com múltiplos utilizadores, utilizando `streamlit-authenticator` para uma gestão segura de sessões e cookies.
* **👤 Gestão de Papéis (Roles):**
    * **Administrador:** Acesso total ao painel de gestão de utilizadores (Criar, Ver, Editar, Apagar) e a todos os simuladores.
    * **Utilizador:** Acesso restrito aos simuladores para consulta e geração de propostas.
* **🛠️ Conjunto de Simuladores:**
    * **Simulador Pessoa Jurídica (PJ):** Gera propostas comerciais completas em formato `.docx` a partir de um template, com base nos produtos e planos selecionados.
    * **Simulador Pessoa Física (PF):** Calcula o valor de venda de produtos para o consumidor final, com opções de desconto e parcelamento.
    * **Simulador para Licitações:** Cria cotações detalhadas para editais, calculando custos de hardware, serviços e margem de lucro.
    * **Gerador de Comandos:** Fornece os comandos técnicos corretos para diferentes modelos de rastreadores Suntech.
* **📄 Processamento de Ficheiros:**
    * Ferramenta para fazer o upload de planilhas de clientes (`.xlsx`) e reorganizar os dados de forma automática.
    * Geração dinâmica de propostas em formato `.docx` a partir de um template pré-definido.

---

## 🚀 Tecnologias Utilizadas

* **Backend & Frontend:** Python, Streamlit
* **Base de Dados:** MongoDB
* **Manipulação de Dados:** Pandas
* **Autenticação:** streamlit-authenticator
* **Geração de Documentos:** docxtpl
* **Bibliotecas Principais:** pymongo, passlib, bcrypt

---

## ⚙️ Configuração e Instalação Local

Siga estes passos para executar o projeto no seu ambiente local.

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/luizbicalho2024/Simulador-Telemetria.git](https://github.com/luizbicalho2024/Simulador-Telemetria.git)
    cd Simulador-Telemetria
    ```

2.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure os Segredos (Secrets):**
    * Crie uma pasta `.streamlit` na raiz do projeto, se ela não existir.
    * Dentro dela, crie um ficheiro chamado `secrets.toml`.
    * Copie e cole o conteúdo abaixo no ficheiro e substitua com as suas credenciais.

    ```toml
    # .streamlit/secrets.toml

    # Substitua pela sua connection string COMPLETA do MongoDB Atlas
    MONGO_CONNECTION_STRING = "mongodb+srv://<user>:<password>@<cluster-url>?retryWrites=true&w=majority"

    # Chaves para os cookies de autenticação
    AUTH_COOKIE_NAME = "simulador_auth_cookie"
    AUTH_COOKIE_KEY = "uma_chave_muito_segura_e_aleatoria_que_voce_inventar"
    AUTH_COOKIE_EXPIRY_DAYS = 30
    ```

5.  **Execute a Aplicação:**
    ```bash
    streamlit run Simulador_Comercial.py
    ```

---

## 🐞 Resolvendo o Erro Final do DOCX

Como mencionado, o erro `Unexpected end of template` é um problema com o ficheiro Word, não com o código. A solução mais garantida é **criar um novo documento do zero**.

1.  **Crie um NOVO ficheiro Word em branco.** Não copie o antigo.
2.  Adicione o texto e as tabelas que você precisa.
3.  Na tabela de produtos, use a sintaxe que discutimos na mensagem anterior com **extremo cuidado**, digitando as tags em vez de copiar e colar, se possível:

| Item | Descrição | Preço | Mês |
| :--- | :--- | :--- |
| `{%tr for item in itens_proposta %}{{ item.nome }}` | `{{ item.desc }}` | `{{ item.preco }}{% endtr %}` |

4.  Salve este novo ficheiro como `Proposta Comercial e Intenção - Verdio.docx` na raiz do projeto e envie para o GitHub.

Esta abordagem de "começar do zero" elimina qualquer formatação XML corrompida que possa estar escondida no seu template antigo, resolvendo o problema de forma definitiva.
