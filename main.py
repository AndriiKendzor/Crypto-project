from send_massage import send_message
from models import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import time

# Налаштування вебдрайвера
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Використовувати в headless-режимі
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Автоматичне завантаження та налаштування ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


# Функція для обробки ціни
def parse_price(price_str):
    clean_str = price_str.replace("(", "").replace(")", "").replace("$", "").replace(",", "").replace("<", "")

    if "M" in clean_str:
        return float(clean_str.replace("M", "")) * 1_000_000
    elif "B" in clean_str:
        return float(clean_str.replace("B", "")) * 1_000_000_000
    else:
        return float(clean_str)


# Основна функція парсера транзакцій
def get_data_from_user(address):
    url = f"https://debank.com/profile/{address}/history"
    driver.get(url)

    try:
        # Очікуємо появу першої транзакції
        first_transaction = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'History_tableLine')]"))
        )

        # Збираємо дані транзакції
        time_of_tx = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'History_sinceTime')]").text
        amount = first_transaction.find_element(By.XPATH,
                                                ".//span[contains(@class, 'ChangeTokenList_tokenPrice')]").text
        token = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenName')]").text

        parsed_amount = parse_price(amount)

        if parsed_amount > 300:
            message = f"\ud83d\udea8 High Transaction Alert \ud83d\udea8\nUSER: {address}\nToken: {token}\nAmount: {parsed_amount:.2f} $\nTime: {time_of_tx}"
            send_message(message)

        print(f"Time: {time_of_tx}, Amount: {parsed_amount:.2f} $, Token: {token}")
        print("-------------")
    except Exception as e:
        print(f"Error while parsing: {e}")


# Функція для зчитування адрес із бази даних
def get_addresses():
    try:
        addresses = session.query(Address).all()
        return [address.address for address in addresses]
    except Exception as e:
        print(f"An error occurred while accessing the database: {e}")
        return []

if __name__ == "__main__":
    addresses = get_addresses()

    for address in addresses:
        current_time = datetime.now().strftime("%m-%d %H:%M")
        print(f"/ {current_time} / USER: {address}")
        get_data_from_user(address)
        time.sleep(1)  # Невелика затримка між запитами

    driver.quit()
