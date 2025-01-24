from send_massage import send_message
from models import *
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

import time
import random
import string
from datetime import datetime, timedelta
import re

from fake_useragent import UserAgent
from stem import Signal
from stem.control import Controller

import asyncio

# Проксі для Tor
TOR_SOCKS_PROXY = '127.0.0.1:9150'
TOR_CONTROL_PORT = 9151
TOR_PASSWORD = ''


def set_up_driver():
    """Налаштування Selenium WebDriver для роботи через локальний Tor"""
    print("# start set up driver (set_up_driver())")
    options = Options()

    # Налаштування проксі для SOCKS5
    options.add_argument(f'--proxy-server=socks5://{TOR_SOCKS_PROXY}')

    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')

    # Випадковий User-Agent
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    print("# install chromedriver (set_up_driver())")
    service = Service(ChromeDriverManager().install())
    print("# add options to driver (set_up_driver())")
    driver = webdriver.Chrome(service=service, options=options)
    print("# driver created (set_up_driver())")
    return driver

async def renew_connection():
    #Функція для оновлення IP-адреси через Tor
    print("# start connection to TOR (renew_connection())")
    with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
        print("New Tor connection initiated.")
        await asyncio.sleep(5)


async def generate_random_cookie_js():
    print("# start generate random cooky (generate_random_cookie_js())")
    """Генерує рядок JavaScript для встановлення рандомного cookie"""
    name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    value = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    domain = ".debank.com"  # Замініть на відповідний домен
    path = "/"

    # Формуємо JavaScript
    js_script = f"""
        document.cookie = "name={name}; value={value}; path={path}; domain={domain}";
    """
    return js_script


async def set_cookies(driver):
    """Встановлює рандомні cookie через JavaScript перед кожним запитом"""
    print("! long time # start set cookie (set_cookies())")

    # Очікування завантаження сторінки
    WebDriverWait(driver, 35).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Встановлення cookie через JavaScript
    try:
        print("# called generate_random_cookie (set_cookies())")
        js_script = await generate_random_cookie_js()
        print("# add cooky to driver (set_cookies())")
        driver.execute_script(js_script)
        print(f"Рандомний cookie встановлено")
    except Exception as js_error:
        curent_time = datetime.now() + timedelta(hours=1)
        print(curent_time)
        print(f"Не вдалося встановити cookie")



# Функція для обробки ціни
async def parse_price(price_str):
    print('# start parse price (parse_price())')
    clean_str = price_str.replace("(", "").replace(")", "").replace("$", "").replace(",", "").replace("<", "")

    if "M" in clean_str:
        return float(clean_str.replace("M", "")) * 1_000_000
    elif "B" in clean_str:
        return float(clean_str.replace("B", "")) * 1_000_000_000
    else:
        return float(clean_str)


async def press_load_more_button(driver):
    print('# start press load more (press_load_more_button())')
    load_more_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'History_loadMore')]"))
    )
    load_more_button.click()
    print('# load more clicked (press_load_more_button())')

async def find_token_address(action, driver):
    print('# start find token address (find_token_address())')
    hover_element = action

    actions = ActionChains(driver)
    actions.move_to_element(hover_element).perform()

    token_address = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'TransactionAction_addr')]"))
    ).text
    print('# token address was find (find_token_address())')
    return token_address

