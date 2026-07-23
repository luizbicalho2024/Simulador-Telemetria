# Histórico de alterações

## 2.0.0 — modernização corporativa

### Interface e experiência

- identidade visual corporativa compartilhada por todas as páginas;
- navegação lateral sem emojis ou ícones inconsistentes;
- dashboard inicial, atalhos e indicadores comerciais;
- formulários, tabelas, gráficos, mensagens e estados vazios padronizados;
- nomes de arquivos normalizados para evitar falhas de encoding no deploy.

### Administração

- personalização de logomarca, nome, subtítulo, rodapé e paleta de cores;
- validação automática de contraste para preservar legibilidade;
- gestão de usuários, ativação, perfis e redefinição de senha;
- gestão de preços e produtos PF, PJ e licitações;
- diagnóstico de MongoDB e Twilio;
- auditoria restrita a administradores.

### Funcionalidade e dados

- correção do registro de propostas PF;
- dashboard de propostas com filtros, consolidação e exclusão controlada;
- sincronização FIPE detalhada por ano e versão;
- conciliação de estoque e análises operacionais revisadas;
- compatibilidade com nomes antigos e novos dos Secrets da Twilio.

### Segurança e desempenho

- restauração segura de sessão em páginas internas;
- validação de conta ativa em cada acesso;
- limite de tentativas de login;
- chave de cookie obrigatória com pelo menos 32 caracteres;
- validação e otimização de logomarcas enviadas;
- pool, timeouts, índices e operações em lote no MongoDB;
- imagens reduzidas e dependências Chromium/Selenium removidas;
- remoção da página de cadastro automatizado de veículos.
