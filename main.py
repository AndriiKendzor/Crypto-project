#-- imports --
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import time
from multiprocessing import Queue

#-- parsing settings --
# Налаштування вебдрайвера
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Використовувати в headless-режимі (опційно)
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Запуск драйвера
# Автоматичне завантаження та налаштування ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)



#-- correct format for price --
def parse_price(price_str):
    # Видалення непотрібних символів
    clean_str = price_str.replace("(", "").replace(")", "").replace("$", "").replace(",", "").replace("<", "")

    # Перевірка на множники (M = мільйони, B = мільярди)
    if "M" in clean_str:
        return float(clean_str.replace("M", "")) * 1000000
    elif "B" in clean_str:
        return float(clean_str.replace("B", "")) * 1000000000
    else:
        return float(clean_str)


#-- get transactions data --
def get_data_from_user(address, queue):
    # URL сторінки DeBank
    url = f"https://debank.com/profile/{address}/history"  # Вставте реальну адресу
    # Перехід на сторінку
    driver.get(url)

    try:
        # Очікування появи хоча б одного елемента
        first_transaction = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'History_tableLine')]"))
        )
        # Отримання даних з першого знайденого елемента
        time_of_tx = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'History_sinceTime')]").text
        amount = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenPrice')]").text
        token = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenName')]").text

        # Обробка значення через parse_price
        parsed_amount = parse_price(amount)
        # Виведення обробленої ціни

        # Перевірка на поріг
        if parsed_amount > 1000:
            message = f"🚨 High Transaction Alert 🚨\nUSER: {address}\n Token: {token}\nAmount: {parsed_amount:.2f} $\n Time: {time_of_tx}"
            send_message_to_telegram(queue, message)

        print(f"Time: {time_of_tx}, Amount: {parsed_amount:.2f} $, Token: {token}")
        print("-------------")
    except Exception as e:
        print(f"Error while parsing: {e}")



#-- get addresses --
def get_addresses(file_path):
    try:
        # Відкрити файл і зчитати всі рядки
        with open(file_path, "r") as file:
            addresses = file.readlines()

        # Видалити зайві символи (пробіли, переходи на новий рядок)
        addresses = [address.strip() for address in addresses]
        return addresses

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# -- send message to Telegram --
def send_message_to_telegram(queue, message):
    queue.put(message)
    print("massage to tg")



#-- run --
def run_parser(queue):
    file_path = "address.txt"
    try:
        while True:
            addresses = get_addresses(file_path)
            for address in addresses:
                current_time = datetime.now()
                formatted_time = current_time.strftime("%m-%d %H:%M")
                print(f"/ {formatted_time} / USER: {address}")
                get_data_from_user(address, queue)
            print("---BREAK---")
            time.sleep(5 * 60)
    except KeyboardInterrupt:
        print("Програму зупинено вручну.")
    finally:
        driver.quit()