# Основна функція парсера транзакцій
async def get_data_from_user(driver, address):
    print("# start get data from user (get_data_from_user())")

    print("# call renew connection with TOR (get_data_from_user())")
    await renew_connection()  # Оновлюємо IP перед кожним запитом

    print("! long time # get the url (get_data_from_user())")
    url = f"https://debank.com/profile/{address}/history"
    try:
        driver.set_page_load_timeout(40)
        driver.get(url)
    except Exception as e:
        print("Set link toke so ling time: ", e)
        return

    print("# call set cookie (get_data_from_user())")
    try:
        await set_cookies(driver)
    except Exception as e:
        print("Set cookies toke so ling time: ", e)
        return

    await asyncio.sleep(1)
    try:
        #finding first transaction
        first_transaction = None
        load_more_count = 0
        print("# try to get first transaction (get_data_from_user())")
        while not first_transaction and load_more_count <= 3:
            try:
                # Спроба знайти першу транзакцію, яка не містить клас 'History_error'
                first_transaction = WebDriverWait(driver, 35).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'History_tableLine') and not(contains(@class, 'History_error'))]"))
                )
            except:
                # Якщо транзакція не знайдена, натискаємо кнопку 'Load More'
                try:
                    load_more_count += 1
                    await press_load_more_button(driver)
                    print('load more clicked', load_more_count)
                except Exception as e:
                    curent_time = datetime.now() + timedelta(hours=1)
                    print(curent_time)
                    print("No more transactions to load or error occurred:", e)
                    break

        # Перевіряємо кожен елемент окремо
        print("# start finding transaction details (get_data_from_user())")
        print("# find time (get_data_from_user())")
        try:
            time_of_tx = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'History_sinceTime')]").text
            time_of_tx_correct = await parse_time(time_of_tx)
        except Exception:
            time_of_tx = "NOT FOUND"
            time_of_tx_correct = "NOT FOUND"
        print("# find amount (get_data_from_user())")
        try:
            amount = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenPrice')]").text
        except Exception:
            amount = "NOT FOUND"
        print("# find token name (get_data_from_user())")
        try:
            token = first_transaction.find_element(By.XPATH, ".//span[contains(@class, 'ChangeTokenList_tokenName')]").text
        except Exception:
            token = "NOT FOUND"
        print("# find action (get_data_from_user())")
        try:
            action = first_transaction.find_element(By.XPATH, ".//div[contains(@class, 'TransactionAction_action')]")
            action_text = action.text
        except Exception:
            action_text = "NOT FOUND"
        print("# find token address (get_data_from_user())")
        try:
            token_address = await find_token_address(action, driver)
        except Exception:
            token_address = "NOT FOUND"
        print("# check amount (>300$) (get_data_from_user())")
        #check amount
        if amount == "NOT FOUND":
            parsed_amount = "NOT FOUND"
            message_send = False
        else:
            try:
                parsed_amount = await parse_price(amount)
                message_send = False
                if parsed_amount > 300:
                    # finding links
                    # if token_address != "NOT FOUND" and action == "execute":
                    #     try:
                    #         marketcap_link = await find_marketcap_link(driver, token_address)
                    #         uniswap_link = await find_uniswap_link(driver, token_address)
                    #     except Exception:
                    #         marketcap_link = "NOT FOUND"
                    #         uniswap_link = "NOT FOUND"
                    # else:
                    #     marketcap_link = "NOT FOUND"
                    #     uniswap_link = "NOT FOUND"

                    message = f"\ud83d\udea8 High Transaction Alert \ud83d\udea8\n" \
                            f"USER: {address}\n" \
                            f"Time: {time_of_tx_correct} \n" \
                            f"Action: {action_text} \n" \
                            f"Amount: {parsed_amount} $\n" \
                            f"Token: {token}\n" \
                            f"Token address: {token_address} \n\n"\
                            f"Links: \n" \
                            f"DeBank: https://debank.com/profile/{address}/history"
                    message_send = True
                else:
                    message_send = False
            except Exception as e:
                message_send = False
                print("Error with data to send (maybe amount=''): ", e)

        print("# check if some problem is (get_data_from_user())")
        problem = any(field == "NOT FOUND" for field in [time_of_tx, amount, token, action_text, token_address])

        if time_of_tx_correct != "NOT FOUND":
            print("# check if transaction exist (get_data_from_user())")
            if not await transaction_exists(address, time_of_tx_correct, action_text, amount, token, token_address):
                if message_send==True:
                    await send_message(message)

                await save_transaction(
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
                              f"Amount: {parsed_amount} $\n" \
                              f"Token: {token}\n" \
                              f"Token address: {token_address} \n" \
                              f"Links: \n" \
                              f"DeBank: https://debank.com/profile/{address}/history"
                    await send_message(error_message)
        else:
            curent_time = datetime.now() + timedelta(hours=1)
            print(curent_time)
            error_message = f"\u274C Problem Transaction Alert \u274C\n" \
                            f"USER: {address}\n" \
                            f"Can not get transaction"
            #await send_message(error_message)
            print(error_message)
        print("# print transaction info (get_data_from_user())")
        curent_time = datetime.now() + timedelta(hours=1)
        print(curent_time)
        print(
              f"USER: {address}\n"
              f"Time: {time_of_tx} \n"
              f"Time convert: {time_of_tx_correct} \n"
              f"Action: {action_text} \n"
              f"Amount: {parsed_amount} $\n"
              f"Token: {token}\n"
              f"Token address: {token_address}\n"
              "-------------"
              )
    except Exception as e:
        curent_time = datetime.now() + timedelta(hours=1)
        print(curent_time)
        print(f"Error while parsing: {e}")


# async def find_marketcap_link(driver, token_address):
#     print("Trying to find MarketCap link")
#
#     await renew_connection()  # Оновлюємо IP перед кожним запитом
#     url = "https://coinmarketcap.com/"
#     driver.get(url)
#     await asyncio.sleep(3)  # Невелика пауза для завантаження сторінки
#
#     res_link = "NOT FOUND"  # Значення за замовчуванням
#
#     try:
#         # Очікуємо появи поля пошуку та клікаємо на нього
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='Search_mobile-icon-wrapper']"))
#         ).click()
#
#         # Знаходимо поле введення та вводимо token_address
#         input_field = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='search-input desktop-input']"))
#         )
#         input_field.send_keys(token_address)
#         await asyncio.sleep(2)  # Невелика пауза для завантаження пропозицій
#         input_field.send_keys(Keys.RETURN)  # Натискаємо Enter
#
#         # Очікуємо деякий час для можливої переадресації
#         await asyncio.sleep(5)
#
#         # Отримуємо поточний URL після можливого перенаправлення
#         current_url = driver.current_url
#
#         # Якщо URL змінився з початкового, вважаємо, що ми знайшли сторінку
#         if current_url != url:
#             res_link = current_url
#         else:
#             res_link = "NOT FOUND"
#
#     except Exception as e:
#         print(f"MarketCap link not found. Error: {e}")
#         res_link = "NOT FOUND"
#
#     return res_link

