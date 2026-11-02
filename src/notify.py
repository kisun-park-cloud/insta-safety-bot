"""처리 결과 알림 (텔레그램, 선택)."""
import os
import requests


def notify(msg: str):
    print(msg)
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if tok and chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                          data={"chat_id": chat, "text": msg[:4000]}, timeout=15)
        except requests.RequestException:
            pass
