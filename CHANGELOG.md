# Changelog

## 2.1.0 — Personalização visual e navegação

- Salvamento de cores liberado mesmo quando a combinação escolhida possui contraste reduzido.
- Contraste automático de textos sobre botões, sidebar, cards e cabeçalhos.
- Controles específicos para fundo, texto, hover e item ativo da barra lateral.
- Fundo automático, transparente ou personalizado para logomarcas claras e escuras.
- Configuração de espaçamento e arredondamento do painel da logomarca.
- Botão de encerramento da sessão movido para o topo da sidebar em todas as páginas.
- Estilos de botões, links, abas e componentes alinhados à cor primária configurada.
- Migração automática das configurações visuais salvas na versão 2.0.

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
