from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

import user_management_db as db
from app_core.auth import LOGIN_FIELDS, build_authenticator, clear_auth_state
from app_core.settings import branding_contrast_errors, get_default_branding, normalize_branding
from app_core.ui import apply_branding, configure_page, money, render_hero, render_logo, render_sidebar

configure_page("Simulador de Telemetria")
branding = apply_branding()


def render_connection_error() -> None:
    render_logo(max_width=260)
    render_hero("Não foi possível iniciar a plataforma", "A conexão com o banco de dados não foi estabelecida.")
    st.error("Verifique o Secret MONGO_CONNECTION_STRING e a liberação de rede no MongoDB Atlas.")
    st.code(
        'MONGO_CONNECTION_STRING = "mongodb+srv://USUARIO:SENHA@cluster.mongodb.net/?retryWrites=true&w=majority"',
        language="toml",
    )
    st.stop()


if db.get_mongo_client() is None:
    render_connection_error()

db.initialize_database()
try:
    authenticator, credentials = build_authenticator()
except RuntimeError as exc:
    render_logo(max_width=260)
    render_hero("Configuração de segurança incompleta", "Revise os Secrets da aplicação no Streamlit Cloud.")
    st.error(str(exc))
    st.code('AUTH_COOKIE_KEY = "USE_UMA_CHAVE_ALEATORIA_COM_PELO_MENOS_32_CARACTERES"', language="toml")
    st.stop()


if not credentials.get("usernames"):
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        render_logo(max_width=260)
        st.markdown("## Configuração inicial")
        st.caption("Crie a primeira conta administrativa da plataforma.")
        with st.form("first_admin_form", clear_on_submit=False):
            name = st.text_input("Nome completo")
            username = st.text_input("Usuário de acesso")
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password", help="Use pelo menos 8 caracteres.")
            confirmation = st.text_input("Confirmar senha", type="password")
            submitted = st.form_submit_button("Criar administrador", type="primary", width="stretch")

        if submitted:
            if not all([name.strip(), username.strip(), email.strip(), password, confirmation]):
                st.warning("Preencha todos os campos.")
            elif password != confirmation:
                st.warning("A confirmação de senha não corresponde.")
            elif len(password) < 8:
                st.warning("A senha deve possuir pelo menos 8 caracteres.")
            elif db.add_user(username, name, email, password, "admin"):
                db.add_log(username.strip().lower(), "Criou o primeiro administrador")
                st.success("Administrador criado. A página será recarregada.")
                st.rerun()
            else:
                st.error("Não foi possível criar o administrador. Verifique os dados informados.")
    st.stop()


if st.session_state.get("authentication_status") is True:
    authenticator.login(location="unrendered", key="main_cookie_login", max_login_attempts=5)
else:
    login_left, login_center, login_right = st.columns([1, 1.15, 1])
    with login_center:
        render_logo(max_width=260)
        st.markdown("## Acesso à plataforma")
        st.caption(branding.get("system_subtitle", ""))
        authenticator.login(location="main", fields=LOGIN_FIELDS, key="main_login", max_login_attempts=5)

if "logged_in_log" not in st.session_state:
    st.session_state.logged_in_log = False

if st.session_state.get("authentication_status"):
    username = str(st.session_state.get("username") or "").strip().lower()
    current_role = db.get_user_role(username)
    if current_role is None:
        clear_auth_state()
        st.error("A conta está inativa ou não existe mais.")
        st.stop()
    st.session_state["username"] = username
    st.session_state["role"] = current_role
    if not st.session_state.logged_in_log:
        db.add_log(username, "Login realizado")
        st.session_state.logged_in_log = True
elif st.session_state.get("authentication_status") is False:
    st.session_state.logged_in_log = False
    st.error("Usuário ou senha inválidos.")
    st.stop()
else:
    st.stop()


render_sidebar(include_logout=True)
render_hero(
    branding["system_name"],
    f"Bem-vindo, {st.session_state.get('name', 'usuário')}. Acesse os simuladores e ferramentas pelo menu lateral.",
)

