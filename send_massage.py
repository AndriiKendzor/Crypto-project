import requests
from models import *

def send_message(text: str) -> None:
    token = "7943976877:AAFTnXwKbrxgJdi3mhv5xe2N5zK52CKgZ7o"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Формування URL для запиту

    active_users = check_if_allowed()

    for user in active_users:
        payload = {
            "chat_id": user.telegram_id,
            "text": text
        }
        # Надсилання запиту
        response = requests.post(url, json=payload)

        # Перевірка відповіді
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print("Failed to send message:", response.json())


def check_if_allowed():

    active_users = session.query(AllowedParticipants).filter_by(active=True).all()
    return active_users


