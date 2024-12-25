from send_massage import send_message
from models import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import time
from datetime import datetime, timedelta
import re

# Налаштування вебдрайвера
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Використовувати в headless-режимі
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Автоматичне завантаження та налаштування ChromeDriver
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# Функція для обробки ціни
def parse_price(price_str):
    clean_str = price_str.replace("(", "").replace(")", "").replace("$", "").replace(",", "").replace("<", "")

    if "M" in clean_str:
        return float(clean_str.replace("M", "")) * 1_000_000
    elif "B" in clean_str:
        return float(clean_str.replace("B", "")) * 1_000_000_000
    else:
        return float(clean_str)

def press_load_more_button():
    load_more_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'History_loadMore__IilgR')]"))
    )
    load_more_button.click()
    print("Clicked 'Load More' button.")

def find_token_address(action):
    hover_element = action

    actions = ActionChains(driver)
    actions.move_to_element(hover_element).perform()

    token_address = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'TransactionAction_addr')]"))
    ).text

    return token_address


# Основна функція парсера транзакцій
def get_data_from_user(address):
    url = f"https://debank.com/profile/{address}/history"
    driver.get(url)

    try:
        #finding first transaction
        first_transaction = None
        while not first_transaction:
            try:
                # Спроба знайти першу транзакцію, яка не містить клас 'History_error'
                first_transaction = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'History_tableLine') and not(contains(@class, 'History_error'))]"))
                )
            except:
                # Якщо транзакція не знайдена, натискаємо кнопку 'Load More'
                try:
                    press_load_more_button()
                    print("Clicked 'Load More' button.")
                except Exception as e:
                    print("No more transactions to load or error occurred:", e)
                    break

        # Перевіряємо кожен елемент окремо
        try:
            time_of_tx = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'History_sinceTime')]").text
        except Exception:
            time_of_tx = "NOT FOUND"

        try:
            amount = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenPrice')]").text
        except Exception:
            amount = "NOT FOUND"

        try:
            token = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenName')]").text
        except Exception:
            token = "NOT FOUND"

        try:
            action = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'TransactionAction_action')]")
            action_text = action.text
        except Exception:
            action_text = "NOT FOUND"

        try:
            token_address = find_token_address(action)
        except Exception:
            token_address = "NOT FOUND"

        #check amount
        if amount == "NOT FOUND":
            parsed_amount = "NOT FOUND"
            message_send = False
        else:
            parsed_amount = parse_price(amount)

            if parsed_amount > 1000:
                message = f"\ud83d\udea8 High Transaction Alert \ud83d\udea8\n" \
                          f"USER: {address}\n" \
                          f"Time: {time_of_tx} \n" \
                          f"Action: {action_text} \n" \
                          f"Amount: {parsed_amount:.2f} $\n" \
                          f"Token: {token}\n" \
                          f"Token address: {token_address} \n"
                message_send = True
            else:
                message_send = False



        problem = any(field == "NOT FOUND" for field in [time_of_tx, amount, token, action_text, token_address])


        if not transaction_exists(address, time_of_tx, action_text, amount, token, token_address):
            if message_send==True:
                send_message(message)

            save_transaction(
                user_address=address,
                time=time_of_tx,
                action=action_text,
                amount=amount,
                token=token,
                token_address=token_address,
                message_send=message_send,
                problem=problem
            )

        print(
              f"Time: {time_of_tx} \n"
              f"Action: {action_text} \n"
              f"Amount: {parsed_amount:.2f} $\n"
              f"Token: {token}\n"
              f"Token address: {token_address}\n"
              "-------------"
              )
    except Exception as e:
        print(f"Error while parsing: {e}")


# Функція для збереження транзакції в базу даних
def save_transaction(user_address, time, action, amount, token, token_address, message_send, problem):
    try:
        new_transaction = Transactions(
            user_address=user_address,
            time=time,
            action=action,
            amount=amount,
            token=token,
            token_address=token_address,
            message_send=message_send,
            problem=problem
        )
        session.add(new_transaction)
        session.commit()
        print("Transaction saved to database.")
    except Exception as e:
        print(f"Error while saving transaction: {e}")



# Функція для парсингу часу
def parse_time(time_str):
    now = datetime.now()

    # Якщо формат - XXmins XXsecs ago або Xhr Xmin ago
    if "ago" in time_str:
        time_match = re.match(r"(?:(\d+)hr[s]?)? ?(?:(\d+)min[s]?)? ?(?:(\d+)sec[s]?)? ago", time_str)
        if time_match:
            hours = int(time_match.group(1)) if time_match.group(1) else 0
            minutes = int(time_match.group(2)) if time_match.group(2) else 0
            seconds = int(time_match.group(3)) if time_match.group(3) else 0
            return now - timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # Якщо формат - YYYY/MM/DD HH:MM:SS
    try:
        return datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        pass

    # Якщо формат не розпізнано
    raise ValueError(f"Unrecognized time format: {time_str}")

# Функція для перевірки існування транзакції
def transaction_exists(user_address, time_of_tx, action, amount, token, token_address):
    try:
        # Конвертуємо час у datetime
        converted_time = parse_time(time_of_tx)

        # Шукаємо транзакцію з подібними критеріями
        existing_transaction = session.query(Transactions).filter_by(
            user_address=user_address,
            action=action,
            amount=amount,
            token=token,
            token_address=token_address
        ).filter(
            Transactions.time.between(
                (converted_time - timedelta(seconds=5)).strftime("%Y/%m/%d %H:%M:%S"),
                (converted_time + timedelta(seconds=5)).strftime("%Y/%m/%d %H:%M:%S")
            )
        ).first()

        return existing_transaction is not None
    except Exception as e:
        print(f"Error while checking transaction existence: {e}")
        return False


# Функція для зчитування адрес із бази даних
def get_addresses():
    try:
        addresses = session.query(Address).all()
        return [address.address for address in addresses]
    except Exception as e:
        print(f"An error occurred while accessing the database: {e}")
        return []

if __name__ == "__main__":
    while True:
        addresses = get_addresses()

        for address in addresses:
            current_time = datetime.now().strftime("%m-%d %H:%M")
            print(f"/ {current_time} / USER: {address}")
            get_data_from_user(address)
            time.sleep(1)  # Невелика затримка між запитами

    driver.quit()