summary = db.get_dashboard_summary()
last_proposal = summary.get("last_proposal")
last_proposal_label = last_proposal.strftime("%d/%m/%Y %H:%M") if isinstance(last_proposal, datetime) else "Sem registros"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Propostas registradas", summary["total_proposals"])
k2.metric("Valor total simulado", money(summary["total_value"]))
k3.metric("Usuários ativos", summary["active_users"])
k4.metric("Última proposta", last_proposal_label)

st.markdown("### Acessos rápidos")
quick_1, quick_2, quick_3, quick_4 = st.columns(4)
with quick_1:
    st.markdown('<div class="app-card"><div class="app-card-title">Pessoa jurídica</div><div class="app-card-value">Proposta PJ</div><p class="app-muted">Planos, produtos e geração de documento comercial.</p></div>', unsafe_allow_html=True)
    st.page_link("pages/1_Simulador_PJ.py", label="Abrir simulador PJ", width="stretch")
with quick_2:
    st.markdown('<div class="app-card"><div class="app-card-title">Pessoa física</div><div class="app-card-value">Proposta PF</div><p class="app-muted">Descontos, parcelamento e valor final da venda.</p></div>', unsafe_allow_html=True)
    st.page_link("pages/2_Simulador_PF.py", label="Abrir simulador PF", width="stretch")
with quick_3:
    st.markdown('<div class="app-card"><div class="app-card-title">Editais</div><div class="app-card-value">Licitações</div><p class="app-muted">Custos, amortização, serviços e margem comercial.</p></div>', unsafe_allow_html=True)
    st.page_link("pages/3_Simulador_Licitacao.py", label="Abrir simulador", width="stretch")
with quick_4:
    st.markdown('<div class="app-card"><div class="app-card-title">Gestão</div><div class="app-card-value">Dashboard</div><p class="app-muted">Indicadores e histórico consolidado de propostas.</p></div>', unsafe_allow_html=True)
    st.page_link("pages/4_Dashboard.py", label="Abrir dashboard", width="stretch")

recent = db.get_recent_proposals(limit=8)
if recent:
    st.markdown("### Atividade comercial recente")
    recent_df = pd.DataFrame(recent)
    if "_id" in recent_df.columns:
        recent_df.drop(columns=["_id"], inplace=True)
    display_columns = [column for column in ["data_geracao", "tipo", "empresa", "consultor", "valor_total"] if column in recent_df.columns]
    st.dataframe(
        recent_df[display_columns],
        width="stretch",
        hide_index=True,
        column_config={
            "data_geracao": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
            "tipo": "Tipo",
            "empresa": "Cliente ou órgão",
            "consultor": "Consultor",
            "valor_total": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        },
    )


