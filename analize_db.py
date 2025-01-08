from models import *

# Пошук всіх транзакцій для конкретної адреси

problem = "1"
transactions = session.query(Transactions).filter(Transactions.problem == problem).all()

count = 0
for transaction in transactions:
    count += 1
    print(f"ID: {transaction.id}, Time: {transaction.time}, Action: {transaction.action}, "
          f"Amount: {transaction.amount}, Token: {transaction.token}, Token Address: {transaction.token_address}, "
          f"Message Sent: {transaction.message_send}, Problem: {transaction.problem}")

print(count)