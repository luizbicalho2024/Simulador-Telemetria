# Changelog

## 2.4.0 — Dashboard executivo de churn com amCharts

- Página Churn e Base Ativa reorganizada para leitura executiva, com filtros mais claros e resumo automático do mês.
- Gráficos Plotly substituídos por amCharts 5.20.3 com tooltips, animações, cursores e identidade visual da plataforma.
- Novo diagnóstico de impacto de receita por movimento e composição de churn, contração, expansão, novos clientes e reativações.
- Evolução histórica passa a combinar faturamento e base ativa, além de ativações, desativações, suspensões e saldo líquido.
- Ranking visual dos clientes que mais explicam a alta ou queda de receita, com controle de Top N.
- Filtro de clientes passa a afetar também KPIs e séries históricas, eliminando divergência entre filtros e indicadores.
- Tabela completa fica em expander e drill-down por cliente continua disponível com snapshots por período.
- Fallback técnico dos gráficos preserva KPIs e tabelas caso o CDN do amCharts não carregue.

## 2.3.1 — Correção de renderização do amCharts

- Corrigida quebra de linha escapada no tooltip que gerava `SyntaxError` dentro do iframe do Streamlit.
- CDN do amCharts fixado na versão 5.20.3 para evitar mudanças inesperadas da versão `latest`.
- Gráfico passa a exibir fallback técnico quando a biblioteca externa não carregar ou ocorrer erro de renderização.
- Teste de contrato visual passa a impedir regressão do escape JavaScript inválido.

## 2.3.0 — Interface compacta PJ e amCharts

- Produtos e serviços reorganizados em linhas compactas, reduzindo rolagem e excesso de métricas visuais.
- Preço padrão, preço aplicado, margem e instalação ficam visíveis em uma única linha por produto.
- Condições personalizadas passam a ser editadas em popover sob demanda, sem expandir toda a página.
- Ponto de equilíbrio passa a exibir gráfico interativo amCharts 5 comparando instalação cobrada e isenta.
- Linha de referência visual indica o piso de governança comercial diretamente no gráfico.
- Tabelas detalhadas dos cenários permanecem disponíveis em expansores para análise complementar.

## 2.2.0 — Governança comercial do Simulador PJ

- Simulação PJ passa a aceitar preços e margens abaixo do piso comercial para análise de cenários.
- Piso de 30% deixa de bloquear a simulação e passa a funcionar como gatilho de aprovação do Head Comercial.
- Propostas abaixo do piso ficam registradas com os valores econômicos visíveis, mas com download bloqueado até aprovação.
- Margem consolidada considera mensalidade, custo recorrente, instalação e custo fixo de implantação antes de decidir a alçada.
- Descontos e isenção de instalação só exigem aprovação quando derrubam a margem consolidada abaixo do piso.
- Snapshot da proposta registra piso de margem, status da política, motivo de aprovação e referência comercial usada.
- Inclusão dos atalhos comerciais VERDIO Start, Fleet, Safety e Sat como presets de composição, mantendo liberdade para ajustes manuais.
- Faixas de posicionamento comercial exibidas como referência, sem substituir a análise de custo e margem real.
- Cálculo por margem personalizada passa a aceitar cenários abaixo do piso, inclusive margens negativas, preservando validação matemática abaixo de 100%.
- Testes de regras PJ atualizados para validar simulação abaixo do piso e classificação de conformidade.

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
