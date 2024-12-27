from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

# Налаштування бази даних
Base = declarative_base()
engine = create_engine("sqlite:///database.db")
Session = sessionmaker(bind=engine)
session = Session()


# Модель бази даних
class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    description = Column(String, nullable=True)

class Transactions(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_address = Column(String, nullable=False)
    time = Column(DateTime, nullable=True)
    action = Column(String, nullable=True)
    amount = Column(String, nullable=True)
    token = Column(String, nullable=True)
    token_address = Column(String, nullable=True)
    message_send = Column(Boolean, default=False)
    problem = Column(Boolean, default=False)

class AllowedParticipants(Base):
    __tablename__ = "allowed_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    active = Column(Boolean, default=False)

Base.metadata.create_all(engine)
