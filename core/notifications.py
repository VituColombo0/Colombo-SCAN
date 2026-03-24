"""
Colombo Scanner — Notification System
Sends scan completion notifications via webhooks (Discord, Slack, Telegram, generic).
"""
import os
import json
import urllib.request
from core.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
log = get_logger("notifications")


def _send_webhook(url: str, payload: dict) -> bool:
    """Sends a JSON payload to a webhook URL."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"Webhook enviado com sucesso: {resp.status}")
            return True
    except Exception as e:
        log.warning(f"Falha ao enviar webhook: {e}")
        return False


def notificar_scan_completo(alvo: str, total_plugins: int, total_entidades: int,
                            case_name: str = "", correlacoes: int = 0):
    """
    Sends a notification about scan completion.
    Supports Discord, Slack, Telegram, and generic webhooks via env vars.
    """
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not webhook_url and not (telegram_token and telegram_chat):
        return  # No notification configured

    mensagem = (
        f"🔍 **Colombo Scanner — Scan Completo**\n"
        f"📎 Alvo: `{alvo}`\n"
        f"📂 Case: {case_name or 'Sessão Rápida'}\n"
        f"🔌 Plugins executados: {total_plugins}\n"
        f"🧠 Entidades encontradas: {total_entidades}\n"
        f"🔥 Correlações: {correlacoes}\n"
    )

    if webhook_url:
        # Auto-detect webhook type
        if "discord.com/api/webhooks" in webhook_url:
            payload = {"content": mensagem}
        elif "hooks.slack.com" in webhook_url:
            payload = {"text": mensagem.replace("**", "*")}
        else:
            payload = {"text": mensagem, "message": mensagem}

        _send_webhook(webhook_url, payload)

    if telegram_token and telegram_chat:
        try:
            msg_clean = mensagem.replace("**", "*").replace("`", "")
            tg_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {"chat_id": telegram_chat, "text": msg_clean, "parse_mode": "Markdown"}
            _send_webhook(tg_url, payload)
        except Exception as e:
            log.warning(f"Falha Telegram: {e}")
