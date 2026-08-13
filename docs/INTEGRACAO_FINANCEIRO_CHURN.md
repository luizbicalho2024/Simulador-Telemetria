# Integração Financeiro → Simulador Comercial

O Simulador mantém o MongoDB atual para propostas, usuários e configurações e usa um segundo datasource, o Firestore do Financeiro, exclusivamente para a página **Churn e base ativa**.

## Secret obrigatório no Streamlit Cloud do Simulador

Adicione uma seção separada nos Secrets do aplicativo do Simulador:

```toml
[financeiro_service_account]
type = "service_account"
project_id = "SEU_PROJECT_ID_FIREBASE_FINANCEIRO"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "simulador-financeiro-reader@SEU_PROJECT_ID.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

Não versionar chave privada no GitHub.

## Permissão recomendada

Crie uma conta de serviço exclusiva para o Simulador e conceda apenas permissão de leitura no projeto do Firebase/Firestore. No Google Cloud IAM, prefira um papel de leitura compatível com Firestore/Datastore, em vez de reutilizar uma conta administrativa do Financeiro.

## Coleções consumidas

- `billing_monthly_metrics`: receita, base ativa, ativações, desativações e suspensões por cliente/mês.
- `billing_terminal_snapshots`: snapshot vigente de cada terminal em cada mês.
- `billing_month_closures`: indica quais meses foram processados/fechados integralmente.
- `billing_history`: fallback para histórico anterior à implantação da camada analítica.

## Regra de churn

Um cliente só é classificado como **Churn total** quando possuía base ativa no mês anterior, fica com base zero/ausente no mês selecionado e esse mês possui fechamento em `billing_month_closures`. Isso evita falso churn durante um faturamento ainda parcial.
