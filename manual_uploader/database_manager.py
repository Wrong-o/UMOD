from sqlalchemy import create_engine, Column, String, Integer, Text, select, distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from dotenv import load_dotenv
import os
from sqlalchemy import inspect
from sqlalchemy.orm import Session

# Initialize the Base for SQLAlchemy models
Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        try:
            db_url = (
                f"postgresql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}"
                f"@{os.environ.get('DB_ENDPOINT')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
            )

            self.engine = create_engine(db_url, echo=False)
            self.Session = scoped_session(sessionmaker(bind=self.engine))

            # Test connection
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")

        except Exception as e:
            raise ConnectionError(f"Error connecting to database: {e}")

    def fetch_context(self, query, params=None):
        """Fetch data from the database and return as a single string."""
        with self.Session() as session:
            result = session.execute(query, params).fetchall()
            return str(result)

    def fetch_productlist(self, table: str):
        """Fetch distinct products from a given table."""
        with self.Session() as session:
            query = f"SELECT DISTINCT product FROM {table}"
            result = session.execute(query).fetchall()
            return [row[0] for row in result]

    def fetch_questions_by_language(self, product: str, language: str):
        """Fetch questions for a specific product and language."""
        with self.Session() as session:
            query = "SELECT question FROM questionlog WHERE product = :product AND q_lang = :language"
            result = session.execute(query, {"product": product, "language": language}).fetchall()
            return [row[0] for row in result]

    def fetch_languageslist(self, table: str):
        """Fetch distinct languages from a given table."""
        with self.Session() as session:
            query = f"SELECT DISTINCT q_lang FROM {table}"
            result = session.execute(query).fetchall()
            return [row[0] for row in result]

    def write_data(self, query, params=None):
        """Write data to the database."""
        with self.Session() as session:
            session.execute(query, params)
            session.commit()

    def add_manual(self, product: str, manual: str):
        """Insert a manual into the context table."""
        with self.Session() as session:
            query = "INSERT INTO context (product, context) VALUES (:product, :manual)"
            session.execute(query, {"product": product, "manual": manual})
            session.commit()

# Example SQLAlchemy Model
class Context(Base):
    __tablename__ = 'context'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product = Column(String, nullable=False)
    context = Column(Text, nullable=False)

# To initialize the database schema (if required)
def initialize_database():
    load_dotenv()
    db_url = (
        f"postgresql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_ENDPOINT')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
    )

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

# Dependency for FastAPI to get a database session
def get_db():
    load_dotenv()
    db_url = (
        f"postgresql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_ENDPOINT')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
    )

    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def list_all_tables(db: Session):
    """
    List all available tables in the connected database.
    
    Args:
        db (Session): SQLAlchemy Session instance.
    
    Returns:
        list: A list of table names.
    """
    inspector = inspect(db.bind)  # Get an inspector bound to the session's engine
    tables = inspector.get_table_names()
    return tables
