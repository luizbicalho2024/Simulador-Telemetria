# 🛰️ Simulador de Telemetria

Bem-vindo ao Simulador de Telemetria, uma aplicação web completa desenvolvida com Python e Streamlit para otimizar o processo comercial de uma empresa de rastreamento e telemetria.

Esta ferramenta centraliza a geração de propostas comerciais, cotações para licitações e comandos técnicos para rastreadores, tudo isso protegido por um sistema de autenticação robusto com diferentes níveis de acesso.

![Simulador de Telemetria Screenshot](https://user-images.githubusercontent.com/your-username/your-repo/your-screenshot.png) ---

## ✨ Funcionalidades Principais

* **🔐 Autenticação Segura:** Sistema de login com múltiplos utilizadores, utilizando `streamlit-authenticator` e `passlib` para uma gestão segura de sessões, cookies e senhas encriptadas.

* **👤 Gestão de Papéis (Roles):**
    * **Administrador:** Acesso total ao painel de gestão de utilizadores (Criar, Ver, Editar, Apagar), localizado diretamente na página principal para maior conveniência.
    * **Utilizador:** Acesso de consulta aos simuladores para gerar propostas e cotações.

* **🛠️ Conjunto de Simuladores:**
    * **Simulador Pessoa Jurídica (PJ):** Gera propostas comerciais completas em formato `.docx` a partir de um template, com base nos produtos e planos selecionados.
    * **Simulador Pessoa Física (PF):** Calcula o valor de venda de produtos para o consumidor final, com opções de desconto e parcelamento com taxas realistas.
    * **Simulador para Licitações:** Cria cotações detalhadas para editais, calculando custos de hardware, serviços e margem de lucro. A tabela de detalhamento agora inclui totais por coluna e destaca a linha de valor total.
    * **Gerador de Comandos:** Fornece os comandos técnicos corretos para diferentes modelos de rastreadores.
    * **Organizador de Planilhas:** Ferramenta para fazer o upload de ficheiros de clientes (`.xlsx`) e reorganizar os dados de forma automática.

* **🎨 Identidade Visual Consistente:**
    * Logo e favicon presentes em todas as páginas da aplicação.
    * Imagem de perfil circular na barra lateral para uma experiência de utilizador mais elegante e profissional.

---

## 🚀 Tecnologias Utilizadas

* **Frontend & Backend:** Python, Streamlit
* **Base de Dados:** MongoDB (conectado via PyMongo)
* **Autenticação & Segurança:** streamlit-authenticator, passlib, bcrypt
* **Manipulação de Dados:** Pandas, NumPy
* **Geração de Documentos:** python-docx, docxtpl
* **Bibliotecas Principais:** pymongo, requests, Pillow

---

## ⚙️ Configuração e Instalação

Siga estes passos para executar o projeto no seu ambiente local ou para fazer o deploy no Streamlit Cloud.

### 1. Pré-requisitos
* Python 3.9+
* Conta no MongoDB Atlas

### 2. Instalação

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
    O ficheiro `requirements.txt` contém todas as bibliotecas necessárias.
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuração dos Segredos (Secrets)

Para a aplicação funcionar, ela precisa das credenciais de acesso à base de dados.

* **Para Deploy no Streamlit Cloud:**
    1.  Vá às configurações (`Settings`) da sua aplicação.
    2.  Clique em `Secrets`.
    3.  Copie e cole o conteúdo abaixo, substituindo com as suas credenciais.

* **Para Desenvolvimento Local:**
    1.  Crie uma pasta chamada `.streamlit` na raiz do projeto.
    2.  Dentro dela, crie um ficheiro chamado `secrets.toml`.
    3.  Copie e cole o conteúdo abaixo no ficheiro.

    ```toml
    # Conteúdo para o ficheiro de segredos

    # Substitua pela sua connection string COMPLETA do MongoDB Atlas
    MONGO_CONNECTION_STRING = "mongodb+srv://<user>:<password>@<cluster-url>?retryWrites=true&w=majority"

    # Chaves para os cookies de autenticação
    AUTH_COOKIE_NAME = "simulador_auth_cookie_v2"
    AUTH_COOKIE_KEY = "uma_chave_muito_segura_e_aleatoria_que_voce_inventar_aqui"
    AUTH_COOKIE_EXPIRY_DAYS = 30
    ```
    **Importante:** No MongoDB Atlas, vá a "Network Access" e autorize o acesso de qualquer IP (`0.0.0.0/0`) para que o Streamlit Cloud possa conectar-se.

### 4. Executar a Aplicação

```bash
streamlit run Simulador_Comercial.py