if st.session_state.get("role") == "admin":
    st.markdown("---")
    st.markdown("## Administração")
    tab_users, tab_prices, tab_branding, tab_account, tab_status = st.tabs(
        ["Usuários", "Preços e produtos", "Identidade visual", "Conta e senha", "Ambiente"]
    )

    with tab_users:
        users = db.get_all_users_for_admin_display()
        overview_col, create_col = st.columns([1.4, 1])

        with overview_col:
            st.markdown("#### Usuários cadastrados")
            search = st.text_input("Pesquisar usuário", placeholder="Nome, login ou e-mail")
            filtered = users
            if search.strip():
                term = search.strip().lower()
                filtered = [
                    user
                    for user in users
                    if term in str(user.get("name", "")).lower()
                    or term in str(user.get("username", "")).lower()
                    or term in str(user.get("email", "")).lower()
                ]
            if filtered:
                st.dataframe(
                    pd.DataFrame(filtered),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "username": "Usuário",
                        "name": "Nome",
                        "email": "E-mail",
                        "role": "Perfil",
                        "active": "Ativo",
                        "created_at": st.column_config.DatetimeColumn("Criado em", format="DD/MM/YYYY HH:mm"),
                        "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="DD/MM/YYYY HH:mm"),
                    },
                )
            else:
                st.info("Nenhum usuário encontrado.")

        with create_col:
            st.markdown("#### Novo usuário")
            with st.form("create_user", clear_on_submit=True):
                new_name = st.text_input("Nome completo")
                new_username = st.text_input("Usuário")
                new_email = st.text_input("E-mail")
                new_password = st.text_input("Senha inicial", type="password")
                new_role = st.selectbox("Perfil", ["user", "admin"], format_func=lambda value: "Usuário" if value == "user" else "Administrador")
                create_user = st.form_submit_button("Cadastrar usuário", type="primary", width="stretch")
            if create_user:
                if len(new_password) < 8:
                    st.warning("A senha inicial deve possuir pelo menos 8 caracteres.")
                elif db.add_user(new_username, new_name, new_email, new_password, new_role):
                    db.add_log(username, "Criou usuário", {"usuario": new_username, "perfil": new_role})
                    st.success("Usuário cadastrado.")
                    st.rerun()
                else:
                    st.error("Não foi possível cadastrar. O usuário pode já existir ou os dados estão incompletos.")

        if users:
            st.markdown("#### Editar usuário")
            users_map = {user["username"]: user for user in users}
            selected_username = st.selectbox("Selecione o usuário", list(users_map), key="admin_user_select")
            selected = users_map[selected_username]
            edit_col, password_col, delete_col = st.columns([1.3, 1, 0.8])

            with edit_col:
                with st.form("edit_user"):
                    edited_name = st.text_input("Nome", value=selected.get("name", ""))
                    edited_email = st.text_input("E-mail", value=selected.get("email", ""))
                    edited_role = st.selectbox(
                        "Perfil",
                        ["user", "admin"],
                        index=0 if selected.get("role") == "user" else 1,
                        format_func=lambda value: "Usuário" if value == "user" else "Administrador",
                    )
                    edited_active = st.toggle("Acesso ativo", value=selected.get("active", True))
                    save_user = st.form_submit_button("Salvar alterações", width="stretch")
                if save_user and db.update_user_details(selected_username, edited_name, edited_email, edited_role, edited_active):
                    db.add_log(username, "Editou usuário", {"usuario": selected_username, "perfil": edited_role, "ativo": edited_active})
                    st.success("Usuário atualizado.")
                    st.rerun()

            with password_col:
                with st.form("reset_user_password"):
                    reset_password = st.text_input("Nova senha", type="password")
                    reset_confirmation = st.text_input("Confirmar nova senha", type="password")
                    reset_submit = st.form_submit_button("Redefinir senha", width="stretch")
                if reset_submit:
                    if len(reset_password) < 8:
                        st.warning("Use pelo menos 8 caracteres.")
                    elif reset_password != reset_confirmation:
                        st.warning("As senhas não correspondem.")
                    elif db.reset_user_password_by_admin(selected_username, reset_password):
                        db.add_log(username, "Redefiniu senha", {"usuario": selected_username})
                        st.success("Senha redefinida.")
                    else:
                        st.error("Não foi possível redefinir a senha.")

            with delete_col:
                st.caption("Exclusão permanente")
                confirmation = st.text_input("Digite o usuário", key="delete_user_confirmation")
                if st.button("Excluir usuário", type="primary", width="stretch", disabled=confirmation != selected_username):
                    if selected_username == username:
                        st.error("Você não pode excluir a própria conta durante a sessão.")
                    elif db.delete_user(selected_username):
                        db.add_log(username, "Excluiu usuário", {"usuario": selected_username})
                        st.success("Usuário excluído.")
                        st.rerun()
                    else:
                        st.error("A exclusão foi bloqueada. Verifique se este é o único administrador.")

    with tab_prices:
        pricing = db.get_pricing_config()
        st.caption(
            "As alterações são aplicadas imediatamente aos simuladores. "
            "Os custos PJ são internos e nunca aparecem na proposta enviada ao cliente."
        )

        missing_costs = [
            f"{plan} / {product}"
            for plan, products in pricing.get("PLANOS_PJ", {}).items()
            for product in products
            if float(pricing.get("CUSTOS_PJ", {}).get(plan, {}).get(product, 0) or 0) <= 0
        ]
        if missing_costs:
            st.warning(
                f"Existem {len(missing_costs)} combinações de produto e prazo sem custo mensal cadastrado. "
                "A margem do Simulador PJ ficará pendente para esses itens."
            )

        add_pf, add_pj, add_bid = st.columns(3)
        with add_pf:
            with st.form("add_pf_product", clear_on_submit=True):
                st.markdown("#### Novo produto PF")
                pf_name = st.text_input("Nome do produto")
                pf_price = st.number_input("Preço de venda", min_value=0.0, step=10.0, format="%.2f")
                pf_submit = st.form_submit_button("Adicionar produto", width="stretch")
            if pf_submit and pf_name.strip():
                pricing.setdefault("PRECOS_PF", {})[pf_name.strip()] = pf_price
                if db.update_pricing_config(pricing):
                    db.add_log(username, "Adicionou produto PF", {"produto": pf_name, "preco": pf_price})
                    st.success("Produto PF adicionado.")
                    st.rerun()

        with add_pj:
            with st.form("add_pj_product", clear_on_submit=True):
                st.markdown("#### Novo produto PJ")
                pj_name = st.text_input("Nome do produto")
                pj_description = st.text_input("Descrição comercial")
                pj_price = st.number_input(
                    "Preço mensal inicial",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f",
                )
                pj_cost = st.number_input(
                    "Custo mensal inicial",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f",
                    help="Custo unitário mensal por veículo usado no cálculo de margem.",
                )
                pj_submit = st.form_submit_button("Adicionar produto", width="stretch")
            if pj_submit and pj_name.strip():
                product_name = pj_name.strip()
                plans_config = pricing.setdefault("PLANOS_PJ", {})
                costs_config = pricing.setdefault("CUSTOS_PJ", {})
                for plan_name, plan_products in plans_config.items():
                    plan_products[product_name] = pj_price
                    costs_config.setdefault(plan_name, {})[product_name] = pj_cost
                pricing.setdefault("PRODUTOS_PJ_DESCRICAO", {})[product_name] = (
                    pj_description.strip() or product_name
                )
                if db.update_pricing_config(pricing):
                    db.add_log(
                        username,
                        "Adicionou produto PJ",
                        {"produto": product_name, "preco": pj_price, "custo": pj_cost},
                    )
                    st.success("Produto PJ adicionado.")
                    st.rerun()

        with add_bid:
            with st.form("add_bid_product", clear_on_submit=True):
                st.markdown("#### Novo item de licitação")
                bid_name = st.text_input("Nome do item")
                bid_cost = st.number_input("Custo do item", min_value=0.0, step=10.0, format="%.2f")
                bid_submit = st.form_submit_button("Adicionar item", width="stretch")
            if bid_submit and bid_name.strip():
                pricing.setdefault("PRECO_CUSTO_LICITACAO", {})[bid_name.strip()] = bid_cost
                if db.update_pricing_config(pricing):
                    db.add_log(username, "Adicionou item de licitação", {"produto": bid_name, "custo": bid_cost})
                    st.success("Item adicionado.")
                    st.rerun()

        with st.form("edit_pricing"):
            st.markdown("#### Valores atuais")
            pf_prices = dict(pricing.get("PRECOS_PF", {}))
            with st.expander("Pessoa física", expanded=True):
                pf_columns = st.columns(3)
                for index, item in enumerate(list(pf_prices)):
                    pf_prices[item] = pf_columns[index % 3].number_input(
                        item,
                        value=float(pf_prices[item]),
                        min_value=0.0,
                        format="%.2f",
                        key=f"price_pf_{index}",
                    )

            bid_prices = dict(pricing.get("PRECO_CUSTO_LICITACAO", {}))
            with st.expander("Licitações", expanded=False):
                amortization = st.number_input(
                    "Prazo de amortização do hardware (meses)",
                    min_value=1,
                    value=int(pricing.get("AMORTIZACAO_HARDWARE_MESES", 12)),
                )
                bid_columns = st.columns(3)
                for index, item in enumerate(list(bid_prices)):
                    bid_prices[item] = bid_columns[index % 3].number_input(
                        item,
                        value=float(bid_prices[item]),
                        min_value=0.0,
                        format="%.2f",
                        key=f"price_bid_{index}",
                    )

            pj_plans = {
                plan: dict(products)
                for plan, products in pricing.get("PLANOS_PJ", {}).items()
            }
            pj_costs = {
                plan: dict(pricing.get("CUSTOS_PJ", {}).get(plan, {}))
                for plan in pj_plans
            }
            with st.expander("Pessoa jurídica — preços, custos e margens", expanded=True):
                st.caption(
                    "Preço e custo são mensais, unitários e específicos por prazo contratual. "
                    "A margem é calculada sobre o preço de venda."
                )
                for plan_index, (plan, products) in enumerate(pj_plans.items()):
                    st.markdown(f"##### {plan}")
                    header_name, header_sale, header_cost = st.columns([1.7, 1, 1])
                    header_name.markdown("**Produto**")
                    header_sale.markdown("**Preço mensal**")
                    header_cost.markdown("**Custo mensal**")
                    plan_costs = pj_costs.setdefault(plan, {})

                    for product_index, item in enumerate(list(products)):
                        name_col, sale_col, cost_col = st.columns([1.7, 1, 1])
                        name_col.markdown(f"**{item}**")
                        sale_value = sale_col.number_input(
                            f"Preço {item} {plan}",
                            value=float(products[item]),
                            min_value=0.0,
                            format="%.2f",
                            key=f"price_pj_{plan_index}_{product_index}",
                            label_visibility="collapsed",
                        )
                        cost_value = cost_col.number_input(
                            f"Custo {item} {plan}",
                            value=float(plan_costs.get(item, 0.0) or 0.0),
                            min_value=0.0,
                            format="%.2f",
                            key=f"cost_pj_{plan_index}_{product_index}",
                            label_visibility="collapsed",
                        )
                        products[item] = sale_value
                        plan_costs[item] = cost_value

                        if sale_value > 0 and cost_value > 0:
                            margin_value = sale_value - cost_value
                            margin_percent = (margin_value / sale_value) * 100
                            name_col.caption(
                                f"Margem padrão: {money(margin_value)} ({margin_percent:.2f}%)"
                            )
                        elif cost_value <= 0:
                            name_col.caption("Margem pendente: informe o custo mensal.")
                        else:
                            name_col.caption("Preço zerado: margem indisponível.")
                    st.markdown("---")

            save_prices = st.form_submit_button("Salvar preços e custos", type="primary", width="stretch")

        if save_prices:
            pricing["PRECOS_PF"] = pf_prices
            pricing["PRECO_CUSTO_LICITACAO"] = bid_prices
            pricing["PLANOS_PJ"] = pj_plans
            pricing["CUSTOS_PJ"] = pj_costs
            pricing["AMORTIZACAO_HARDWARE_MESES"] = amortization
            if db.update_pricing_config(pricing):
                db.add_log(username, "Atualizou preços, custos e margens")
                st.success("Preços e custos atualizados.")
                st.rerun()
            else:
                st.error("Não foi possível salvar os preços e custos.")

    with tab_branding:
        # A normalização nesta camada impede KeyError mesmo quando o MongoDB
        # ainda contém um documento criado por versões anteriores do sistema.
        current = normalize_branding(db.get_system_settings())
        flash = st.session_state.pop("branding_flash", None)
        if flash:
            level = flash.get("level", "success")
            message = flash.get("message", "Identidade visual atualizada.")
            getattr(st, level, st.success)(message)
            for detail in flash.get("details", []):
                st.caption(detail)

        st.markdown("#### Logomarcas")
        st.caption(
            "Cadastre imagens diferentes para cada contexto. As logos são exibidas "
            "com transparência, sem painel ou fundo artificial."
        )

        main_logo_col, sidebar_logo_col = st.columns(2)

        with main_logo_col:
            st.markdown("##### Logo principal e login")
            st.caption("Usada na tela de login, página inicial e áreas de conteúdo.")
            render_logo(max_width=320, branding=current)

            uploaded_main_logo = st.file_uploader(
                "Enviar logo principal",
                type=["png", "jpg", "jpeg", "webp"],
                key="main_logo_uploader",
                help="Recomendado: PNG ou WebP transparente, largura de até 1200 px.",
            )
            if uploaded_main_logo:
                try:
                    if uploaded_main_logo.size > 5_000_000:
                        raise ValueError("O arquivo original deve possuir no máximo 5 MB.")
                    image = Image.open(uploaded_main_logo)
                    if image.width * image.height > 20_000_000:
                        raise ValueError("A imagem possui resolução excessiva. Use no máximo 20 megapixels.")
                    image = ImageOps.exif_transpose(image).convert("RGBA")
                    image.thumbnail((1200, 500), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG", optimize=True)
                    optimized = buffer.getvalue()
                    if len(optimized) > 2_000_000:
                        st.error("A imagem otimizada ainda excede 2 MB.")
                    elif st.button(
                        "Aplicar logo principal",
                        type="primary",
                        width="stretch",
                        key="apply_main_logo",
                    ):
                        if db.update_system_logo(optimized, "image/png", uploaded_main_logo.name):
                            db.add_log(username, "Atualizou a logo principal")
                            st.session_state["branding_flash"] = {
                                "level": "success",
                                "message": "Logo principal e de login atualizada.",
                            }
                            st.rerun()
                        else:
                            st.error("Não foi possível salvar a logo principal.")
                except Exception as exc:
                    st.error(f"Arquivo de imagem inválido: {exc}")

            if current.get("logo_base64") and st.button(
                "Restaurar logo principal padrão",
                width="stretch",
                key="reset_main_logo",
            ):
                if db.reset_system_logo():
                    db.add_log(username, "Restaurou a logo principal padrão")
                    st.session_state["branding_flash"] = {
                        "level": "success",
                        "message": "Logo principal padrão restaurada.",
                    }
                    st.rerun()

        with sidebar_logo_col:
            st.markdown("##### Logo da sidebar")
            st.caption(
                "Usada somente na barra lateral. Envie uma versão clara quando a sidebar for escura."
            )
            render_logo(sidebar=True, max_width=260, branding=current)

            if not current.get("sidebar_logo_base64"):
                st.info("Nenhuma logo específica cadastrada; a sidebar está reutilizando a logo principal.")

            uploaded_sidebar_logo = st.file_uploader(
                "Enviar logo da sidebar",
                type=["png", "jpg", "jpeg", "webp"],
                key="sidebar_logo_uploader",
                help="Recomendado: PNG ou WebP transparente, adequado à cor da sidebar.",
            )
            if uploaded_sidebar_logo:
                try:
                    if uploaded_sidebar_logo.size > 5_000_000:
                        raise ValueError("O arquivo original deve possuir no máximo 5 MB.")
                    image = Image.open(uploaded_sidebar_logo)
                    if image.width * image.height > 20_000_000:
                        raise ValueError("A imagem possui resolução excessiva. Use no máximo 20 megapixels.")
                    image = ImageOps.exif_transpose(image).convert("RGBA")
                    image.thumbnail((1200, 500), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG", optimize=True)
                    optimized = buffer.getvalue()
                    if len(optimized) > 2_000_000:
                        st.error("A imagem otimizada ainda excede 2 MB.")
                    elif st.button(
                        "Aplicar logo da sidebar",
                        type="primary",
                        width="stretch",
                        key="apply_sidebar_logo",
                    ):
                        if db.update_sidebar_logo(optimized, "image/png", uploaded_sidebar_logo.name):
                            db.add_log(username, "Atualizou a logo da sidebar")
                            st.session_state["branding_flash"] = {
                                "level": "success",
                                "message": "Logo da sidebar atualizada.",
                            }
                            st.rerun()
                        else:
                            st.error("Não foi possível salvar a logo da sidebar.")
                except Exception as exc:
                    st.error(f"Arquivo de imagem inválido: {exc}")

            if current.get("sidebar_logo_base64") and st.button(
                "Remover logo específica da sidebar",
                width="stretch",
                key="reset_sidebar_logo",
            ):
                if db.reset_sidebar_logo():
                    db.add_log(username, "Removeu a logo específica da sidebar")
                    st.session_state["branding_flash"] = {
                        "level": "success",
                        "message": "A sidebar voltou a usar a logo principal.",
                    }
                    st.rerun()

        st.markdown("---")
        preview_col, config_col = st.columns([1, 1.45])

        with preview_col:
            st.markdown("#### Pré-visualização das cores")
            st.markdown(f"### {current['system_name']}")
            st.caption(current["system_subtitle"])
            st.markdown(
                f"""
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-top:1rem;">
                    <div title="Primária" style="height:64px;border-radius:10px;background:{current['primary_color']};border:1px solid rgba(15,23,42,.08);"></div>
                    <div title="Secundária" style="height:64px;border-radius:10px;background:{current['secondary_color']};border:1px solid rgba(15,23,42,.08);"></div>
                    <div title="Destaque" style="height:64px;border-radius:10px;background:{current['accent_color']};border:1px solid rgba(15,23,42,.08);"></div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-top:.6rem;">
                    <div title="Sidebar" style="height:48px;border-radius:10px;background:{current.get('sidebar_background_color', current['secondary_color'])};border:1px solid rgba(15,23,42,.08);"></div>
                    <div title="Hover da sidebar" style="height:48px;border-radius:10px;background:{current.get('sidebar_hover_color', current['primary_color'])};border:1px solid rgba(15,23,42,.08);"></div>
                    <div title="Item ativo da sidebar" style="height:48px;border-radius:10px;background:{current.get('sidebar_active_color', current['primary_color'])};border:1px solid rgba(15,23,42,.08);"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Linha superior: primária, secundária e destaque. Linha inferior: sidebar, hover e item ativo.")

        with config_col:
            with st.form("branding_form"):
                st.markdown("#### Textos e identidade")
                system_name = st.text_input("Nome do sistema", value=current["system_name"], max_chars=80)
                system_subtitle = st.text_input("Descrição curta", value=current["system_subtitle"], max_chars=160)
                footer_text = st.text_input("Texto do rodapé", value=current.get("footer_text", ""), max_chars=160)
                auto_contrast = st.toggle(
                    "Ajustar automaticamente a cor dos textos para manter a leitura",
                    value=bool(current.get("auto_contrast", True)),
                    help="Quando habilitado, o sistema troca apenas a cor do texto que ficaria ilegível. As cores de fundo escolhidas não são alteradas.",
                )

                with st.expander("Cores gerais", expanded=True):
                    color_1, color_2, color_3 = st.columns(3)
                    primary = color_1.color_picker("Cor primária", current["primary_color"])
                    secondary = color_2.color_picker("Cor secundária", current["secondary_color"])
                    accent = color_3.color_picker("Cor de destaque", current["accent_color"])

                    color_4, color_5, color_6 = st.columns(3)
                    background = color_4.color_picker("Fundo", current["background_color"])
                    surface = color_5.color_picker("Superfície", current["surface_color"])
                    text = color_6.color_picker("Texto", current["text_color"])
                    muted = st.color_picker("Texto secundário", current["muted_color"])

                with st.expander("Barra lateral", expanded=True):
                    sidebar_1, sidebar_2, sidebar_3 = st.columns(3)
                    sidebar_background = sidebar_1.color_picker(
                        "Fundo da sidebar",
                        current.get("sidebar_background_color", current["secondary_color"]),
                    )
                    sidebar_text = sidebar_2.color_picker(
                        "Texto da sidebar",
                        current.get("sidebar_text_color", "#F8FAFC"),
                    )
                    sidebar_muted = sidebar_3.color_picker(
                        "Texto secundário da sidebar",
                        current.get("sidebar_muted_color", "#CBD5E1"),
                    )

                    sidebar_4, sidebar_5, sidebar_6 = st.columns(3)
                    sidebar_hover = sidebar_4.color_picker(
                        "Hover da sidebar",
                        current.get("sidebar_hover_color", current["primary_color"]),
                    )
                    sidebar_active = sidebar_5.color_picker(
                        "Item ativo da sidebar",
                        current.get("sidebar_active_color", current["primary_color"]),
                    )
                    sidebar_active_text = sidebar_6.color_picker(
                        "Texto do item ativo",
                        current.get("sidebar_active_text_color", "#FFFFFF"),
                    )

                save_branding = st.form_submit_button(
                    "Salvar identidade visual",
                    type="primary",
                    width="stretch",
                )

            if save_branding:
                updated = normalize_branding(current)
                updated.update(
                    {
                        "system_name": system_name,
                        "system_subtitle": system_subtitle,
                        "footer_text": footer_text,
                        "primary_color": primary,
                        "secondary_color": secondary,
                        "accent_color": accent,
                        "background_color": background,
                        "surface_color": surface,
                        "text_color": text,
                        "muted_color": muted,
                        "sidebar_background_color": sidebar_background,
                        "sidebar_text_color": sidebar_text,
                        "sidebar_muted_color": sidebar_muted,
                        "sidebar_hover_color": sidebar_hover,
                        "sidebar_active_color": sidebar_active,
                        "sidebar_active_text_color": sidebar_active_text,
                        "auto_contrast": auto_contrast,
                    }
                )
                contrast_warnings = branding_contrast_errors(updated)
                if db.update_system_settings(updated):
                    db.add_log(username, "Atualizou a identidade visual")
                    message = "Identidade visual atualizada."
                    if contrast_warnings and auto_contrast:
                        message += " O contraste automático ajustou somente os textos necessários."
                    elif contrast_warnings:
                        message += " Algumas combinações possuem contraste reduzido."
                    st.session_state["branding_flash"] = {
                        "level": "success" if not contrast_warnings or auto_contrast else "warning",
                        "message": message,
                        "details": contrast_warnings,
                    }
                    st.rerun()
                else:
                    st.error("Não foi possível salvar a identidade visual.")

            if st.button("Restaurar todas as cores padrão", width="stretch"):
                defaults = get_default_branding()
                for field in (
                    "logo_base64",
                    "logo_mime",
                    "logo_filename",
                    "sidebar_logo_base64",
                    "sidebar_logo_mime",
                    "sidebar_logo_filename",
                ):
                    defaults[field] = current.get(field)
                if db.update_system_settings(defaults):
                    db.add_log(username, "Restaurou a identidade visual padrão")
                    st.session_state["branding_flash"] = {
                        "level": "success",
                        "message": "Cores e comportamento visual restaurados para o padrão.",
                    }
                    st.rerun()

    with tab_account:
        with st.form("own_password_form"):
            st.markdown("#### Alterar sua senha")
            current_password = st.text_input("Senha atual", type="password")
            new_password = st.text_input("Nova senha", type="password")
            new_confirmation = st.text_input("Confirmar nova senha", type="password")
            change_password = st.form_submit_button("Alterar senha", type="primary")
        if change_password:
            stored_hash = credentials["usernames"][username]["password"]
            if not db.verify_password(current_password, stored_hash):
                st.error("A senha atual está incorreta.")
            elif len(new_password) < 8:
                st.warning("A nova senha deve possuir pelo menos 8 caracteres.")
            elif new_password != new_confirmation:
                st.warning("As senhas não correspondem.")
            elif db.update_user_password(username, new_password):
                db.add_log(username, "Alterou a própria senha")
                st.success("Senha alterada.")
            else:
                st.error("Não foi possível alterar a senha.")

    with tab_status:
        st.markdown("#### Diagnóstico do ambiente")
        mongo_ok = db.get_mongo_client() is not None
        twilio_configured = bool(
            st.secrets.get("TWILIO_ACCOUNT_SID", st.secrets.get("account_sid"))
            and st.secrets.get("TWILIO_AUTH_TOKEN", st.secrets.get("auth_token"))
            and st.secrets.get("TWILIO_PHONE_NUMBER", st.secrets.get("phone_number"))
        )
        status_1, status_2, status_3 = st.columns(3)
        status_1.metric("MongoDB", "Conectado" if mongo_ok else "Indisponível")
        status_2.metric("Twilio", "Configurado" if twilio_configured else "Não configurado")
        status_3.metric("Perfil atual", "Administrador")
        st.caption("As credenciais permanecem exclusivamente nos Secrets do Streamlit Cloud e não são exibidas nesta tela.")

else:
    st.markdown("---")
    with st.expander("Minha conta"):
        with st.form("user_password_form"):
            current_password = st.text_input("Senha atual", type="password")
            new_password = st.text_input("Nova senha", type="password")
            new_confirmation = st.text_input("Confirmar nova senha", type="password")
            change_password = st.form_submit_button("Alterar senha")
        if change_password:
            stored_hash = credentials["usernames"][username]["password"]
            if not db.verify_password(current_password, stored_hash):
                st.error("A senha atual está incorreta.")
            elif len(new_password) < 8:
                st.warning("A nova senha deve possuir pelo menos 8 caracteres.")
            elif new_password != new_confirmation:
                st.warning("As senhas não correspondem.")
            elif db.update_user_password(username, new_password):
                db.add_log(username, "Alterou a própria senha")
                st.success("Senha alterada.")
