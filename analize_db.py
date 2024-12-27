from models import *

# Пошук всіх транзакцій для конкретної адреси

address_to_check = "0x27cc4d6bc95b55a3a981bf1f1c7261cda7bb0931"
transactions = session.query(Transactions).filter(Transactions.user_address == address_to_check).all()
count = session.query(func.count(Transactions.id)).filter(Transactions.user_address == address_to_check).scalar()

# Виведення результатів
count = 0
for transaction in transactions:
    count += 1
    print(f"Count: {count}, ID: {transaction.id}, Time: {transaction.time}, Action: {transaction.action}, "
          f"Amount: {transaction.amount}, Token: {transaction.token}, Token Address: {transaction.token_address}, "
          f"Message Sent: {transaction.message_send}, Problem: {transaction.problem}")

print(f"Кількість повторень адреси {address_to_check}: {count}")