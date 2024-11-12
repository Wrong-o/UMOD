import psycopg2
from dotenv import load_dotenv
import os


load_dotenv()
db_endpoint = os.environ.get("DB_ENDPOINT")
db_user = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")



db_config = {
    'host': db_endpoint,
    'dbname': db_name,
    'user': db_user,
    'password': db_password,
    'port': db_port
}


def insert_product_context(product_name, file_path):
    conn = None
    cursor = None
    try:
        # Read context from the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            context = file.read()

        # Connect to the database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Insert data into the 'context' table
        insert_query = """
        INSERT INTO context (product, context)
        VALUES (%s, %s)
        """
        cursor.execute(insert_query, (product_name, context))
        conn.commit()

        print(f"Product '{product_name}' and context loaded successfully.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close connections if they were created
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


# Example usage
product_name = "yamahayzf1000"  # Replace with the desired product name
file_path = "yamahayzf1000.txt"  # Replace with the path to your .txt file
insert_product_context(product_name, file_path)