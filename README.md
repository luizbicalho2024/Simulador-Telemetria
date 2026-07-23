# Simulador de Telemetria

Plataforma interna em Streamlit para simulação comercial, propostas, licitações, consultas, conciliação de estoque e análises operacionais.

## Principais melhorias desta versão

- interface corporativa e responsiva, sem navegação baseada em emojis;
- identidade visual centralizada e configurável pelo administrador;
- upload de logomarca persistido no MongoDB;
- personalização de nome, subtítulo, rodapé e cores do sistema;
- menu lateral controlado por perfil e página de auditoria exclusiva para administradores;
- dashboard comercial com filtros e gráficos;
- correção do registro de propostas PF;
- correção da sincronização FIPE, agora consultando o detalhe de cada ano/versão;
- compatibilidade com os dois padrões de nomes dos Secrets da Twilio;
- índices, pool de conexão, timeouts e operações em lote no MongoDB;
- imagens otimizadas para reduzir o tempo de carregamento no Streamlit Cloud;
- remoção da página de cadastro automatizado de veículos e das dependências Chromium/Selenium;
- nomes de arquivos normalizados para evitar problemas de encoding no deploy.

## Estrutura

```text
Simulador_Comercial.py          # Login, visão geral e administração
app_core/
  auth.py                       # Autenticação e controle de acesso
  settings.py                   # Configuração padrão de identidade visual
  ui.py                         # Tema, menu, cabeçalho e componentes compartilhados
assets/templates/               # Template DOCX da proposta PJ
pages/                          # Simuladores e ferramentas
user_management_db.py          # Persistência, índices e serviços MongoDB
```

## Deploy no Streamlit Cloud

1. Crie ou atualize o aplicativo no Streamlit Community Cloud.
2. Defina `Simulador_Comercial.py` como arquivo principal e selecione Python 3.12.
3. Abra **Settings > Secrets**.
4. Copie o conteúdo de `.streamlit/secrets.toml.example` e substitua os valores.
5. Reinicie o aplicativo.

Exemplo:

```toml
MONGO_CONNECTION_STRING = "mongodb+srv://USUARIO:SENHA@CLUSTER.mongodb.net/?retryWrites=true&w=majority&appName=SimuladorTelemetria"
AUTH_COOKIE_NAME = "simulador_telemetria_auth"
AUTH_COOKIE_KEY = "SUBSTITUA_POR_UMA_CHAVE_ALEATORIA_COM_64_CARACTERES"
AUTH_COOKIE_EXPIRY_DAYS = 30

TWILIO_ACCOUNT_SID = "AC..."
TWILIO_AUTH_TOKEN = "..."
TWILIO_PHONE_NUMBER = "+55..."
```

A Twilio é opcional. Sem essas credenciais, a página de comandos continua gerando os comandos, mas não envia SMS.

## Execução local

Use preferencialmente Python 3.12, a mesma versão padrão atual do Streamlit Community Cloud.


```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
streamlit run Simulador_Comercial.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run Simulador_Comercial.py
```

## Primeiro acesso

Quando a coleção de usuários estiver vazia, a aplicação exibirá o formulário para criação do primeiro administrador. A senha deve possuir pelo menos oito caracteres.

## Identidade visual

Entre como administrador e abra a página inicial. Na seção **Administração > Identidade visual** é possível alterar:

- logomarca;
- nome do sistema;
- descrição curta;
- texto do rodapé;
- cor primária;
- cor secundária;
- cor de destaque;
- fundo, superfície, texto e texto secundário.

As alterações ficam armazenadas na coleção `system_settings` do MongoDB e são aplicadas a todas as páginas.

## Segurança

- Nunca envie `.streamlit/secrets.toml` ao GitHub.
- Use uma chave de cookie longa e exclusiva.
- Restrinja o usuário do MongoDB ao banco necessário.
- Revogue imediatamente credenciais que tenham sido publicadas em mensagens, commits ou capturas de tela.
