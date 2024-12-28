from send_massage import send_message
from models import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
import time
import random
import string
from datetime import datetime, timedelta
import re


# Аутентифікація для Scraping Browser
AUTH = 'brd-customer-hl_f402bbf9-zone-crypto_project:sqdckur1s8nj'
SBR_WEBDRIVER = f'https://{AUTH}@brd.superproxy.io:9515'
sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')

def generate_random_cookie():
    """Генерує випадкові cookie для маскування активності"""
    return {
        "name": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        "value": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
        "domain": ".debank.com",
        "path": "/"
    }


def set_cookies(driver, url):
    """Встановлює нові cookie перед кожним запитом"""
    driver.get(url)

    # Очікування повного завантаження сторінки
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Генерація та встановлення cookie
    cookie = {
        "name": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        "value": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
        "domain": "debank.com",
        "path": "/"
    }
    try:
        driver.add_cookie(cookie)
        print(f"Cookie встановлено: {cookie}")
    except Exception as e:
        print(f"Не вдалося встановити cookie: {e}")



# Функція для обробки ціни
def parse_price(price_str):
    clean_str = price_str.replace("(", "").replace(")", "").replace("$", "").replace(",", "").replace("<", "")

    if "M" in clean_str:
        return float(clean_str.replace("M", "")) * 1_000_000
    elif "B" in clean_str:
        return float(clean_str.replace("B", "")) * 1_000_000_000
    else:
        return float(clean_str)

def press_load_more_button(driver):
    load_more_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'History_loadMore__IilgR')]"))
    )
    load_more_button.click()
    print("Clicked 'Load More' button.")

def find_token_address(action, driver):
    hover_element = action

    actions = ActionChains(driver)
    actions.move_to_element(hover_element).perform()

    token_address = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'TransactionAction_addr')]"))
    ).text

    return token_address

# Основна функція парсера транзакцій
def get_data_from_user(address):
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        url = f"https://debank.com/profile/{address}/history"
        driver.get(url)
        set_cookies(driver, url)

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
                        press_load_more_button(driver)
                        print("Clicked 'Load More' button.")
                    except Exception as e:
                        print("No more transactions to load or error occurred:", e)
                        break

            # Перевіряємо кожен елемент окремо
            try:
                time_of_tx = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'History_sinceTime')]").text
                time_of_tx_correct = parse_time(time_of_tx)
            except Exception:
                time_of_tx = "NOT FOUND"
                time_of_tx_correct = "NOT FOUND"

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
                token_address = find_token_address(action, driver)
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
                              f"Time: {time_of_tx_correct} \n" \
                              f"Action: {action_text} \n" \
                              f"Amount: {parsed_amount:.2f} $\n" \
                              f"Token: {token}\n" \
                              f"Token address: {token_address} \n"
                    message_send = True
                else:
                    message_send = False



            problem = any(field == "NOT FOUND" for field in [time_of_tx, amount, token, action_text, token_address])

            if not transaction_exists(address, time_of_tx_correct, action_text, amount, token, token_address):
                if message_send==True:
                    send_message(message)

                save_transaction(
                    user_address=address,
                    time=time_of_tx_correct,
                    action=action_text,
                    amount=amount,
                    token=token,
                    token_address=token_address,
                    message_send=message_send,
                    problem=problem
                )

                if problem == True:
                    error_message = f"\u274C Problem Transaction Alert \u274C\n" \
                              f"USER: {address}\n" \
                              f"Time: {time_of_tx_correct} \n" \
                              f"Action: {action_text} \n" \
                              f"Amount: {parsed_amount:.2f} $\n" \
                              f"Token: {token}\n" \
                              f"Token address: {token_address} \n"
                    send_message(error_message)


            print(
                  f"Time: {time_of_tx} \n"
                  f"Time convert: {time_of_tx_correct} \n"
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

            # Ігноруємо секунди і скорочуємо до хвилини
            adjusted_time = now - timedelta(hours=hours, minutes=minutes)
            return adjusted_time.replace(second=0, microsecond=0)

    # Якщо формат - YYYY/MM/DD HH:MM:SS
    try:
        parsed_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
        # Скорочуємо до хвилини
        return parsed_time.replace(second=0, microsecond=0)
    except ValueError:
        pass

    # Якщо формат не розпізнано
    raise ValueError(f"Unrecognized time format: {time_str}")


# Функція для перевірки існування транзакції
def transaction_exists(user_address, time, action, amount, token, token_address):
    try:
        # Шукаємо транзакцію з подібними критеріями
        existing_transaction = session.query(Transactions).filter_by(
            user_address=user_address,
            action=action,
            amount=amount,
            token=token,
            token_address=token_address
        ).filter(
            Transactions.time.between(
                time - timedelta(minutes=1),
                time + timedelta(minutes=1)
            )
        ).first()
        print(existing_transaction)
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
