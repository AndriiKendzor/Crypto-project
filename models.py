from sqlalchemy import create_engine, Column, Integer, String
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

Base.metadata.create_all(engine)