# async def find_uniswap_link(driver,token_address):
#
#     print("Trying to find Uniswap link")
#
#     await renew_connection()  # Оновлюємо IP перед кожним запитом
#     url = "https://app.uniswap.org/"
#     driver.get(url)
#     await asyncio.sleep(3)
#
#     try:
#         # Знаходимо поле введення та вводимо token_address
#         input_field = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='css-11aywtz']"))
#         )
#         input_field.send_keys(token_address)
#         await asyncio.sleep(2)
#         WebDriverWait(driver, 2).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-testid*='searchbar-token-row']"))
#         ).click()
#
#
#         # Отримуємо поточний URL після можливого перенаправлення
#         current_url = driver.current_url
#
#         # Якщо URL змінився з початкового, вважаємо, що ми знайшли сторінку
#         if current_url != url:
#             res_link = current_url
#         else:
#             res_link = "NOT FOUND"
#     except Exception as e:
#         print(f"Uniswap link not found. Error: {e}")
#         res_link = "NOT FOUND"
#
#     return res_link


# Функція для збереження транзакції в базу даних
async def save_transaction(user_address, time, action, amount, token, token_address, message_send, problem):
    print('# start save transaction (save_transaction())')
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
        session.close()
    except Exception as e:
        curent_time = datetime.now() + timedelta(hours=1)
        print(curent_time)
        print(f"Error while saving transaction: {e}")
        session.close()



# Функція для парсингу часу
async def parse_time(time_str):
    print('# start parse time (parse_time())')
    now = datetime.now() + timedelta(hours=1)

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
        parsed_time = parsed_time + timedelta(hours=1)
        # Скорочуємо до хвилини
        return parsed_time.replace(second=0, microsecond=0)
    except ValueError:
        pass

    # Якщо формат не розпізнано
    raise ValueError(f"Unrecognized time format: {time_str}")


# Функція для перевірки існування транзакції
async def transaction_exists(user_address, time, action, amount, token, token_address):
    print('# start transaction exist (transaction_exists())')
    try:
        # Створюємо базовий запит
        query = session.query(Transactions).filter_by(
            user_address=user_address,
            action=action,
            token=token
        ).filter(
            Transactions.time.between(
                time - timedelta(minutes=1),
                time + timedelta(minutes=1)
            )
        )

        # Якщо token_address не порожній, додаємо його до фільтра
        if token_address != '':
            query = query.filter_by(token_address=token_address)

        # Виконуємо запит
        print('# start check transaction (transaction_exists())')
        existing_transaction = query.first()
        print(existing_transaction)
        return existing_transaction is not None
    except Exception as e:
        curent_time = datetime.now() + timedelta(hours=1)
        print(curent_time)
        print(f"Error while checking transaction existence: {e}")
        return False



# Функція для зчитування адрес із бази даних
def get_addresses():
    try:
        print('# start get addresses (get_addresses())')
        addresses = session.query(Address).all()
        return [address.address for address in addresses]
    except Exception as e:
        curent_time = datetime.now() + timedelta(hours=1)
        print(curent_time)
        print(f"An error occurred while accessing the database: {e}")
        return []



async def fetch_task(address):
    """Асинхронне завдання для безперервного парсингу однієї адреси."""
    print('# start fetch task func (fetch_task())')
    while True:
        print('# call set up driver (fetch_task())')
        driver = set_up_driver()
        try:
            print('# call get data from user (fetch_task())')
            await get_data_from_user(driver, address)
        except Exception as e:
            error_message = f"\u274C Problem Transaction Alert \u274C\n" \
                            f"An error with proxy."
            await send_message(error_message)
            curent_time = datetime.now() + timedelta(hours=1)
            print(curent_time)
            print(f"An error with proxy: {e}.")
        finally:
            print('# driver quit (fetch_task())')
            driver.quit()

        # Невелика затримка перед повторним запуском
        await asyncio.sleep(random.uniform(2, 5))

async def send_alive_message(interval=7200):
    while True:
        try:
            await send_message(".")
            print("Sent 'I am alive' message to Telegram.")
        except Exception as e:
            curent_time = datetime.now() + timedelta(hours=1)
            print(curent_time)
            print(f"Error while sending 'I am alive' message: {e}")
        await asyncio.sleep(interval)  # Очікуємо заданий інтервал перед наступним повідомленням


async def main():
    """Основна функція для запуску асинхронного парсингу."""
    print('# get addresses from database (main())')
    addresses = get_addresses()
    print('# fetch task (main())')
    tasks = [fetch_task(address) for address in addresses]
    print('# append alive message (main())')
    tasks.append(send_alive_message())
    # Запускаємо всі завдання та чекаємо їх завершення
    print('# start tasks (main())')
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    while True:
        try:
            print('# start run main (__name__ == "__main__")')
            asyncio.run(main())
        except Exception as e:
            curent_time = datetime.now() + timedelta(hours=1)
            print(curent_time)
            print(f"!!!!!Critical error: {e}. Restarting...")
            time.sleep(5)