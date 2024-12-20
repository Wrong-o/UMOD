import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
from psycopg2 import pool
from fastapi import HTTPException

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        """
        Samuel: Rör ej den här koden!
        Jag testar ny metod, är det trasigt så är det.

        Creates a pool with 10 connections that can be used for calls.
        """
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
        self.pool = pool.SimpleConnectionPool(
            minconn = 1,
            maxconn = 10, 
            **self.db_config 
        )

    def get_connection(self):
        """Takes a connection from the pool of connections initiated in the
        construction of the class. """
        return self.pool.getconn()
    def put_connection(self, conn):
        """Puts the connection back into the pool."""
        self.pool.putconn(conn)

    def fetch_manual(self, params: str):
        """
        Fetch data from the database and return as a single string.
        """
        query ="""SELECT manual FROM product_table 
        WHERE LOWER(REPLACE(product_name, ' ', '')) = %s;
        """
        conn = self.get_connection()
        
        try:

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
            return str(result)
        except Exception as e:
            raise ConnectionError(f"db_manager: manual not found: {e}")
        
        finally:
            self.put_connection(conn)

    
    def fetch_productlist(self):
        #Old: query = f"SELECT DISTINCT product FROM {table};"
        #sanitized:i
        query = """
        SELECT DISTINCT product_name FROM product_table;
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query,)
                result = cursor.fetchall()
        except psycopg2.DatabaseError:
            raise psycopg2.DatabaseError("The product list was not fetched. Check logs for more info.")
        finally:
            self.put_connection(conn)
        return result
        
    def check_product_in_productlist(self, product: str):
        products = self.fetch_productlist()
        if any(row['product_name'] == product for row in products):
            return 0        
        else:
            raise HTTPException(f"{product} not in list: {list}")
        

    def fetch_questions_by_language(self, product: str, language: str):
        query = """
        SELECT question FROM questionlog
        WHERE product = %s AND q_lang = %s;"
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (product, language))
                result = cursor.fetchall()
                return result
        except Exception as e:
            raise Exception(f"error when getting language: {e}")
        finally:
            self.put_connection(conn)
    
    def fetch_languageslist(self, table: str):
        #old: query = f"SELECT DISTINCT q_lang FROM {table}"
        #Sanitized:
        query = """
        SELECT DISTINCT q_lang
        FROM %s;
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (table,))
                result = cursor.fetchall()
                return result
        except Exception as e:
            raise Exception(f"error when getting language list: {e}")
        finally:
            self.put_connection(conn)

    def write_data(self, query, params=None):
        """Write data to the database."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
        except psycopg2.IntegrityError:
            raise psycopg2.IntegrityError("Product already exists")
        finally:
            self.put_connection(conn)

    def add_manual(self, product: str, manual: str):
        query = "INSERT INTO product_table (product_name, manual) VALUES (%s, %s)"
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (product, manual))
                self.connection.commit()
        except Exception:
            pass
        finally:
            self.put_connection(conn)
