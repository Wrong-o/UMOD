import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.db_config = {
            'host': os.environ.get("DB_ENDPOINT"),
            'dbname': os.environ.get("DB_NAME"),
            'user': os.environ.get("DB_USERNAME"),
            'password': os.environ.get("DB_PASSWORD"),
            'port': os.environ.get("DB_PORT")
        }
        self.connection = None

    def connect(self):
        """Establish a database connection."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.connection = None

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def fetch_data(self, query, params=None):
        """Fetch data from the database and return as a single string."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        return str(result)

    def write_data(self, query, params=None):
        """Write data to the database."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            self.connection.commit()
