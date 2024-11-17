import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        try:
            self.db_config = {
                'host': os.environ.get("DB_ENDPOINT"),
                'dbname': os.environ.get("DB_NAME"),
                'user': os.environ.get("DB_USERNAME"),
                'password': os.environ.get("DB_PASSWORD"),
                'port': os.environ.get("DB_PORT")
            }
            self.connection = None
        except ValueError as e:  
            raise ValueError(f"Enviroment variables are missing! Contact manager for proper credentials. {e}") from e


    def connect(self):
        """Establish a database connection."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
        except Exception as e:
            self.connection = None
            raise ConnectionError(f"Error connecting to database: {e}")

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def fetch_context(self, query, params=None):
        """Fetch data from the database and return as a single string."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        return str(result)
    
    def fetch_productlist(self, table: str):
        query = f"SELECT DISTINCT product FROM {table};"
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result
    
    def fetch_questions_by_language(self, product: str, language: str):
        query = "SELECT question FROM questionlog WHERE product = %s AND q_lang = %s;"
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (product, language))
            result = cursor.fetchall()
        return result
    
    def fetch_languageslist(self, table: str):
        query = f"SELECT DISTINCT q_lang FROM {table}"
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result

    def write_data(self, query, params=None):
        """Write data to the database."""   
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            self.connection.commit()
    
    def add_manual(self, product: str, manual: str):
        query = "INSERT INTO context (product, context) VALUES (%s, %s)"
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (product, manual))
            self.connection.commit()



    
