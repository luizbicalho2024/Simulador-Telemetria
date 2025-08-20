# twilio_utils.py
import streamlit as st
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import re

def send_sms(to_number: str, message_body: str):
    """
    Envia uma mensagem SMS usando a API da Twilio.
    Retorna (sucesso, mensagem_de_status).
    """
    # Validação das credenciais
    account_sid = st.secrets.get("TWILIO_ACCOUNT_SID")
    auth_token = st.secrets.get("TWILIO_AUTH_TOKEN")
    twilio_phone_number = st.secrets.get("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, twilio_phone_number]):
        return False, "Credenciais da Twilio não configuradas nos Secrets."

    # Limpa e formata o número do destinatário para o padrão E.164
    to_number_cleaned = re.sub(r'[^0-9]', '', to_number)
    if not to_number_cleaned.startswith("55"):
         # Assume que é um número brasileiro sem o código do país e adiciona
        if len(to_number_cleaned) >= 10:
             to_number_formatted = f"+55{to_number_cleaned}"
        else:
            return False, f"Número de chip inválido: {to_number}"
    else:
        to_number_formatted = f"+{to_number_cleaned}"

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=twilio_phone_number,
            to=to_number_formatted
        )
        return True, f"SMS enviado com sucesso! SID: {message.sid}"
    except TwilioRestException as e:
        return False, f"Falha no envio do SMS: {e.msg}"
    except Exception as e:
        return False, f"Ocorreu um erro inesperado: {e}"
