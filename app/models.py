import bcrypt
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = "product_table"

    product_id = Column(Integer, primary_key=True)
    product_name = Column(String(255))
    manual = Column(String)
    category = Column(String(255))


class Role(Base):
    __tablename__ = "role_table"

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String, unique=True)


class User(Base):
    __tablename__ = "user_table"

    user_id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Integer, ForeignKey("role_table.role_id"), default=1)

    role_relation = relationship("Role")

    def set_password(self, password: str):
        """Hash the password before storing"""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Check if the password matches stored hash"""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )
    
class QuestionLog(Base):
    __tablename__ = 'questionlog'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product = Column(String, nullable=False)
    question = Column(String, nullable=False)
    response = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    q_lang = Column(String, nullable=False)
    r_lang = Column(String, nullable=False)
    response_id = Column(String, nullable=False)


