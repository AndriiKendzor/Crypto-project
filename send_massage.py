import requests

def send_message(text: str) -> None:
    token = "7943976877:AAFTnXwKbrxgJdi3mhv5xe2N5zK52CKgZ7o"
    chat_id = "1306841120"
    # Формування URL для запиту
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Дані для запиту
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    # Надсилання запиту
    response = requests.post(url, json=payload)

    # Перевірка відповіді
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print("Failed to send message:", response.json())

