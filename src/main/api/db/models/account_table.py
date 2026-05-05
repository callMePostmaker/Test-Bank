from symtable import Class

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from src.main.api.db.base import Base


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    number = Column(String, nullable=False, unique=True)
    balance = Column(Float, nullable=False, default=0)

def __repr__(self):
    return f'<Account(id={self.id}, user_id={self.user_id}, number={self.number}, balance={self.balance})>'


