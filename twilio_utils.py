from __future__ import annotations

import re

import streamlit as st
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


def _secret(*names: str) -> str | None:
    for name in names:
        try:
            value = st.secrets.get(name)
        except Exception:
            value = None
        if value:
            return str(value)
    return None


def normalize_brazilian_phone(phone_number: str) -> str | None:
    digits = re.sub(r"\D", "", phone_number)
    if digits.startswith("55") and 12 <= len(digits) <= 13:
        return f"+{digits}"
    if 10 <= len(digits) <= 11:
        return f"+55{digits}"
    return None


def send_sms(to_number: str, message_body: str) -> tuple[bool, str]:
    account_sid = _secret("TWILIO_ACCOUNT_SID", "account_sid")
    auth_token = _secret("TWILIO_AUTH_TOKEN", "auth_token")
    source_number = _secret("TWILIO_PHONE_NUMBER", "phone_number")

    if not all([account_sid, auth_token, source_number]):
        return False, "As credenciais da Twilio não estão configuradas nos Secrets."

    destination = normalize_brazilian_phone(to_number)
    if not destination:
        return False, "Número de telefone inválido. Informe DDD e número."

    if not message_body.strip():
        return False, "O comando está vazio."

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=message_body, from_=source_number, to=destination)
        return True, f"SMS enviado. SID: {message.sid}"
    except TwilioRestException as exc:
        return False, f"A Twilio recusou o envio: {exc.msg}"
    except Exception as exc:
        return False, f"Falha inesperada no envio: {exc}"
