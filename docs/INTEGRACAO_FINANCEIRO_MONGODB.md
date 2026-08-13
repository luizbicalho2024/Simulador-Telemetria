# Integração Financeiro -> Simulador via MongoDB

O Simulador continua usando `simulador_db` para os seus próprios dados e consulta o banco
`financeiro_verdio` para a página Churn e Base Ativa.

Por padrão, ambos usam `MONGO_CONNECTION_STRING`. Se no futuro o Financeiro for colocado em outro
cluster, o Simulador também aceita `FINANCEIRO_MONGO_CONNECTION_STRING`.

O nome do banco pode ser alterado pelo Secret `FINANCEIRO_MONGO_DB`.

A página comercial consulta diretamente:

- `billing_monthly_metrics`
- `billing_month_closures`
- `billing_terminal_snapshots`
- `billing_history` como fallback

Não existe sincronização, cópia intermediária ou dependência de Firebase.
